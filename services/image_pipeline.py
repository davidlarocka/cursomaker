"""Coordinación del pipeline visual existente, con rutas por curso."""
import hashlib
import json
from pathlib import Path

from models.blueprint import CursoBlueprint
from models.contexto_curso import ContextoCurso
from models.render_blueprint import (
    CursoRender, SeccionRender, ContenidoRender, BloqueRender,
    ImagenRender, ImagenSubseccionMapping,
)
from services.documents import (
    extraer_texto_pdf, extraer_imagenes_pdf, deduplicar_imagenes, clasificar_imagenes,
)
from services.image_analyzer import analizar_imagen
from services.image_mapper import resolver_destino_imagen
from services.image_section_mapper import asignar_imagen_subseccion
from services.content_structure import detectar_estructura_contenido
from services.image_qa_store import cargar_analisis_imagenes, guardar_analisis_imagenes
from services.subsection_mapping_store import cargar_checkpoint, guardar_checkpoint
from services.blueprint_store import guardar_blueprint, guardar_json


def analizar_imagenes_manual(contexto, documento):
    salida = contexto.output_dir / "image_analysis.json"
    fuente = hashlib.sha256(contexto.config.manual.read_bytes()).hexdigest()
    estado = cargar_analisis_imagenes(salida)
    if estado.get("fuente_sha256") != fuente:
        estado = {"fuente_sha256": fuente, "imagenes": {}}
    imagenes = extraer_imagenes_pdf(contexto.config.manual, contexto.assets_dir)
    clasificacion = clasificar_imagenes(deduplicar_imagenes(imagenes))
    candidatos = clasificacion["candidatos"]
    nombres = {imagen["archivo"] for imagen in candidatos}
    estado["imagenes"] = {k: v for k, v in estado["imagenes"].items() if k in nombres}
    textos = {p["numero"]: p["texto"] for p in documento["paginas"]}
    guardar_analisis_imagenes(salida, estado)
    for imagen in candidatos:
        nombre = imagen["archivo"]
        anterior = estado["imagenes"].get(nombre, {})
        if anterior.get("estado") == "analizada":
            anterior["ruta"] = imagen["ruta"]
            print(f"Reutilizando análisis: {nombre}")
            continue
        pagina = imagen["paginas"][0]
        datos = {**imagen, "pagina": pagina}
        try:
            resultado = analizar_imagen(imagen["ruta"], pagina, textos.get(pagina, ""))
            if resultado is None:
                raise RuntimeError("Análisis visual vacío")
            datos.update(resultado.model_dump())
            datos["estado"] = "analizada"
        except Exception as error:
            datos.update(estado="error", error=str(error))
        estado["imagenes"][nombre] = datos
        guardar_analisis_imagenes(salida, estado)
    guardar_analisis_imagenes(salida, estado)
    errores = [nombre for nombre, datos in estado["imagenes"].items() if datos["estado"] == "error"]
    if errores:
        raise RuntimeError(
            f"Falló el análisis de {len(errores)} imágenes. Revisar {salida}; "
            "volver a ejecutar --etapa imagenes para reintentar."
        )
    return estado


def mapear_imagenes(contexto, blueprint, analisis, documento):
    salida = contexto.output_dir / "image_mapping.json"
    firma = hashlib.sha256((blueprint.model_dump_json() + json.dumps(analisis, sort_keys=True)).encode()).hexdigest()
    mapa = json.loads(salida.read_text(encoding="utf-8")) if salida.exists() else {}
    if mapa.get("fuente_sha256") != firma:
        mapa = {"fuente_sha256": firma, "imagenes": {}}
    textos = {p["numero"]: p["texto"] for p in documento["paginas"]}
    for nombre, imagen in analisis["imagenes"].items():
        if imagen.get("recomendacion") != "incluir" or nombre in mapa["imagenes"]:
            continue
        paginas = set(imagen.get("paginas", [imagen["pagina"]]))
        destinos = []
        for ns, seccion in enumerate(blueprint.secciones, start=1):
            for nc, contenido in enumerate(seccion.contenidos, start=1):
                comunes = paginas.intersection(contenido.paginas_fuente)
                if comunes:
                    destinos.append({
                        "seccion_numero": ns, "seccion": seccion.titulo,
                        "contenido_numero": nc, "contenido": contenido.titulo,
                        "pagina": min(comunes),
                    })
        if not destinos:
            raise RuntimeError(f"La imagen {nombre} no tiene destino en el Content Blueprint.")
        if len(destinos) == 1:
            destino, metodo, justificacion = destinos[0], "deterministico", "Único contenido con páginas fuente coincidentes."
        else:
            resolucion = resolver_destino_imagen(
                imagen, "\n".join(textos.get(p, "") for p in sorted(paginas)), destinos,
            )
            if not 0 <= resolucion.indice_destino < len(destinos):
                raise RuntimeError(f"Destino inválido para {nombre}")
            destino, metodo, justificacion = destinos[resolucion.indice_destino], "semantico", resolucion.justificacion
        mapa["imagenes"][nombre] = {
            **imagen, **destino, "metodo_asignacion": metodo, "justificacion": justificacion,
        }
        guardar_json(salida, mapa)
    guardar_json(salida, mapa)
    return mapa


def construir_render(blueprint, mapa):
    secciones = []
    utilizadas = set()
    for ns, seccion in enumerate(blueprint.secciones, start=1):
        contenidos = []
        for nc, contenido in enumerate(seccion.contenidos, start=1):
            bloques = [BloqueRender(tipo="html", html=contenido.contenido)]
            imagenes = sorted(
                ((nombre, imagen) for nombre, imagen in mapa["imagenes"].items()
                 if imagen["seccion_numero"] == ns and imagen["contenido_numero"] == nc),
                key=lambda item: (item[1]["pagina"], item[0]),
            )
            for nombre, imagen in imagenes:
                bloques.append(BloqueRender(tipo="imagen", imagen=ImagenRender(
                    archivo=nombre, ruta=imagen["ruta"], pagina_fuente=imagen["pagina"],
                    descripcion=imagen["descripcion"], alt=imagen["descripcion"],
                )))
                utilizadas.add(nombre)
            contenidos.append(ContenidoRender(
                titulo=contenido.titulo, paginas_fuente=contenido.paginas_fuente, bloques=bloques,
            ))
        secciones.append(SeccionRender(titulo=seccion.titulo, contenidos=contenidos))
    if utilizadas != set(mapa["imagenes"]):
        raise RuntimeError("Hay imágenes mapeadas que no fueron incorporadas al Render Blueprint.")
    return CursoRender(nombre=blueprint.nombre, shortname=blueprint.shortname,
                       descripcion=blueprint.descripcion, secciones=secciones)


def mapear_subsecciones(contexto, render):
    salida = contexto.output_dir / "subsection_image_mapping.json"
    firma = hashlib.sha256(render.model_dump_json().encode()).hexdigest()
    checkpoint = cargar_checkpoint(salida)
    if checkpoint.get("fuente_sha256") != firma:
        checkpoint = {"fuente_sha256": firma, "asignaciones": {}, "sin_estructura": []}
    sin_estructura = []
    for seccion in render.secciones:
        for contenido in seccion.contenidos:
            html = next(b.html for b in contenido.bloques if b.tipo == "html")
            deteccion = detectar_estructura_contenido(html)
            estructura = deteccion["estructura"]
            for bloque in contenido.bloques:
                imagen = bloque.imagen
                if imagen is None:
                    continue
                if estructura is None:
                    sin_estructura.append({"archivo": imagen.archivo, "contenido": contenido.titulo})
                    continue
                if imagen.archivo in checkpoint["asignaciones"]:
                    continue
                if len(estructura.subsecciones) == 1:
                    indice, justificacion = 0, "Única subsección candidata."
                else:
                    resolucion = asignar_imagen_subseccion(imagen, estructura.subsecciones)
                    indice, justificacion = resolucion.indice_subseccion, resolucion.justificacion
                if not 0 <= indice < len(estructura.subsecciones):
                    raise RuntimeError(f"Subsección inválida para {imagen.archivo}")
                checkpoint["asignaciones"][imagen.archivo] = ImagenSubseccionMapping(
                    archivo=imagen.archivo, contenido=contenido.titulo, tipo_estructura=deteccion["tipo"],
                    indice_subseccion=indice, titulo_subseccion=estructura.subsecciones[indice].titulo,
                    justificacion=justificacion,
                ).model_dump()
                guardar_checkpoint(salida, checkpoint)
    checkpoint["sin_estructura"] = sin_estructura
    guardar_checkpoint(salida, checkpoint)
    return salida


def ejecutar_pipeline_imagenes(contexto: ContextoCurso) -> ContextoCurso:
    ruta = contexto.output_dir / "blueprint.json"
    if not ruta.is_file():
        raise FileNotFoundError(f"Falta Content Blueprint: {ruta}. Ejecutar --etapa contenido primero.")
    blueprint = CursoBlueprint.model_validate_json(ruta.read_text(encoding="utf-8"))
    if blueprint.nombre != contexto.config.nombre or blueprint.shortname != contexto.config.shortname:
        raise ValueError("El Content Blueprint no coincide con la identidad de config.json.")
    documento = extraer_texto_pdf(contexto.config.manual)
    analisis = analizar_imagenes_manual(contexto, documento)
    mapa = mapear_imagenes(contexto, blueprint, analisis, documento)
    render = construir_render(blueprint, mapa)
    contexto.subsection_mapping_path = mapear_subsecciones(contexto, render)
    contexto.render_blueprint_path = guardar_blueprint(contexto.output_dir / "blueprint_render.json", render)
    contexto.content_blueprint_path = ruta
    contexto.image_analysis_path = contexto.output_dir / "image_analysis.json"
    contexto.image_mapping_path = contexto.output_dir / "image_mapping.json"
    return contexto

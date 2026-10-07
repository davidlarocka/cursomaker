"""Preflight y coordinación de contenido y Assessment en Moodle."""
import hashlib
import json
import re
from pathlib import Path
import unicodedata

from models.blueprint import CursoBlueprint
from models.render_blueprint import CursoRender
from models.assessment_blueprint import AssessmentBlueprint
from services.image_pipeline import construir_render
from services.html_renderer import renderizar_contenido
from services.content_executor import preparar_secciones, ejecutar_contenido
from services.assessment_executor import ejecutar_assessment, validar_actividades
from services.blueprint_store import guardar_json
from tools import courses


def normalizar_titulo(titulo):
    return " ".join(unicodedata.normalize("NFKC", titulo).casefold().split())


def separar_prefijo_modulo(titulo):
    coincidencia = re.fullmatch(r"m[oó]dulo\s+(\d+|[ivxlcdm]+)\s*:\s*(.+)", normalizar_titulo(titulo))
    if not coincidencia:
        return None
    etiqueta, texto = coincidencia.groups()
    if etiqueta.isdigit():
        numero = int(etiqueta)
    else:
        if not re.fullmatch(r"m{0,3}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})", etiqueta):
            return None
        valores = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
        numero, mayor = 0, 0
        for letra in reversed(etiqueta):
            valor = valores[letra]
            numero += -valor if valor < mayor else valor
            mayor = max(mayor, valor)
    return numero, texto


def resolver_modulo_secciones(config, render, assessment):
    nombres = {}
    for seccion in render.secciones:
        clave = normalizar_titulo(seccion.titulo)
        if clave in nombres:
            raise ValueError(f"Secciones con títulos duplicados: {seccion.titulo}")
        nombres[clave] = seccion.titulo
    resultado = {}
    for modulo in assessment.modulos:
        titulo = config.modulo_secciones.get(modulo.numero, modulo.titulo)
        destino = nombres.get(normalizar_titulo(titulo))
        if destino is None and modulo.numero not in config.modulo_secciones:
            prefijo = separar_prefijo_modulo(modulo.titulo)
            esperado = prefijo[1] if prefijo and prefijo[0] == modulo.numero else normalizar_titulo(modulo.titulo)
            candidatos = [original for original in nombres.values()
                          if separar_prefijo_modulo(original) == (modulo.numero, esperado)]
            if len(candidatos) == 1:
                destino = candidatos[0]
        if destino is None:
            raise ValueError(
                f"No se pudo asignar módulo {modulo.numero} ({modulo.titulo}) a una sección. "
                f"Agregar modulo_secciones en config.json: {{\"{modulo.numero}\": \"TÍTULO EXACTO DE SECCIÓN\"}}. "
                f"Secciones disponibles: {list(nombres.values())}"
            )
        resultado[modulo.numero] = destino
    return resultado


def cargar_artefactos(contexto):
    salida = contexto.output_dir
    rutas = {nombre: salida / nombre for nombre in (
        "blueprint.json", "assessment_blueprint.json", "image_analysis.json",
        "image_mapping.json", "blueprint_render.json", "subsection_image_mapping.json",
    )}
    for ruta in rutas.values():
        if not ruta.is_file():
            raise FileNotFoundError(f"Falta artefacto para ejecutar Moodle: {ruta}")
    blueprint = CursoBlueprint.model_validate_json(rutas["blueprint.json"].read_text(encoding="utf-8"))
    render = CursoRender.model_validate_json(rutas["blueprint_render.json"].read_text(encoding="utf-8"))
    assessment = AssessmentBlueprint.model_validate_json(rutas["assessment_blueprint.json"].read_text(encoding="utf-8"))
    analisis = json.loads(rutas["image_analysis.json"].read_text(encoding="utf-8"))
    mapa = json.loads(rutas["image_mapping.json"].read_text(encoding="utf-8"))
    subsecciones = json.loads(rutas["subsection_image_mapping.json"].read_text(encoding="utf-8"))
    if (blueprint.nombre != contexto.config.nombre or blueprint.shortname != contexto.config.shortname
            or assessment.curso != contexto.config.nombre):
        raise ValueError("Los blueprints no coinciden con la identidad de config.json.")
    if analisis.get("fuente_sha256") != hashlib.sha256(contexto.config.manual.read_bytes()).hexdigest():
        raise ValueError("El manual cambió; volver a ejecutar --etapa imagenes.")
    firma = hashlib.sha256((blueprint.model_dump_json() + json.dumps(analisis, sort_keys=True)).encode()).hexdigest()
    if mapa.get("fuente_sha256") != firma or construir_render(blueprint, mapa) != render:
        raise ValueError("El Render Blueprint o el mapa visual está desactualizado; ejecutar --etapa imagenes.")
    if subsecciones.get("fuente_sha256") != hashlib.sha256(render.model_dump_json().encode()).hexdigest():
        raise ValueError("El mapa de subsecciones está desactualizado; ejecutar --etapa imagenes.")
    if not render.secciones or not assessment.modulos:
        raise ValueError("Los blueprints no contienen secciones o módulos.")
    validar_actividades(assessment)
    modulo_titulos = resolver_modulo_secciones(contexto.config, render, assessment)
    actividades_destino = set()
    for modulo in assessment.modulos:
        for actividad in modulo.actividades:
            clave = (modulo_titulos[modulo.numero], actividad.tipo, actividad.titulo)
            if clave in actividades_destino:
                raise ValueError(f"Actividades con el mismo nombre y tipo en la sección destino: {actividad.titulo}")
            actividades_destino.add(clave)
    mapping = subsecciones["asignaciones"]
    total = 0
    for seccion in render.secciones:
        titulos = [c.titulo for c in seccion.contenidos]
        if len(titulos) != len(set(titulos)):
            raise ValueError(f"Páginas con títulos duplicados en {seccion.titulo}")
        for contenido in seccion.contenidos:
            html = renderizar_contenido(contenido, mapping, modo="moodle")
            for bloque in contenido.bloques:
                imagen = bloque.imagen
                if imagen is None:
                    continue
                ruta = Path(imagen.ruta)
                if not ruta.is_file():
                    raise FileNotFoundError(f"Falta imagen: {ruta}")
                if html.count("@@PLUGINFILE@@/" + imagen.archivo) != 1:
                    raise ValueError(f"Referencia de imagen inválida: {imagen.archivo}")
                if str(contexto.assets_dir) in html:
                    raise ValueError("El HTML contiene una ruta local.")
        if seccion.contenidos:
            total += 1
    contexto.content_blueprint_path = rutas["blueprint.json"]
    contexto.assessment_blueprint_path = rutas["assessment_blueprint.json"]
    contexto.render_blueprint_path = rutas["blueprint_render.json"]
    return render, assessment, mapping, modulo_titulos, total


def ejecutar_pipeline_moodle(contexto, dry_run=False):
    render, assessment, mapping, modulo_titulos, total = cargar_artefactos(contexto)
    if dry_run:
        contexto.moodle_resultado = {"estado": "validado", "dry_run": True, "paginas": total,
                                     "modulo_secciones": modulo_titulos}
        return contexto
    if not courses.MOODLE_URL or not courses.MOODLE_TOKEN:
        raise ValueError("Faltan MOODLE_URL o MOODLE_TOKEN en el entorno o en .env.")
    encontrados = [c for c in courses.listar_cursos() if c["shortname"] == contexto.config.shortname]
    if len(encontrados) > 1:
        raise RuntimeError("Existe más de un curso con el shortname configurado.")
    if encontrados:
        curso = encontrados[0]
        if curso["nombre"] != contexto.config.nombre or curso["visible"]:
            raise RuntimeError("El curso existente debe coincidir en nombre y permanecer oculto.")
        for archivo, campo in (("execution_render_checkpoint.json", "curso_id"),
                               ("execution_assessment_checkpoint.json", "courseid")):
            ruta = contexto.output_dir / archivo
            if ruta.exists():
                estado = json.loads(ruta.read_text(encoding="utf-8"))
                if estado.get(campo) != curso["id"] or estado.get("moodle_url") != courses.MOODLE_URL.rstrip("/"):
                    raise RuntimeError("El checkpoint pertenece a otro curso o servidor Moodle.")
    else:
        if any((contexto.output_dir / n).exists() for n in
               ("execution_render_checkpoint.json", "execution_assessment_checkpoint.json")):
            raise RuntimeError("Hay checkpoints de ejecución, pero el curso ya no existe en Moodle.")
        curso = courses.crear_curso(contexto.config.nombre, contexto.config.shortname, contexto.config.categoria_id)
    courseid = curso["id"]
    contexto.moodle_curso_id = courseid
    secciones = preparar_secciones(render, courseid)
    contenido = ejecutar_contenido(render, mapping, courseid, secciones,
                                   contexto.output_dir / "execution_render_checkpoint.json")
    actividades = ejecutar_assessment(
        assessment, courseid, modulo_secciones={n: secciones[t] for n, t in modulo_titulos.items()},
        output_dir=str(contexto.output_dir / "h5p"),
        checkpoint_path=contexto.output_dir / "execution_assessment_checkpoint.json",
    )
    contexto.moodle_resultado = {"estado": "completado" if actividades["success"] else "con_pendientes",
                                 "courseid": courseid, **contenido, "assessment": actividades}
    contexto.moodle_report_path = guardar_json(contexto.output_dir / "execution_summary.json", contexto.moodle_resultado)
    return contexto

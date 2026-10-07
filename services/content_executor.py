"""Creación y renderizado de páginas mediante las herramientas Moodle existentes."""
import hashlib
import html as html_module
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

from services.blueprint_store import guardar_json
from services.html_renderer import renderizar_contenido
from tools import courses


def contenido_modulo(seccion, mapping):
    """Conserva los temas y sus imágenes dentro de una sola página."""
    partes = []
    imagenes = []
    for tema in seccion.contenidos:
        partes.append(f"<section><h2>{html_module.escape(tema.titulo)}</h2>"
                      f"{renderizar_contenido(tema, mapping, modo='moodle')}</section>")
        imagenes.extend(b.imagen for b in tema.bloques if b.imagen is not None)
    return "\n".join(partes), imagenes


def generar_pdf(html, imagenes, destino, titulo_modulo):
    """Exporta el mismo HTML de la página, con sus imágenes locales."""
    try:
        from weasyprint import HTML
    except ImportError as exc:
        raise RuntimeError("La exportación requiere instalar weasyprint en el entorno de CursoMaker.") from exc
    for imagen in imagenes:
        html = html.replace("@@PLUGINFILE@@/" + imagen.archivo, Path(imagen.ruta).resolve().as_uri())
    contenido = BeautifulSoup(html, "html.parser")
    for encabezado in contenido.find_all(re.compile(r"^h[1-6]$")):
        primer_texto = next((n for n in encabezado.descendants if isinstance(n, NavigableString)
                             and n.strip()), None)
        if primer_texto is not None:
            corregido = re.sub(r"^(\s*\d+(?:\.\d+)*)(?![\d.])(?=\s|$)",
                               r"\1.", str(primer_texto), count=1)
            primer_texto.replace_with(corregido)
    for numero in contenido.select(".cm-toggle-number"):
        valor = numero.get_text(strip=True)
        if re.fullmatch(r"\d+(?:\.\d+)*", valor):
            numero.string = valor + "."
    portada = f'<div class="cm-cover"><h1>{html_module.escape(titulo_modulo)}</h1></div>'
    documento = ("<meta charset='utf-8'><style>"
                 "@page{size:A4;margin:20mm}body{font-family:sans-serif;line-height:1.5} "
                 ".cm-cover{height:240mm;display:flex;align-items:center;justify-content:center;"
                 "text-align:center;break-after:page} .cm-cover h1{font-size:30pt;margin:0} "
                 "p{text-indent:1.25em} details{display:block} details>*{display:block!important} "
                 "img{max-width:100%;height:auto}</style>" + portada + str(contenido))
    HTML(string=documento).write_pdf(str(destino))


def preparar_secciones(curso, courseid):
    resultado = {}
    for seccion in curso.secciones:
        coincidencias = [s for s in courses.obtener_secciones(courseid) if s["nombre"] == seccion.titulo]
        if len(coincidencias) > 1:
            raise RuntimeError(f"Sección Moodle duplicada: {seccion.titulo}")
        if not coincidencias:
            courses.crear_seccion(courseid, seccion.titulo)
            coincidencias = [s for s in courses.obtener_secciones(courseid) if s["nombre"] == seccion.titulo]
        if len(coincidencias) != 1:
            raise RuntimeError(f"No pudo verificarse la sección: {seccion.titulo}")
        resultado[seccion.titulo] = coincidencias[0]["numero"]
    return resultado


def ejecutar_contenido(curso, mapping, courseid, secciones, checkpoint_path):
    ruta = Path(checkpoint_path)
    estado = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}
    destino = (courses.MOODLE_URL or "").rstrip("/")
    if estado and (estado.get("curso_id") != courseid or estado.get("moodle_url") != destino):
        raise RuntimeError("El checkpoint de contenido pertenece a otro curso o servidor Moodle.")
    estado = estado or {"curso_id": courseid, "moodle_url": destino, "paginas": {}}
    verificadas = 0
    for ns, seccion in enumerate(curso.secciones, 1):
        numero = secciones[seccion.titulo]
        if not seccion.contenidos:
            continue
        clave = f"{ns}:contenido"
        cuerpo, imagenes = contenido_modulo(seccion, mapping)
        pdf = ruta.parent / "pdf" / f"modulo-{ns:02d}-contenido.pdf"
        pdf.parent.mkdir(parents=True, exist_ok=True)
        generar_pdf(cuerpo, imagenes, pdf, seccion.titulo)
        html = cuerpo
        titulo = "Contenido"
        archivos_imagen = b"".join(Path(i.ruta).read_bytes() for i in imagenes)
        firma = hashlib.sha256(html.encode() + archivos_imagen).hexdigest()
        paginas_seccion = [a for s in courses.obtener_secciones(courseid) if s["numero"] == numero
                           for a in s["actividades"] if a["tipo"] == "page"]
        antiguas = [a for a in paginas_seccion
                    if a["nombre"] in {c.titulo for c in seccion.contenidos} and a["nombre"] != titulo]
        registradas = {(p.get("coursemodule_id"), p.get("titulo"))
                       for k, p in estado["paginas"].items() if k.startswith(f"{ns}:")}
        sin_registro = [a["nombre"] for a in antiguas if (a["id"], a["nombre"]) not in registradas]
        if sin_registro:
            raise RuntimeError(f"Páginas por tema sin registro en el checkpoint de {seccion.titulo}: "
                               f"{sin_registro}. Revisarlas manualmente antes de migrar.")
        actuales = [a for a in paginas_seccion if a["nombre"] == titulo]
        recursos = [a for s in courses.obtener_secciones(courseid) if s["numero"] == numero
                    for a in s["actividades"] if a["tipo"] == "pdfprotect"]
        nombre_pdf = "PDF del módulo"
        propios = [a for a in recursos if a["nombre"] == nombre_pdf]
        if len(propios) > 1:
            raise RuntimeError(f"Recursos PDF Protect duplicados en {seccion.titulo}.")
        registro = estado.setdefault("pdfprotect", {}).get(clave, {})
        firma_pdf = hashlib.sha256(("pdfprotect-v2:" + seccion.titulo + cuerpo).encode()
                                    + archivos_imagen).hexdigest()
        if propios:
            if registro and registro.get("coursemodule_id") != propios[0]["id"]:
                raise RuntimeError(f"PDF Protect existente en {seccion.titulo} no coincide con el checkpoint.")
            if registro.get("firma") != firma_pdf:
                courses.crear_pdf_protect(courseid, numero, nombre_pdf, pdf,
                                          existing_cmid=propios[0]["id"])
                estado["pdfprotect"][clave] = {"coursemodule_id": propios[0]["id"],
                                                "firma": firma_pdf}
                guardar_json(ruta, estado)
        else:
            if registro:
                raise RuntimeError(f"Falta el PDF Protect registrado en {seccion.titulo}.")
            creado = courses.crear_pdf_protect(courseid, numero, nombre_pdf, pdf)
            encontrado = [a for s in courses.obtener_secciones(courseid) if s["numero"] == numero
                          for a in s["actividades"] if a["id"] == creado["coursemoduleid"]
                          and a["tipo"] == "pdfprotect" and a["nombre"] == nombre_pdf]
            if len(encontrado) != 1:
                raise RuntimeError(f"No se pudo verificar PDF Protect en {seccion.titulo}.")
            estado["pdfprotect"][clave] = {"coursemodule_id": creado["coursemoduleid"],
                                            "firma": firma_pdf}
            guardar_json(ruta, estado)
        if len(actuales) > 1:
            raise RuntimeError(f"Página Moodle duplicada: {titulo}")
        if not actuales:
            resultado = courses.crear_pagina(courseid, numero, titulo, "<p>Preparando contenido.</p>")
            cmid = resultado["coursemodule_id"]
        else:
            cmid = actuales[0]["id"]
        anterior = estado["paginas"].get(clave, {})
        pagina = courses.obtener_pagina(courseid, cmid)
        coincide = (pagina.get("encontrada") and pagina.get("nombre") == titulo
                    and courses._normalizar_html_moodle(pagina.get("contenido", "")) == courses._normalizar_html_moodle(html))
        if not (coincide and anterior.get("firma") == firma and anterior.get("coursemodule_id") == cmid):
            for imagen in imagenes:
                courses.subir_archivo_pagina(cmid, imagen.ruta)
            resultado = courses.actualizar_pagina(cmid, titulo, html)
            if not resultado.get("verificada"):
                raise RuntimeError(f"No pudo verificarse la página: {titulo}")
        estado["paginas"][clave] = {"titulo": titulo, "coursemodule_id": cmid,
                                    "firma": firma, "estado": "verificada"}
        guardar_json(ruta, estado)
        for antigua in antiguas:
            courses.eliminar_paginas([antigua["id"]])
            if any(a["id"] == antigua["id"] for s in courses.obtener_secciones(courseid)
                   if s["numero"] == numero for a in s["actividades"]):
                raise RuntimeError(f"No se pudo verificar la eliminación de {antigua['nombre']}.")
            for k, p in list(estado["paginas"].items()):
                if k != clave and p.get("coursemodule_id") == antigua["id"]:
                    del estado["paginas"][k]
            guardar_json(ruta, estado)
        verificadas += 1
    return {"paginas_verificadas": verificadas}

"""Creación y renderizado de páginas mediante las herramientas Moodle existentes."""
import hashlib
import json
from pathlib import Path

from services.blueprint_store import guardar_json
from services.html_renderer import renderizar_contenido
from tools import courses


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
        for nc, contenido in enumerate(seccion.contenidos, 1):
            clave = f"{ns}:{nc}"
            html = renderizar_contenido(contenido, mapping, modo="moodle")
            imagenes = [b.imagen for b in contenido.bloques if b.imagen is not None]
            firma = hashlib.sha256(html.encode() + b"".join(Path(i.ruta).read_bytes() for i in imagenes)).hexdigest()
            actuales = [a for s in courses.obtener_secciones(courseid) if s["numero"] == numero
                        for a in s["actividades"] if a["tipo"] == "page" and a["nombre"] == contenido.titulo]
            if len(actuales) > 1:
                raise RuntimeError(f"Página Moodle duplicada: {contenido.titulo}")
            if not actuales:
                resultado = courses.crear_pagina(courseid, numero, contenido.titulo, "<p>Preparando contenido.</p>")
                cmid = resultado["coursemodule_id"]
            else:
                cmid = actuales[0]["id"]
            anterior = estado["paginas"].get(clave, {})
            pagina = courses.obtener_pagina(courseid, cmid)
            coincide = (pagina.get("encontrada") and pagina.get("nombre") == contenido.titulo
                        and courses._normalizar_html_moodle(pagina.get("contenido", "")) == courses._normalizar_html_moodle(html))
            if not (coincide and anterior.get("firma") == firma and anterior.get("coursemodule_id") == cmid):
                for imagen in imagenes:
                    courses.subir_imagen_pagina(cmid, imagen.ruta)
                resultado = courses.actualizar_pagina(cmid, contenido.titulo, html)
                if not resultado.get("verificada"):
                    raise RuntimeError(f"No pudo verificarse la página: {contenido.titulo}")
            estado["paginas"][clave] = {"titulo": contenido.titulo, "coursemodule_id": cmid,
                                        "firma": firma, "estado": "verificada"}
            guardar_json(ruta, estado)
            verificadas += 1
    return {"paginas_verificadas": verificadas}

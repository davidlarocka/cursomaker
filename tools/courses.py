import base64
from pathlib import Path
import os
import re

import requests
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

MOODLE_URL = os.getenv("MOODLE_URL")
MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")

def flatten_moodle_params(data, prefix=""):
    params = {}

    for key, value in data.items():

        new_key = f"{prefix}[{key}]" if prefix else key

        if isinstance(value, list):

            for index, item in enumerate(value):

                if isinstance(item, dict):
                    params.update(
                        flatten_moodle_params(
                            item,
                            f"{new_key}[{index}]"
                        )
                    )
                else:
                    params[
                        f"{new_key}[{index}]"
                    ] = item

        elif isinstance(value, dict):

            params.update(
                flatten_moodle_params(
                    value,
                    new_key
                )
            )

        else:
            params[new_key] = value

    return params

def _moodle_request(function, params=None):
    """
    Ejecuta una petición REST contra Moodle.
    """

    if not MOODLE_URL:
        raise ValueError("No se encontró MOODLE_URL en .env")

    if not MOODLE_TOKEN:
        raise ValueError("No se encontró MOODLE_TOKEN en .env")

    endpoint = f"{MOODLE_URL}/webservice/rest/server.php"

    data = {
        "wstoken": MOODLE_TOKEN,
        "wsfunction": function,
        "moodlewsrestformat": "json",
    }

    if params:
        data.update(params)

    data = flatten_moodle_params(data)

    response = requests.post(
        endpoint,
        data=data,
        timeout=10
    )

    response.raise_for_status()

    result = response.json()

    if isinstance(result, dict) and "exception" in result:
        raise RuntimeError(
            f"Moodle error: {result.get('message')}"
        )

    return result


def listar_cursos():
    """
    Obtiene los cursos reales disponibles en Moodle.
    """

    print("🔧 Consultando cursos reales en Moodle...")

    cursos = _moodle_request(
        "core_course_get_courses"
    )

    return [
        {
            "id": curso.get("id"),
            "nombre": curso.get("fullname"),
            "shortname": curso.get("shortname"),
            "visible": str(curso.get("visible")).lower() in ("1", "true"),
        }
        for curso in cursos
    ]


def obtener_curso(nombre):
    """
    Busca un curso real por nombre o shortname.
    """

    print(f"🔧 Buscando curso real: '{nombre}'")

    cursos = listar_cursos()

    nombre_busqueda = nombre.lower().strip()

    # Coincidencia exacta
    for curso in cursos:

        if curso["nombre"].lower() == nombre_busqueda:
            return {
                "encontrado": True,
                "curso": curso
            }

        if curso["shortname"].lower() == nombre_busqueda:
            return {
                "encontrado": True,
                "curso": curso
            }

    # Coincidencia parcial
    for curso in cursos:

        if nombre_busqueda in curso["nombre"].lower():
            return {
                "encontrado": True,
                "curso": curso
            }

    return {
        "encontrado": False,
        "busqueda": nombre
    }
    
    
def crear_curso(nombre, shortname, categoria_id=1):
    """
    Crea un curso real en Moodle.

    Por seguridad, todos los cursos creados por CursoMaker
    nacen ocultos.
    """

    print(f"🔧 Creando curso real en Moodle: '{nombre}'")

    params = {
        "courses[0][fullname]": nombre,
        "courses[0][shortname]": shortname,
        "courses[0][categoryid]": categoria_id,
        "courses[0][visible]": 0,
    }

    resultado = _moodle_request(
        "core_course_create_courses",
        params
    )

    if not resultado:
        raise RuntimeError("Moodle no devolvió información del curso creado.")

    curso = resultado[0]

    return {
        "creado": True,
        "id": curso.get("id"),
        "shortname": curso.get("shortname"),
        "nombre": nombre,
        "visible": False
    }    
    
def actualizar_curso(curso_id, visible=None):
    """
    Actualiza propiedades de un curso existente en Moodle.
    Por ahora permite modificar su visibilidad.
    """
    print(f"🔧 Actualizando curso Moodle ID {curso_id}...")

    params = {
        "courses[0][id]": curso_id,
    }

    if visible is not None:
        params["courses[0][visible]"] = 1 if visible else 0

    _moodle_request(
        "core_course_update_courses",
        params
    )

    return {
        "actualizado": True,
        "id": curso_id,
    }    
    
def crear_seccion(curso_id, nombre):
    """
    Crea una sección real dentro de un curso Moodle.
    """

    print(
        f"🔧 Creando sección '{nombre}' "
        f"en el curso ID {curso_id}..."
    )

    params = {
        "courseid": curso_id,
        "name": nombre,
    }

    resultado = _moodle_request(
        "local_cursomaker_create_section",
        params
    )

    return {
        "creada": True,
        "id": resultado.get("id"),
        "numero": resultado.get("section"),
        "nombre": resultado.get("name"),
        "curso_id": resultado.get("courseid"),
    }
    
def obtener_secciones(curso_id):
    """
    Obtiene las secciones reales de un curso Moodle,
    incluyendo las actividades que contiene cada sección.
    """

    print(
        f"🔧 Consultando secciones del curso ID {curso_id}..."
    )

    resultado = _moodle_request(
        "core_course_get_contents",
        {
            "courseid": curso_id
        }
    )

    secciones = []

    for seccion in resultado:
        secciones.append({
            "id": seccion.get("id"),
            "numero": seccion.get("section"),
            "nombre": seccion.get("name"),
            "visible": bool(seccion.get("visible")),
            "actividades": [
                {
                    "id": modulo.get("id"),
                    "nombre": modulo.get("name"),
                    "tipo": modulo.get("modname"),
                }
                for modulo in seccion.get("modules", [])
            ]
        })

    return secciones

def crear_pagina(curso_id, seccion_numero, nombre, contenido):
    """
    Crea una página Moodle real dentro de una sección.
    """

    print(
        f"🔧 Creando página '{nombre}' "
        f"en curso ID {curso_id}, sección {seccion_numero}..."
    )

    resultado = _moodle_request(
        "local_cursomaker_create_page",
        {
            "courseid": curso_id,
            "section": seccion_numero,
            "name": nombre,
            "content": contenido,
        }
    )

    coursemodule_id = resultado.get("coursemoduleid")

    secciones = obtener_secciones(curso_id)

    pagina_encontrada = None

    for seccion in secciones:
        for actividad in seccion["actividades"]:
            if actividad["id"] == coursemodule_id:
                pagina_encontrada = {
                    "id": actividad["id"],
                    "nombre": actividad["nombre"],
                    "tipo": actividad["tipo"],
                    "seccion_numero": seccion["numero"],
                    "seccion_nombre": seccion["nombre"],
                }
                break

        if pagina_encontrada:
            break

    if not pagina_encontrada:
        raise RuntimeError(
            "Moodle informó que la página fue creada, "
            "pero no pudo verificarse posteriormente."
        )

    return {
        "creada": True,
        "verificada": True,
        "coursemodule_id": coursemodule_id,
        "instance_id": resultado.get("instanceid"),
        "curso_id": resultado.get("courseid"),
        "seccion_numero": resultado.get("section"),
        "nombre": resultado.get("name"),
        "verificacion": pagina_encontrada,
    }
    
def _normalizar_html_moodle(html):
    """
    Normaliza las URLs que Moodle genera a partir de
    @@PLUGINFILE@@ para poder comparar el HTML enviado
    con el HTML recuperado mediante Web Service.

    El resto del HTML permanece intacto.
    """

    patron = (
        r'https?://[^"\']+/'
        r'webservice/pluginfile\.php/'
        r'\d+/mod_page/content/\d+/'
        r'([^"\'?]+)'
        r'(?:\?[^"\']*)?'
    )

    return re.sub(
        patron,
        r'@@PLUGINFILE@@/\1',
        html,
    ).strip()    
    
def actualizar_pagina(coursemodule_id, nombre, contenido):
    """
    Actualiza una página Moodle existente y verifica
    posteriormente que Moodle haya guardado los cambios.
    """

    print(
        f"🔧 Actualizando página '{nombre}' "
        f"(course module ID {coursemodule_id})..."
    )

    resultado = _moodle_request(
        "local_cursomaker_update_page",
        {
            "coursemoduleid": coursemodule_id,
            "name": nombre,
            "content": contenido,
        }
    )

    coursemodule_id = resultado.get("coursemoduleid")
    curso_id = resultado.get("courseid")

    # Volvemos a leer la página directamente desde Moodle.
    pagina = obtener_pagina(
        curso_id=curso_id,
        coursemodule_id=coursemodule_id
    )

    if not pagina["encontrada"]:
        raise RuntimeError(
            "Moodle informó que la página fue actualizada, "
            "pero no pudo encontrarse posteriormente."
        )

    if pagina["nombre"] != nombre:
        raise RuntimeError(
            "La página fue actualizada, pero el nombre guardado "
            "en Moodle no coincide con el solicitado."
        )

    contenido_enviado = _normalizar_html_moodle(
        contenido
    )

    contenido_guardado = _normalizar_html_moodle(
        pagina["contenido"]
    )

    if contenido_guardado != contenido_enviado:
        raise RuntimeError(
            "La página fue actualizada, pero el contenido "
            "guardado en Moodle no coincide con el contenido "
            "enviado después de normalizar las URLs de archivos."
        )

    return {
        "actualizada": True,
        "verificada": True,
        "coursemodule_id": coursemodule_id,
        "instance_id": resultado.get("instanceid"),
        "curso_id": curso_id,
        "nombre": pagina["nombre"],
        "verificacion": {
            "nombre_correcto": True,
            "contenido_correcto": True,
            "seccion_numero": pagina["seccion_numero"],
            "visible": pagina["visible"],
        },
    }
    
def obtener_pagina(curso_id, coursemodule_id):
    """
    Obtiene una página Moodle real y su contenido HTML
    usando el course module ID.
    """

    print(
        f"🔧 Consultando página course module ID "
        f"{coursemodule_id} del curso ID {curso_id}..."
    )

    resultado = _moodle_request(
        "mod_page_get_pages_by_courses",
        {
            "courseids[0]": curso_id
        }
    )

    for pagina in resultado.get("pages", []):
        if pagina.get("coursemodule") == coursemodule_id:
            return {
                "encontrada": True,
                "id": pagina.get("id"),
                "coursemodule_id": pagina.get("coursemodule"),
                "curso_id": pagina.get("course"),
                "seccion_numero": pagina.get("section"),
                "nombre": pagina.get("name"),
                "contenido": pagina.get("content"),
                "formato": pagina.get("contentformat"),
                "visible": pagina.get("visible"),
            }

    return {
        "encontrada": False,
        "curso_id": curso_id,
        "coursemodule_id": coursemodule_id,
    }
    
def subir_imagen_pagina(
    coursemodule_id,
    ruta_imagen,
):
    ruta = Path(ruta_imagen)

    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe la imagen: {ruta}"
        )

    if not ruta.is_file():
        raise ValueError(
            f"La ruta no es un archivo: {ruta}"
        )

    contenido_base64 = base64.b64encode(
        ruta.read_bytes()
    ).decode("ascii")

    resultado = _moodle_request(
        "local_cursomaker_upload_page_image",
        {
            "coursemoduleid": coursemodule_id,
            "filename": ruta.name,
            "contentbase64": contenido_base64,
        },
    )

    if (
        resultado.get("filename")
        != ruta.name
    ):
        raise RuntimeError(
            "Moodle devolvió un nombre "
            "de archivo inesperado."
        )

    if resultado.get("filesize") != ruta.stat().st_size:
        raise RuntimeError(
            "El tamaño almacenado en Moodle "
            "no coincide con el archivo local."
        )

    return resultado

def crear_assignment(
    curso_id: int,
    seccion_numero: int,
    nombre: str,
    descripcion: str,
) -> dict:
    resultado = _moodle_request(
        "local_cursomaker_create_assignment",
        {
            "courseid": curso_id,
            "sectionnum": seccion_numero,
            "name": nombre,
            "intro": descripcion,
        },
    )

    if not resultado.get("created"):
        raise RuntimeError(
            f"Moodle no confirmó la creación del Assignment: {nombre}"
        )

    if int(resultado["courseid"]) != int(curso_id):
        raise RuntimeError(
            "El Assignment fue creado en un curso diferente al esperado."
        )

    if int(resultado["sectionnum"]) != int(seccion_numero):
        raise RuntimeError(
            "El Assignment fue creado en una sección diferente a la esperada."
        )

    if resultado["name"] != nombre:
        raise RuntimeError(
            "El nombre devuelto por Moodle no coincide con el solicitado."
        )

    return resultado

def crear_foro(
    curso_id: int,
    seccion_numero: int,
    nombre: str,
    descripcion: str,
) -> dict:
    resultado = _moodle_request(
        "local_cursomaker_create_forum",
        {
            "courseid": curso_id,
            "sectionnum": seccion_numero,
            "name": nombre,
            "intro": descripcion,
        },
    )

    if not resultado.get("created"):
        raise RuntimeError(
            f"Moodle no confirmó la creación del foro: {nombre}"
        )

    if int(resultado["courseid"]) != int(curso_id):
        raise RuntimeError(
            "El foro fue creado en un curso diferente al esperado."
        )

    if int(resultado["sectionnum"]) != int(seccion_numero):
        raise RuntimeError(
            "El foro fue creado en una sección diferente a la esperada."
        )

    if resultado["name"] != nombre:
        raise RuntimeError(
            "El nombre devuelto por Moodle no coincide con el solicitado."
        )

    return resultado

def crear_quiz(
    curso_id: int,
    seccion_numero: int,
    nombre: str,
    descripcion: str,
) -> dict:
    resultado = _moodle_request(
        "local_cursomaker_create_quiz",
        {
            "courseid": curso_id,
            "sectionnum": seccion_numero,
            "name": nombre,
            "intro": descripcion,
        },
    )

    if not resultado.get("created"):
        raise RuntimeError(
            f"Moodle no confirmó la creación del quiz: {nombre}"
        )

    if int(resultado["courseid"]) != int(curso_id):
        raise RuntimeError(
            "El quiz fue creado en un curso diferente."
        )

    if int(resultado["sectionnum"]) != int(seccion_numero):
        raise RuntimeError(
            "El quiz fue creado en una sección diferente."
        )

    return resultado
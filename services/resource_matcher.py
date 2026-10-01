import re
from typing import Any, Dict, List


STOPWORDS = {
    "de",
    "la",
    "el",
    "los",
    "las",
    "un",
    "una",
    "y",
    "en",
    "para",
    "con",
    "del",
    "al",
    "por",
    "que",
    "se",
    "su",
    "sus",
    "a",
    "o",
    "u",
    "sobre",
}


def normalizar_texto(texto: str) -> List[str]:
    """
    Convierte texto en palabras comparables.
    """
    texto = (texto or "").lower()

    texto = re.sub(
        r"[^a-záéíóúüñ0-9\s]",
        " ",
        texto,
    )

    palabras = texto.split()

    return [
        palabra
        for palabra in palabras
        if len(palabra) >= 4 and palabra not in STOPWORDS
    ]


def construir_texto_actividad(actividad) -> str:
    """
    Obtiene el texto disponible de una actividad sin asumir
    una implementación concreta de cada tipo H5P.
    """

    partes = [
        getattr(actividad, "titulo", ""),
    ]

    for campo in (
        "descripcion",
        "contenido",
        "instrucciones",
        "situacion",
        "texto",
        "pregunta",
    ):
        valor = getattr(actividad, campo, None)

        if isinstance(valor, str):
            partes.append(valor)

    return " ".join(partes)


def calcular_coincidencia(
    actividad,
    recurso: Dict[str, Any],
) -> float:
    """
    Calcula una puntuación semántica simple basada en coincidencia
    de palabras entre la actividad y el recurso.

    No utiliza conocimiento externo ni llamadas a IA.
    """

    texto_actividad = construir_texto_actividad(
        actividad
    )

    texto_recurso = " ".join(
        [
            recurso.get("descripcion", ""),
            recurso.get("relacion_con_texto", ""),
            recurso.get("tipo_imagen", ""),
        ]
    )

    palabras_actividad = set(
        normalizar_texto(texto_actividad)
    )

    palabras_recurso = set(
        normalizar_texto(texto_recurso)
    )

    if not palabras_actividad or not palabras_recurso:
        return 0.0

    coincidencias = (
        palabras_actividad & palabras_recurso
    )

    return len(coincidencias) / len(palabras_actividad)


def buscar_recursos_candidatos(
    actividad,
    recursos: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Busca recursos visuales candidatos para una actividad.
    """

    paginas = set(
        getattr(
            actividad,
            "paginas_fuente",
            [],
        )
    )

    candidatos = []

    for recurso in recursos:

        if not recurso.get("es_pedagogica"):
            continue

        if recurso.get("recomendacion") != "incluir":
            continue

        pagina = recurso.get("pagina")

        # Si la actividad tiene páginas fuente,
        # priorizamos recursos de esas páginas.
        coincidencia_pagina = (
            pagina in paginas
            if paginas
            else True
        )

        puntuacion = calcular_coincidencia(
            actividad,
            recurso,
        )

        if coincidencia_pagina:
            puntuacion += 0.5

        if puntuacion > 0:
            candidatos.append(
                {
                    **recurso,
                    "puntuacion": round(
                        puntuacion,
                        4,
                    ),
                }
            )

    candidatos.sort(
        key=lambda recurso: recurso["puntuacion"],
        reverse=True,
    )

    return candidatos


def asignar_recursos_a_actividad(
    actividad,
    recursos: List[Dict[str, Any]],
    max_recursos: int = 3,
) -> List[Dict[str, Any]]:
    """
    Asigna los recursos más relevantes a una actividad.

    Esta primera versión es deliberadamente conservadora:
    solamente selecciona recursos con coincidencia positiva.
    """

    candidatos = buscar_recursos_candidatos(
        actividad,
        recursos,
    )

    return candidatos[:max_recursos]


def asignar_recursos_a_blueprint(
    blueprint,
    recursos: List[Dict[str, Any]],
    max_recursos_por_actividad: int = 3,
):
    """
    Recorre todas las actividades del AssessmentBlueprint
    y asigna recursos visuales candidatos.

    No modifica Moodle.
    """

    resultados = []

    for modulo in blueprint.modulos:

        for actividad in modulo.actividades:

            asignados = asignar_recursos_a_actividad(
                actividad,
                recursos,
                max_recursos=max_recursos_por_actividad,
            )

            resultados.append(
                {
                    "modulo": modulo.numero,
                    "modulo_titulo": modulo.titulo,
                    "actividad": actividad.titulo,
                    "tipo": actividad.tipo,
                    "recursos": asignados,
                }
            )

    return resultados

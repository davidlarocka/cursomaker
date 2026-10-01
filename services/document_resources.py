import json
from pathlib import Path
from typing import Any, Dict, List


def cargar_image_analysis(ruta_json: str = "image_analysis.json") -> Dict[str, Any]:
    """
    Carga el análisis visual previamente generado por CursoMaker.
    No realiza llamadas a OpenAI.
    """
    ruta = Path(ruta_json)

    if not ruta.exists():
        raise FileNotFoundError(
            f"No existe el análisis de imágenes: {ruta}"
        )

    with ruta.open("r", encoding="utf-8") as f:
        return json.load(f)


def construir_inventario_recursos(
    ruta_json: str = "image_analysis.json",
) -> List[Dict[str, Any]]:
    """
    Convierte image_analysis.json en un inventario normalizado
    de recursos visuales utilizables por CursoMaker.
    """

    data = cargar_image_analysis(ruta_json)

    imagenes = data.get("imagenes", {})

    recursos = []

    for archivo, imagen in imagenes.items():
        recursos.append({
            "tipo": "imagen",
            "archivo": archivo,
            "ruta": imagen.get("ruta"),
            "pagina": imagen.get("pagina"),
            "ancho": imagen.get("ancho"),
            "alto": imagen.get("alto"),

            "es_pedagogica": imagen.get(
                "es_pedagogica",
                False,
            ),

            "tipo_imagen": imagen.get("tipo"),

            "descripcion": imagen.get(
                "descripcion",
                "",
            ),

            "relacion_con_texto": imagen.get(
                "relacion_con_texto",
                "",
            ),

            "recomendacion": imagen.get(
                "recomendacion",
                "descartar",
            ),

            "estado": imagen.get(
                "estado",
                "desconocido",
            ),
        })

    return recursos


def obtener_recursos_pedagogicos(
    ruta_json: str = "image_analysis.json",
) -> List[Dict[str, Any]]:
    """
    Devuelve únicamente recursos visuales que el análisis
    recomienda incluir.
    """

    recursos = construir_inventario_recursos(ruta_json)

    return [
        recurso
        for recurso in recursos
        if (
            recurso["es_pedagogica"]
            and recurso["recomendacion"] == "incluir"
        )
    ]


def obtener_recursos_de_pagina(
    pagina: int,
    ruta_json: str = "image_analysis.json",
) -> List[Dict[str, Any]]:
    """
    Devuelve los recursos visuales asociados a una página.
    """

    recursos = construir_inventario_recursos(ruta_json)

    return [
        recurso
        for recurso in recursos
        if recurso["pagina"] == pagina
    ]

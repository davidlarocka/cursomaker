import json
from pathlib import Path
from services.blueprint_store import guardar_json


def cargar_analisis_imagenes(ruta):
    ruta = Path(ruta)

    if not ruta.exists():
        return {
            "imagenes": {}
        }

    with ruta.open(
        "r",
        encoding="utf-8",
    ) as archivo:
        return json.load(archivo)


def guardar_analisis_imagenes(
    ruta,
    estado,
):
    guardar_json(Path(ruta), estado)

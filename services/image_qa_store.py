import json
from pathlib import Path


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
    ruta = Path(ruta)

    with ruta.open(
        "w",
        encoding="utf-8",
    ) as archivo:
        json.dump(
            estado,
            archivo,
            ensure_ascii=False,
            indent=2,
        )
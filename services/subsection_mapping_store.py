import json
from pathlib import Path


def cargar_checkpoint(ruta):
    ruta = Path(ruta)

    if not ruta.exists():
        return {
            "asignaciones": {},
        }

    with ruta.open(
        "r",
        encoding="utf-8",
    ) as archivo:
        return json.load(archivo)


def guardar_checkpoint(
    ruta,
    datos,
):
    ruta = Path(ruta)

    with ruta.open(
        "w",
        encoding="utf-8",
    ) as archivo:
        json.dump(
            datos,
            archivo,
            ensure_ascii=False,
            indent=2,
        )
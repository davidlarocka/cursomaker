import json
from pathlib import Path
from services.blueprint_store import guardar_json


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
    guardar_json(Path(ruta), datos)

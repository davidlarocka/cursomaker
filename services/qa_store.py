import json
from pathlib import Path


def cargar_qa(ruta):
    """
    Carga el estado de QA si existe.
    """

    ruta = Path(ruta)

    if not ruta.exists():
        return {
            "contenidos": {}
        }

    with ruta.open(
        "r",
        encoding="utf-8",
    ) as archivo:
        return json.load(archivo)


def guardar_qa(ruta, estado):
    """
    Guarda el estado actual del proceso de QA.
    """

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
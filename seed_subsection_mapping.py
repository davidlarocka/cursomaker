import json

from services.subsection_mapping_store import (
    cargar_checkpoint,
    guardar_checkpoint,
)


RUTA_PILOTO = "pilot_image_mapping.json"
RUTA_CHECKPOINT = "subsection_image_mapping.json"


with open(
    RUTA_PILOTO,
    "r",
    encoding="utf-8",
) as archivo:
    piloto = json.load(archivo)


checkpoint = cargar_checkpoint(
    RUTA_CHECKPOINT
)

asignaciones = checkpoint.get(
    "asignaciones",
    {}
)


contenido = piloto["contenido"]


for archivo, datos in piloto["imagenes"].items():

    asignaciones[archivo] = {
        "archivo": archivo,
        "contenido": contenido,
        "tipo_estructura": "lista",
        "indice_subseccion": datos[
            "indice_subseccion"
        ],
        "titulo_subseccion": datos[
            "subseccion"
        ],
        "justificacion": datos[
            "justificacion"
        ],
    }

    print(
        f"✅ Importada: {archivo}"
    )


guardar_checkpoint(
    RUTA_CHECKPOINT,
    {
        "asignaciones": asignaciones,
        "sin_estructura": checkpoint.get(
            "sin_estructura",
            [],
        ),
    },
)


print()
print(
    f"💾 Asignaciones guardadas: "
    f"{len(asignaciones)}"
)
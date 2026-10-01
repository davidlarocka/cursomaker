import json

from models.assessment_blueprint import (
    AssessmentBlueprint,
    ActividadDiscusion,
)
from services.assessment_renderer import renderizar_actividad_discusion


BLUEPRINT_PATH = "assessment_blueprint.json"
ACTIVIDAD_ID = "omi141-m01-discusion-01"


with open(BLUEPRINT_PATH, "r", encoding="utf-8") as archivo:
    datos = json.load(archivo)

blueprint = AssessmentBlueprint.model_validate(datos)

actividad = None

for modulo in blueprint.modulos:
    for item in modulo.actividades:
        if item.id_logico == ACTIVIDAD_ID:
            actividad = item
            break

    if actividad:
        break


if actividad is None:
    raise RuntimeError(
        f"No se encontró la actividad {ACTIVIDAD_ID}"
    )

if not isinstance(actividad, ActividadDiscusion):
    raise TypeError(
        f"{ACTIVIDAD_ID} no es una ActividadDiscusion"
    )


html = renderizar_actividad_discusion(actividad)


print("=== PILOTO FORUM ===")
print(f"ID lógico: {actividad.id_logico}")
print(f"Módulo: {actividad.modulo}")
print(f"Título: {actividad.titulo}")
print(f"Estado: {actividad.estado}")
print(f"Páginas fuente: {actividad.paginas_fuente}")
print(
    "Requiere interacción con pares:",
    actividad.requiere_interaccion_pares,
)
print(
    "Mínimo respuestas a pares:",
    actividad.minimo_respuestas_pares,
)

print("\n=== HTML QUE RECIBIRÍA MOODLE ===")
print(html)

print("\n=== RESULTADO ===")
print("✅ Dry-run completado. Moodle NO fue modificado.")
import json

from models.assessment_blueprint import (
    AssessmentBlueprint,
    ActividadDiscusion,
)
from services.assessment_renderer import renderizar_actividad_discusion
from tools.courses import crear_foro


COURSE_ID = 7
SECTION_NUMBER = 2
ACTIVIDAD_ID = "omi141-m01-discusion-01"


with open("assessment_blueprint.json", "r", encoding="utf-8") as archivo:
    blueprint = AssessmentBlueprint.model_validate(json.load(archivo))


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
        f"No se encontró {ACTIVIDAD_ID}"
    )

if not isinstance(actividad, ActividadDiscusion):
    raise TypeError(
        f"{ACTIVIDAD_ID} no es una ActividadDiscusion"
    )

if actividad.modulo != 1:
    raise RuntimeError(
        f"La actividad pertenece al módulo {actividad.modulo}, no al módulo 1."
    )

# Esta actividad exige interacción con al menos un compañero.
if not actividad.requiere_interaccion_pares:
    raise RuntimeError(
        "El blueprint no indica interacción con pares para esta actividad."
    )

if actividad.minimo_respuestas_pares < 1:
    raise RuntimeError(
        "El mínimo de respuestas a pares no es válido."
    )


html = renderizar_actividad_discusion(actividad)


print("=== EJECUCIÓN PILOTO FORUM ===")
print(f"Curso Moodle: {COURSE_ID}")
print(f"Sección Moodle: {SECTION_NUMBER}")
print(f"Actividad: {actividad.titulo}")
print(f"ID lógico: {actividad.id_logico}")
print(
    f"Interacción con pares: "
    f"{actividad.minimo_respuestas_pares}"
)
print()


resultado = crear_foro(
    curso_id=COURSE_ID,
    seccion_numero=SECTION_NUMBER,
    nombre=actividad.titulo,
    descripcion=html,
)


print("=== RESULTADO MOODLE ===")
print(f"Creado: {resultado['created']}")
print(f"Course module ID: {resultado['coursemoduleid']}")
print(f"Forum instance ID: {resultado['instanceid']}")
print(f"Curso: {resultado['courseid']}")
print(f"Sección: {resultado['sectionnum']}")
print(f"Nombre: {resultado['name']}")
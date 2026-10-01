import json

from models.assessment_blueprint import AssessmentBlueprint
from services.assessment_executor import ejecutar_assessment


COURSE_ID = 7


with open("assessment_blueprint.json", encoding="utf-8") as f:
    datos = json.load(f)

blueprint = AssessmentBlueprint.model_validate(datos)

# Ejecutamos únicamente las actividades H5P.
resultado = ejecutar_assessment(
    blueprint=blueprint,
    courseid=COURSE_ID,
)

print("\n=== RESULTADO EJECUCIÓN H5P ===")

for item in resultado["resultados"]:
    if item["tipo"] == "h5p":
        print(
            f"\n✅ Módulo {item['modulo']}"
            f" | Sección {item['section']}"
            f" | {item['actividad']}"
        )
        print(item["resultado"])

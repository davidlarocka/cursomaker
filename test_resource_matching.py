from services.document_resources import (
    obtener_recursos_pedagogicos,
)

from services.resource_matcher import (
    asignar_recursos_a_blueprint,
)

from services.assessment_blueprint_generator import (
    generar_assessment_blueprint,
)


RUTA_DOCUMENTO = (
    "documents/"
    "ACTIVIDADES Y EVALUACIONES OMI 1.41.docx"
)


def main():

    print("🧠 Generando AssessmentBlueprint...")

    # Ajustaremos esta llamada a la firma real de tu
    # generador si el documento se carga de otra manera.
    blueprint = generar_assessment_blueprint(
        RUTA_DOCUMENTO
    )

    print()

    print("🖼️ Cargando recursos pedagógicos...")

    recursos = obtener_recursos_pedagogicos()

    print(
        f"Recursos disponibles: {len(recursos)}"
    )

    print()

    resultados = asignar_recursos_a_blueprint(
        blueprint,
        recursos,
    )

    print("=" * 70)
    print("=== DRY RUN RESOURCE MATCHING ===")
    print("=" * 70)

    for resultado in resultados:

        print()
        print(
            f"📚 Módulo {resultado['modulo']}: "
            f"{resultado['modulo_titulo']}"
        )

        print(
            f"   {resultado['tipo']}: "
            f"{resultado['actividad']}"
        )

        if not resultado["recursos"]:
            print(
                "      └─ Sin recursos candidatos"
            )
            continue

        for recurso in resultado["recursos"]:

            print(
                "      └─ "
                f"Pág. {recurso['pagina']} | "
                f"{recurso['archivo']} | "
                f"score={recurso['puntuacion']}"
            )

            print(
                f"         {recurso['descripcion']}"
            )

    print()
    print("=" * 70)
    print("=== FIN DRY RUN ===")
    print("=" * 70)


if __name__ == "__main__":
    main()

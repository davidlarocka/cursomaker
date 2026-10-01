import argparse

from services.orchestrator import ejecutar_cursomaker


def main():
    parser = argparse.ArgumentParser(description="CursoMaker Orchestrator")
    parser.add_argument(
        "curso",
        help="Directorio del curso (ej: documents/omi110)",
    )
    args = parser.parse_args()

    try:
        contexto = ejecutar_cursomaker(args.curso)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")

    print(f"Preparación completada: {contexto.config.nombre}")
    print(f"Shortname: {contexto.config.shortname}")
    print(f"Assets: {contexto.assets_dir}")
    print(f"Output: {contexto.output_dir}")
    print("Generación de blueprints y ejecución Moodle pendientes de integración.")


if __name__ == "__main__":
    main()

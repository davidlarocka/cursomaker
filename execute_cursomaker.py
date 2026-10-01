import argparse

from services.orchestrator import ejecutar_cursomaker


def main():
    parser = argparse.ArgumentParser(description="CursoMaker Orchestrator")
    parser.add_argument(
        "curso",
        help="Directorio del curso (ej: documents/omi110)",
    )
    parser.add_argument(
        "--etapa", choices=("todo", "contenido", "assessment", "imagenes"), default="todo",
        help="Etapas a ejecutar (por defecto: blueprints e imágenes).",
    )
    args = parser.parse_args()

    try:
        contexto = ejecutar_cursomaker(args.curso, etapa=args.etapa)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Error: {error}\n")

    print(f"Generación completada: {contexto.config.nombre}")
    print(f"Shortname: {contexto.config.shortname}")
    print(f"Assets: {contexto.assets_dir}")
    print(f"Output: {contexto.output_dir}")
    if contexto.content_blueprint_path:
        print(f"Content Blueprint: {contexto.content_blueprint_path}")
    if contexto.assessment_blueprint_path:
        print(f"Assessment Blueprint: {contexto.assessment_blueprint_path}")
    if contexto.image_analysis_path:
        print(f"Análisis visual: {contexto.image_analysis_path}")
        print(f"Mapeo visual: {contexto.image_mapping_path}")
        print(f"Render Blueprint: {contexto.render_blueprint_path}")
        print(f"Mapeo de subsecciones: {contexto.subsection_mapping_path}")
    print("Ejecución Moodle pendiente de integración.")


if __name__ == "__main__":
    main()

import argparse

from services.orchestrator import ejecutar_cursomaker


def main():
    parser = argparse.ArgumentParser(description="CursoMaker Orchestrator")
    parser.add_argument(
        "curso",
        help="Directorio del curso (ej: documents/omi110)",
    )
    parser.add_argument(
        "--etapa", choices=("todo", "contenido", "assessment", "imagenes", "moodle"), default="todo",
        help="Etapas a ejecutar (por defecto: pipeline completo, incluida ejecución Moodle).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Valida los artefactos Moodle sin modificar el servidor.")
    args = parser.parse_args()

    try:
        contexto = ejecutar_cursomaker(args.curso, etapa=args.etapa, dry_run=args.dry_run)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Error: {error}\n")

    print(f"Proceso completado: {contexto.config.nombre}")
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
    if contexto.moodle_resultado:
        print(f"Moodle: {contexto.moodle_resultado['estado']}")
        if contexto.moodle_curso_id:
            print(f"Curso Moodle ID: {contexto.moodle_curso_id}")
            print(f"Resumen: {contexto.moodle_report_path}")
            print(f"Actividades pendientes: {contexto.moodle_resultado['assessment']['pendientes']}")


if __name__ == "__main__":
    main()

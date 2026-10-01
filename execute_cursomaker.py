from pathlib import Path
import argparse


def etapa(numero: int, total: int, titulo: str):
    print()
    print("=" * 70)
    print(f"ETAPA {numero}/{total}")
    print(titulo.upper())
    print("=" * 70)


def main():

    parser = argparse.ArgumentParser(
        description="CursoMaker Orchestrator"
    )

    parser.add_argument(
        "curso",
        help="Directorio del curso (ej: courses/omi110)"
    )

    args = parser.parse_args()

    curso_dir = Path(args.curso)

    if not curso_dir.exists():
        raise FileNotFoundError(curso_dir)

    TOTAL_ETAPAS = 9

    etapa(1, TOTAL_ETAPAS, "Carga de configuración")

    etapa(2, TOTAL_ETAPAS, "Generación Content Blueprint")

    etapa(3, TOTAL_ETAPAS, "Generación Assessment Blueprint")

    etapa(4, TOTAL_ETAPAS, "Análisis de imágenes")

    etapa(5, TOTAL_ETAPAS, "Mapeo de imágenes")

    etapa(6, TOTAL_ETAPAS, "Validaciones")

    etapa(7, TOTAL_ETAPAS, "Ejecución de contenido")

    etapa(8, TOTAL_ETAPAS, "Ejecución Assessment")

    etapa(9, TOTAL_ETAPAS, "Resumen final")


if __name__ == "__main__":
    main()
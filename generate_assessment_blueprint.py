import json
from pathlib import Path

from services.documents import (
    extraer_texto_pdf,
    construir_texto_documento,
)
from services.assessment_blueprint_generator import (
    generar_assessment_blueprint,
)


PDF_PATH = Path(
    "documents/Actividades de Plataforma OMI 1.41.docx.pdf"
)

OUTPUT_PATH = Path(
    "assessment_blueprint.json"
)


def main():
    print(f"📄 Documento: {PDF_PATH}")

    documento = extraer_texto_pdf(PDF_PATH)

    print(
        f"📚 Páginas detectadas: "
        f"{documento['total_paginas']}"
    )

    texto_documento = construir_texto_documento(
        documento
    )

    print(
        f"📝 Caracteres extraídos: "
        f"{len(texto_documento):,}"
    )

    blueprint = generar_assessment_blueprint(
        texto_documento
    )

    OUTPUT_PATH.write_text(
        blueprint.model_dump_json(indent=2),
        encoding="utf-8",
    )

    total_actividades = sum(
        len(modulo.actividades)
        for modulo in blueprint.modulos
    )

    print()
    print("✅ Assessment blueprint generado")
    print(f"Curso: {blueprint.curso}")
    print(f"Módulos: {len(blueprint.modulos)}")
    print(f"Actividades: {total_actividades}")
    print(f"Archivo: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
from pathlib import Path

from services.documents import (
    extraer_texto_pdf,
    construir_texto_documento,
)
from services.blueprint_generator import generar_blueprint


RUTA_PDF = "documents/MANUAL OMI 1.41.pdf"
RUTA_SALIDA = "blueprint.json"


print("📄 Extrayendo PDF...")

documento = extraer_texto_pdf(RUTA_PDF)

print(
    f"📚 Documento cargado: "
    f"{documento['total_paginas']} páginas"
)


print("🧱 Construyendo representación del documento...")

texto_documento = construir_texto_documento(documento)

print(
    f"📝 Texto preparado: "
    f"{len(texto_documento):,} caracteres"
)


blueprint = generar_blueprint(texto_documento)


print("💾 Guardando blueprint...")

Path(RUTA_SALIDA).write_text(
    blueprint.model_dump_json(indent=2),
    encoding="utf-8",
)


print()
print("✅ Blueprint generado correctamente.")
print(f"📁 Archivo: {RUTA_SALIDA}")
print(f"🎓 Curso: {blueprint.nombre}")
print(f"📚 Secciones: {len(blueprint.secciones)}")

for numero, seccion in enumerate(
    blueprint.secciones,
    start=1,
):
    print(
        f"   {numero}. {seccion.titulo} "
        f"({len(seccion.contenidos)} contenidos)"
    )
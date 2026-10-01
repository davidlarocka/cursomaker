from collections import Counter

from services.documents import (
    extraer_imagenes_pdf,
    deduplicar_imagenes,
    clasificar_imagenes,
)


RUTA_PDF = "documents/MANUAL OMI 1.41.pdf"
DIRECTORIO_SALIDA = "documents/assets/omi141"


print("🖼️ Extrayendo imágenes del PDF...")

imagenes = extraer_imagenes_pdf(
    RUTA_PDF,
    DIRECTORIO_SALIDA,
)

imagenes_unicas = deduplicar_imagenes(imagenes)

clasificacion = clasificar_imagenes(
    imagenes_unicas
)

candidatos = clasificacion["candidatos"]
decorativas = clasificacion["decorativas"]

por_pagina = Counter(
    imagen["pagina"]
    for imagen in imagenes
)

print()
print("=" * 60)
print("📊 IMÁGENES DETECTADAS")
print("=" * 60)

for pagina in sorted(por_pagina):
    print(
        f"🖼️ Página {pagina}: "
        f"{por_pagina[pagina]} imagen(es)"
    )

print()
print(f"🖼️ Total detectado: {len(imagenes)}")
print()
print("=" * 60)
print("📐 DETALLE DE IMÁGENES")
print("=" * 60)

for imagen in imagenes:
    print(
        f"Pág. {imagen['pagina']:>2} | "
        f"{imagen['archivo']} | "
        f"{imagen['ancho']}x{imagen['alto']}"
    )
print(f"📁 Directorio: {DIRECTORIO_SALIDA}")

print()
print("=" * 60)
print("🧬 DEDUPLICACIÓN")
print("=" * 60)

print(f"Imágenes extraídas: {len(imagenes)}")
print(f"Imágenes únicas:    {len(imagenes_unicas)}")
print(
    f"Duplicados:         "
    f"{len(imagenes) - len(imagenes_unicas)}"
)

print()
print("🔁 Imágenes repetidas:")

for imagen in imagenes_unicas:
    if imagen["ocurrencias"] > 1:
        print(
            f"{imagen['archivo']} | "
            f"{imagen['ancho']}x{imagen['alto']} | "
            f"{imagen['ocurrencias']} veces | "
            f"páginas {imagen['paginas']}"
        )
 
print()
print("=" * 60)
print("🎯 FILTRO TÉCNICO")
print("=" * 60)

print(
    f"🖼️ Imágenes únicas:     "
    f"{len(imagenes_unicas)}"
)

print(
    f"🎯 Candidatas:           "
    f"{len(candidatos)}"
)

print(
    f"🗑️ Decorativas:         "
    f"{len(decorativas)}"
)

print()
print("🎯 CANDIDATAS PARA ANÁLISIS:")

for imagen in candidatos:
    print(
        f"Pág. {imagen['paginas']} | "
        f"{imagen['archivo']} | "
        f"{imagen['ancho']}x{imagen['alto']}"
    )        
from services.documents import (
    extraer_texto_pdf,
    extraer_imagenes_pdf,
    deduplicar_imagenes,
    clasificar_imagenes,
)
from services.image_analyzer import analizar_imagen
from services.image_qa_store import (
    cargar_analisis_imagenes,
    guardar_analisis_imagenes,
)


RUTA_PDF = "documents/MANUAL OMI 1.41.pdf"
DIRECTORIO_IMAGENES = "documents/assets/omi141"
RUTA_CHECKPOINT = "image_analysis.json"

MAX_IMAGENES = None


print("📦 Cargando documento...")

documento = extraer_texto_pdf(
    RUTA_PDF
)

paginas = {
    pagina["numero"]: pagina["texto"]
    for pagina in documento["paginas"]
}


print("🖼️ Preparando inventario de imágenes...")

imagenes = extraer_imagenes_pdf(
    RUTA_PDF,
    DIRECTORIO_IMAGENES,
)

imagenes_unicas = deduplicar_imagenes(
    imagenes
)

clasificacion = clasificar_imagenes(
    imagenes_unicas
)

candidatos = clasificacion["candidatos"]


print(
    f"🎯 Candidatas encontradas: "
    f"{len(candidatos)}"
)


estado = cargar_analisis_imagenes(
    RUTA_CHECKPOINT
)

procesadas_ahora = 0


for imagen in candidatos:

    if (
    MAX_IMAGENES is not None
        and procesadas_ahora >= MAX_IMAGENES
    ):
        break

    nombre = imagen["archivo"]

    existente = estado["imagenes"].get(
        nombre
    )

    if (
        existente is not None
        and existente.get("estado") == "analizada"
    ):
        print(
            f"⏭️ {nombre} ya fue analizada. "
            f"Saltando..."
        )
        continue

    if (
        existente is not None
        and existente.get("estado") == "error"
    ):
        print(
            f"🔄 {nombre} tuvo un error anterior. "
            f"Reintentando..."
        )

    numero_pagina = imagen["paginas"][0]

    texto_pagina = paginas.get(
        numero_pagina,
        "",
    )

    print()
    print("-" * 60)
    print(
        f"🖼️ Procesando {nombre} "
        f"(página {numero_pagina})"
    )

    try:
        resultado = analizar_imagen(
            ruta_imagen=imagen["ruta"],
            numero_pagina=numero_pagina,
            texto_pagina=texto_pagina,
        )

        estado["imagenes"][nombre] = {
            "pagina": numero_pagina,
            "ruta": imagen["ruta"],
            "ancho": imagen["ancho"],
            "alto": imagen["alto"],
            "es_pedagogica": resultado.es_pedagogica,
            "tipo": resultado.tipo,
            "descripcion": resultado.descripcion,
            "relacion_con_texto": (
                resultado.relacion_con_texto
            ),
            "recomendacion": resultado.recomendacion,
            "estado": "analizada",
        }

    except Exception as error:

        estado["imagenes"][nombre] = {
            "pagina": numero_pagina,
            "ruta": imagen["ruta"],
            "estado": "error",
            "error": str(error),
        }

        print(
            f"💥 Error analizando {nombre}: "
            f"{error}"
        )

    guardar_analisis_imagenes(
        RUTA_CHECKPOINT,
        estado,
    )

    procesadas_ahora += 1


incluidas = sum(
    1
    for imagen in estado["imagenes"].values()
    if imagen.get("recomendacion") == "incluir"
)

descartadas = sum(
    1
    for imagen in estado["imagenes"].values()
    if imagen.get("recomendacion") == "descartar"
)

errores = sum(
    1
    for imagen in estado["imagenes"].values()
    if imagen.get("estado") == "error"
)


print()
print("=" * 60)
print("🏁 ANÁLISIS VISUAL FINALIZADO")
print("=" * 60)

print(
    f"🔎 Analizadas en checkpoint: "
    f"{len(estado['imagenes'])}"
)

print(
    f"✅ Incluir: "
    f"{incluidas}"
)

print(
    f"🗑️ Descartar: "
    f"{descartadas}"
)

print(
    f"💥 Errores: "
    f"{errores}"
)

print(
    f"📁 Checkpoint: "
    f"{RUTA_CHECKPOINT}"
)
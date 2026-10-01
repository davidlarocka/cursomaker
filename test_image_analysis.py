from services.documents import (
    extraer_texto_pdf,
)
from services.image_analyzer import (
    analizar_imagen,
)


RUTA_PDF = "documents/MANUAL OMI 1.41.pdf"

RUTA_IMAGEN = (
    "documents/assets/omi141/"
    "pagina_005_img_02.jpeg"
)

PAGINA = 5


documento = extraer_texto_pdf(
    RUTA_PDF
)

pagina = next(
    pagina
    for pagina in documento["paginas"]
    if pagina["numero"] == PAGINA
)

resultado = analizar_imagen(
    ruta_imagen=RUTA_IMAGEN,
    numero_pagina=PAGINA,
    texto_pagina=pagina["texto"],
)

print()
print("=" * 60)
print("👁️ ANÁLISIS VISUAL")
print("=" * 60)

print(
    f"Pedagógica:       "
    f"{resultado.es_pedagogica}"
)

print(
    f"Tipo:             "
    f"{resultado.tipo}"
)

print(
    f"Descripción:      "
    f"{resultado.descripcion}"
)

print(
    f"Relación texto:   "
    f"{resultado.relacion_con_texto}"
)

print(
    f"Recomendación:    "
    f"{resultado.recomendacion}"
)
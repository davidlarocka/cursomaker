from services.documents import (
    extraer_texto_pdf,
    obtener_texto_paginas,
)


RUTA_PDF = "documents/MANUAL OMI 1.41.pdf"

PAGINAS = [17, 18, 19]


documento = extraer_texto_pdf(
    RUTA_PDF
)


paginas = obtener_texto_paginas(
    documento,
    PAGINAS,
)


print(
    type(paginas)
)

print(
    paginas
)
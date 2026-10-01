from services.documents import extraer_texto_pdf


resultado = extraer_texto_pdf(
    "documents/MANUAL OMI 1.41.pdf"
)

texto_completo = "\n\n".join(
    pagina["texto"]
    for pagina in resultado["paginas"]
)

paginas_con_texto = sum(
    1
    for pagina in resultado["paginas"]
    if pagina["texto"].strip()
)

paginas_vacias = (
    resultado["total_paginas"] - paginas_con_texto
)

print(f"Archivo: {resultado['archivo']}")
print(f"Páginas totales: {resultado['total_paginas']}")
print(f"Páginas con texto: {paginas_con_texto}")
print(f"Páginas vacías: {paginas_vacias}")
print(f"Caracteres extraídos: {len(texto_completo):,}")
print(f"Palabras aproximadas: {len(texto_completo.split()):,}")
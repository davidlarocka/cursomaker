import json

from services.documents import (
    extraer_texto_pdf,
    obtener_texto_paginas,
)
from services.content_validator import validar_contenido


# 1. Leemos el PDF original.
documento = extraer_texto_pdf(
    "documents/MANUAL OMI 1.41.pdf"
)

# 2. Leemos el blueprint generado.
with open("blueprint.json", encoding="utf-8") as archivo:
    blueprint = json.load(archivo)

# Módulo I -> primer contenido.
contenido = blueprint["secciones"][1]["contenidos"][0]

print(f"📄 Contenido: {contenido['titulo']}")
print(f"📚 Páginas fuente: {contenido['paginas_fuente']}")

# 3. Recuperamos SOLAMENTE las páginas que el blueprint
#    declaró como fuente.
texto_fuente = obtener_texto_paginas(
    documento,
    contenido["paginas_fuente"]
)

# 4. Un segundo proceso de IA audita el contenido.
validacion = validar_contenido(
    titulo=contenido["titulo"],
    contenido=contenido["contenido"],
    texto_fuente=texto_fuente,
)

print()
print("=== RESULTADO DE VALIDACIÓN ===")
print(validacion.model_dump_json(indent=2))
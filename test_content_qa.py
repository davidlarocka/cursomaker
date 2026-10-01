import json

from services.documents import (
    extraer_texto_pdf,
    obtener_texto_paginas,
)
from services.content_qa import procesar_qa_contenido


# 1. Cargamos el PDF.
documento = extraer_texto_pdf(
    "documents/MANUAL OMI 1.41.pdf"
)

# 2. Cargamos el blueprint.
with open("blueprint.json", encoding="utf-8") as archivo:
    blueprint = json.load(archivo)

# 3. Seleccionamos la misma lección de prueba.
contenido = blueprint["secciones"][1]["contenidos"][0]

# 4. Recuperamos sus páginas fuente.
texto_fuente = obtener_texto_paginas(
    documento,
    contenido["paginas_fuente"],
)

# 5. Ejecutamos el ciclo completo de QA.
resultado = procesar_qa_contenido(
    titulo=contenido["titulo"],
    contenido=contenido["contenido"],
    texto_fuente=texto_fuente,
    max_intentos=2,
)

# 6. Mostramos el resultado.
print()
print("=" * 60)
print("📋 RESULTADO FINAL QA")
print("=" * 60)

print(f"Aprobado: {resultado['aprobado']}")
print(f"Correcciones realizadas: {resultado['correcciones']}")
print(
    f"Fidelidad: "
    f"{resultado['validacion'].fidelidad_fuente}%"
)
print(
    f"Cobertura: "
    f"{resultado['validacion'].cobertura_contenido}%"
)

if not resultado["aprobado"]:
    print()
    print("⚠️ REQUIERE REVISIÓN HUMANA")

    for omision in resultado[
        "validacion"
    ].omisiones_importantes:
        print(f"   - {omision}")
import json

from services.documents import (
    extraer_texto_pdf,
    obtener_texto_paginas,
)
from services.content_validator import validar_contenido
from services.content_corrector import corregir_contenido


# 1. Cargamos el documento original.
documento = extraer_texto_pdf(
    "documents/MANUAL OMI 1.41.pdf"
)

# 2. Cargamos el blueprint.
with open("blueprint.json", encoding="utf-8") as archivo:
    blueprint = json.load(archivo)

# Módulo I -> primer contenido.
contenido = blueprint["secciones"][1]["contenidos"][0]

titulo = contenido["titulo"]
html_original = contenido["contenido"]
paginas_fuente = contenido["paginas_fuente"]

# 3. Recuperamos exclusivamente las páginas declaradas.
texto_fuente = obtener_texto_paginas(
    documento,
    paginas_fuente,
)

# 4. Primera auditoría.
print("\n🔎 PRIMERA AUDITORÍA")

validacion_inicial = validar_contenido(
    titulo=titulo,
    contenido=html_original,
    texto_fuente=texto_fuente,
)

print(validacion_inicial.model_dump_json(indent=2))

# 5. Si ya está aprobado, no hacemos nada.
if validacion_inicial.aprobado:
    print("\n✅ El contenido ya estaba aprobado.")

else:
    # 6. Generamos una versión corregida.
    print("\n🛠️ GENERANDO CORRECCIÓN")

    html_corregido = corregir_contenido(
        titulo=titulo,
        contenido=html_original,
        texto_fuente=texto_fuente,
        validacion=validacion_inicial,
    )

    print("\n📄 CONTENIDO CORREGIDO")
    print(html_corregido)

    # 7. Auditamos nuevamente la versión corregida.
    print("\n🔎 SEGUNDA AUDITORÍA")

    validacion_final = validar_contenido(
        titulo=titulo,
        contenido=html_corregido,
        texto_fuente=texto_fuente,
    )

    print(validacion_final.model_dump_json(indent=2))

    # 8. Resultado final.
    print("\n=== RESULTADO ===")

    if validacion_final.aprobado:
        print("✅ La corrección superó el control de calidad.")
    else:
        print("⚠️ La corrección todavía requiere revisión.")
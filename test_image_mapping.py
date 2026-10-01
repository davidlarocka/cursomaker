import json

from models.blueprint import CursoBlueprint
from services.documents import extraer_texto_pdf
from services.image_mapper import resolver_destino_imagen


RUTA_PDF = "documents/MANUAL OMI 1.41.pdf"
RUTA_BLUEPRINT = "blueprint_final.json"
RUTA_ANALISIS = "image_analysis.json"

NOMBRE_IMAGEN = "pagina_007_img_02.jpeg"


with open(
    RUTA_BLUEPRINT,
    "r",
    encoding="utf-8",
) as archivo:
    blueprint = CursoBlueprint.model_validate(
        json.load(archivo)
    )


with open(
    RUTA_ANALISIS,
    "r",
    encoding="utf-8",
) as archivo:
    analisis = json.load(archivo)


datos_imagen = analisis["imagenes"][
    NOMBRE_IMAGEN
]

imagen = {
    "archivo": NOMBRE_IMAGEN,
    **datos_imagen,
}

pagina_imagen = imagen["pagina"]


destinos = []

for indice_seccion, seccion in enumerate(
    blueprint.secciones,
    start=1,
):
    for indice_contenido, contenido in enumerate(
        seccion.contenidos,
        start=1,
    ):
        if pagina_imagen in contenido.paginas_fuente:
            destinos.append({
                "seccion_numero": indice_seccion,
                "seccion": seccion.titulo,
                "contenido_numero": indice_contenido,
                "contenido": contenido.titulo,
            })


documento = extraer_texto_pdf(
    RUTA_PDF
)

pagina = next(
    item
    for item in documento["paginas"]
    if item["numero"] == pagina_imagen
)


print("🖼️ Imagen:")
print(imagen["archivo"])

print()
print("🎯 Destinos candidatos:")

for indice, destino in enumerate(destinos):
    print(
        f"[{indice}] "
        f"{destino['contenido']}"
    )


resultado = resolver_destino_imagen(
    imagen=imagen,
    texto_pagina=pagina["texto"],
    destinos=destinos,
)


destino_elegido = destinos[
    resultado.indice_destino
]


print()
print("=" * 60)
print("🧭 DESTINO RESUELTO")
print("=" * 60)

print(
    f"Imagen:       "
    f"{imagen['archivo']}"
)

print(
    f"Destino:      "
    f"{destino_elegido['contenido']}"
)

print(
    f"Justificación: "
    f"{resultado.justificacion}"
)
import json

from models.blueprint import CursoBlueprint
from services.documents import extraer_texto_pdf
from services.image_mapper import resolver_destino_imagen


RUTA_PDF = "documents/MANUAL OMI 1.41.pdf"
RUTA_BLUEPRINT = "blueprint_final.json"
RUTA_ANALISIS = "image_analysis.json"
RUTA_SALIDA = "image_mapping.json"


print("📦 Cargando datos...")


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


documento = extraer_texto_pdf(
    RUTA_PDF
)

textos_paginas = {
    pagina["numero"]: pagina["texto"]
    for pagina in documento["paginas"]
}


imagenes = [
    {
        "archivo": nombre,
        **datos,
    }
    for nombre, datos
    in analisis["imagenes"].items()
    if datos.get("recomendacion") == "incluir"
]


resultado_final = {
    "imagenes": {}
}


for numero, imagen in enumerate(
    imagenes,
    start=1,
):

    pagina = imagen["pagina"]

    destinos = []

    for indice_seccion, seccion in enumerate(
        blueprint.secciones,
        start=1,
    ):
        for indice_contenido, contenido in enumerate(
            seccion.contenidos,
            start=1,
        ):
            if pagina in contenido.paginas_fuente:
                destinos.append({
                    "seccion_numero": indice_seccion,
                    "seccion": seccion.titulo,
                    "contenido_numero": indice_contenido,
                    "contenido": contenido.titulo,
                })

    print()
    print(
        f"🖼️ [{numero}/{len(imagenes)}] "
        f"{imagen['archivo']}"
    )

    if len(destinos) == 0:
        raise RuntimeError(
            f"La imagen {imagen['archivo']} "
            f"no tiene destino."
        )

    if len(destinos) == 1:

        destino = destinos[0]

        metodo = "deterministico"
        justificacion = (
            "La página fuente corresponde "
            "a un único contenido."
        )

        print(
            f"   ✅ Destino único: "
            f"{destino['contenido']}"
        )

    else:

        print(
            f"   🧠 Resolviendo entre "
            f"{len(destinos)} destinos..."
        )

        resolucion = resolver_destino_imagen(
            imagen=imagen,
            texto_pagina=textos_paginas[pagina],
            destinos=destinos,
        )

        destino = destinos[
            resolucion.indice_destino
        ]

        metodo = "semantico"
        justificacion = (
            resolucion.justificacion
        )

        print(
            f"   🎯 Elegido: "
            f"{destino['contenido']}"
        )

    resultado_final["imagenes"][
        imagen["archivo"]
    ] = {
        "pagina": pagina,
        "ruta": imagen["ruta"],
        "ancho": imagen["ancho"],
        "alto": imagen["alto"],
        "tipo": imagen["tipo"],
        "descripcion": imagen["descripcion"],
        "seccion_numero": destino[
            "seccion_numero"
        ],
        "seccion": destino["seccion"],
        "contenido_numero": destino[
            "contenido_numero"
        ],
        "contenido": destino["contenido"],
        "metodo_asignacion": metodo,
        "justificacion": justificacion,
    }


with open(
    RUTA_SALIDA,
    "w",
    encoding="utf-8",
) as archivo:
    json.dump(
        resultado_final,
        archivo,
        ensure_ascii=False,
        indent=2,
    )


deterministicas = sum(
    1
    for imagen
    in resultado_final["imagenes"].values()
    if imagen["metodo_asignacion"]
    == "deterministico"
)

semanticas = sum(
    1
    for imagen
    in resultado_final["imagenes"].values()
    if imagen["metodo_asignacion"]
    == "semantico"
)


print()
print("=" * 60)
print("🏁 MAPEO VISUAL FINALIZADO")
print("=" * 60)

print(
    f"🖼️ Imágenes mapeadas: "
    f"{len(resultado_final['imagenes'])}"
)

print(
    f"⚙️ Determinísticas: "
    f"{deterministicas}"
)

print(
    f"🧠 Semánticas: "
    f"{semanticas}"
)

print(
    f"📁 Resultado: "
    f"{RUTA_SALIDA}"
)
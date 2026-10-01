import json

from models.blueprint import CursoBlueprint


RUTA_BLUEPRINT = "blueprint_final.json"
RUTA_IMAGENES = "image_analysis.json"


print("📦 Cargando blueprint e inventario visual...")


with open(
    RUTA_BLUEPRINT,
    "r",
    encoding="utf-8",
) as archivo:
    blueprint = CursoBlueprint.model_validate(
        json.load(archivo)
    )


with open(
    RUTA_IMAGENES,
    "r",
    encoding="utf-8",
) as archivo:
    analisis = json.load(archivo)


imagenes_incluidas = [
    {
        "archivo": nombre,
        **datos,
    }
    for nombre, datos
    in analisis["imagenes"].items()
    if datos.get("recomendacion") == "incluir"
]


resultados = []


for imagen in imagenes_incluidas:

    pagina_imagen = imagen["pagina"]

    coincidencias = []

    for indice_seccion, seccion in enumerate(
        blueprint.secciones,
        start=1,
    ):
        for indice_contenido, contenido in enumerate(
            seccion.contenidos,
            start=1,
        ):
            if pagina_imagen in contenido.paginas_fuente:

                coincidencias.append({
                    "seccion_numero": indice_seccion,
                    "seccion": seccion.titulo,
                    "contenido_numero": indice_contenido,
                    "contenido": contenido.titulo,
                })

    resultados.append({
        "archivo": imagen["archivo"],
        "pagina": pagina_imagen,
        "descripcion": imagen["descripcion"],
        "coincidencias": coincidencias,
    })


sin_destino = [
    item
    for item in resultados
    if len(item["coincidencias"]) == 0
]

destino_unico = [
    item
    for item in resultados
    if len(item["coincidencias"]) == 1
]

ambiguas = [
    item
    for item in resultados
    if len(item["coincidencias"]) > 1
]


print()
print("=" * 70)
print("🧭 MAPEO DE IMÁGENES")
print("=" * 70)

print(
    f"🖼️ Imágenes incluidas: "
    f"{len(resultados)}"
)

print(
    f"✅ Destino único:      "
    f"{len(destino_unico)}"
)

print(
    f"⚠️ Ambiguas:           "
    f"{len(ambiguas)}"
)

print(
    f"❓ Sin destino:        "
    f"{len(sin_destino)}"
)


if ambiguas:

    print()
    print("⚠️ IMÁGENES AMBIGUAS")

    for imagen in ambiguas:

        print()
        print(
            f"{imagen['archivo']} "
            f"(página {imagen['pagina']})"
        )

        for destino in imagen["coincidencias"]:
            print(
                f"   → {destino['seccion']} "
                f"/ {destino['contenido']}"
            )


if sin_destino:

    print()
    print("❓ IMÁGENES SIN DESTINO")

    for imagen in sin_destino:
        print(
            f"   {imagen['archivo']} "
            f"(página {imagen['pagina']})"
        )
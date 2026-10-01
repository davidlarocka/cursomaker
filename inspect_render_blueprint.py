import json

from models.render_blueprint import CursoRender


RUTA_RENDER = "blueprint_render.json"


with open(
    RUTA_RENDER,
    "r",
    encoding="utf-8",
) as archivo:
    render = CursoRender.model_validate(
        json.load(archivo)
    )


resultados = []


for numero_seccion, seccion in enumerate(
    render.secciones,
    start=1,
):
    for numero_contenido, contenido in enumerate(
        seccion.contenidos,
        start=1,
    ):

        imagenes = [
            bloque
            for bloque in contenido.bloques
            if bloque.tipo == "imagen"
        ]

        resultados.append({
            "seccion_numero": numero_seccion,
            "seccion": seccion.titulo,
            "contenido_numero": numero_contenido,
            "contenido": contenido.titulo,
            "imagenes": len(imagenes),
            "paginas": contenido.paginas_fuente,
        })


resultados.sort(
    key=lambda item: item["imagenes"],
    reverse=True,
)


print()
print("=" * 70)
print("🖼️ CONTENIDOS CON MÁS MATERIAL VISUAL")
print("=" * 70)


for item in resultados[:10]:

    print()

    print(
        f"📄 {item['contenido']}"
    )

    print(
        f"   Sección: "
        f"{item['seccion']}"
    )

    print(
        f"   Páginas PDF: "
        f"{item['paginas']}"
    )

    print(
        f"   Imágenes: "
        f"{item['imagenes']}"
    )
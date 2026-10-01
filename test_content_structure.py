import json

from models.render_blueprint import CursoRender
from services.content_structure import (
    detectar_estructura_lista,
)


RUTA_RENDER = "blueprint_render.json"

TITULO_PILOTO = (
    "Funciones y responsabilidades "
    "del personal en emergencias"
)


with open(
    RUTA_RENDER,
    "r",
    encoding="utf-8",
) as archivo:
    render = CursoRender.model_validate(
        json.load(archivo)
    )


piloto = None


for seccion in render.secciones:
    for contenido in seccion.contenidos:

        if contenido.titulo == TITULO_PILOTO:
            piloto = contenido
            break

    if piloto:
        break


if piloto is None:
    raise RuntimeError(
        "No se encontró el contenido piloto."
    )


bloque_html = next(
    bloque
    for bloque in piloto.bloques
    if bloque.tipo == "html"
)


estructura = detectar_estructura_lista(
    bloque_html.html
)


print()
print("=" * 70)
print("🧩 ESTRUCTURA INTERNA DETECTADA")
print("=" * 70)

print()
print("INTRODUCCIÓN:")
print(estructura.introduccion)

print()
print(
    f"SUBSECCIONES: "
    f"{len(estructura.subsecciones)}"
)


for numero, subseccion in enumerate(
    estructura.subsecciones,
    start=1,
):

    print()
    print(
        f"{numero}. "
        f"{subseccion.titulo}"
    )

    print(
        f"   {subseccion.contenido}"
    )
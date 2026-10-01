import json

from models.render_blueprint import CursoRender
from services.content_structure import (
    detectar_estructura_lista,
)
from services.image_section_mapper import (
    asignar_imagen_subseccion,
)


RUTA_RENDER = "blueprint_render.json"

TITULO_PILOTO = (
    "Funciones y responsabilidades "
    "del personal en emergencias"
)

IMAGEN_PRUEBA = "pagina_013_img_02.jpeg"


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


bloque_imagen = next(
    bloque
    for bloque in piloto.bloques
    if (
        bloque.tipo == "imagen"
        and bloque.imagen.archivo
        == IMAGEN_PRUEBA
    )
)


resultado = asignar_imagen_subseccion(
    imagen=bloque_imagen.imagen,
    subsecciones=estructura.subsecciones,
)


destino = estructura.subsecciones[
    resultado.indice_subseccion
]


print()
print("=" * 70)
print("🧠 ASIGNACIÓN INTERNA")
print("=" * 70)

print(
    f"🖼️ Imagen: "
    f"{bloque_imagen.imagen.archivo}"
)

print(
    f"👁️ Descripción: "
    f"{bloque_imagen.imagen.descripcion}"
)

print()

print(
    f"🎯 Subsección: "
    f"{destino.titulo}"
)

print(
    f"💡 Justificación: "
    f"{resultado.justificacion}"
)
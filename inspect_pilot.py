import json

from models.render_blueprint import CursoRender


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


print()
print("=" * 70)
print("🧪 CONTENIDO PILOTO")
print("=" * 70)

print(
    f"📄 Título: {piloto.titulo}"
)

print(
    f"📚 Páginas fuente: "
    f"{piloto.paginas_fuente}"
)


for numero, bloque in enumerate(
    piloto.bloques,
    start=1,
):

    print()
    print("-" * 70)

    print(
        f"Bloque {numero} | "
        f"tipo={bloque.tipo}"
    )

    if bloque.tipo == "html":

        print()
        print("HTML:")
        print(bloque.html)

    elif bloque.tipo == "imagen":

        imagen = bloque.imagen

        print(
            f"Archivo: {imagen.archivo}"
        )

        print(
            f"Página: {imagen.pagina_fuente}"
        )

        print(
            f"Descripción: "
            f"{imagen.descripcion}"
        )
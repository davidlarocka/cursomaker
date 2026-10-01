import json

from models.render_blueprint import CursoRender


RUTA_RENDER = "blueprint_render.json"

TITULO_BUSCADO = (
    "Plan de Emergencia de la Tripulación"
)


with open(
    RUTA_RENDER,
    "r",
    encoding="utf-8",
) as archivo:
    render = CursoRender.model_validate(
        json.load(archivo)
    )


for seccion in render.secciones:

    for contenido in seccion.contenidos:

        if (
            contenido.titulo
            != TITULO_BUSCADO
        ):
            continue

        print()
        print("=" * 70)
        print(
            f"📄 {contenido.titulo}"
        )
        print("=" * 70)

        print(
            "📑 Páginas fuente:",
            contenido.paginas_fuente,
        )

        print()

        for bloque in contenido.bloques:

            print(
                f"🧱 Bloque: {bloque.tipo}"
            )

            if bloque.html:
                print(
                    bloque.html
                )

        raise SystemExit


print(
    "❌ Contenido no encontrado."
)
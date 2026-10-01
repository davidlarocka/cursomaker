import json

from bs4 import BeautifulSoup

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


total = 0


print()
print("=" * 70)
print("📊 TABLAS HTML DEL CURSO")
print("=" * 70)


for seccion in render.secciones:

    for contenido in seccion.contenidos:

        bloque_html = next(
            (
                bloque
                for bloque in contenido.bloques
                if bloque.tipo == "html"
            ),
            None,
        )

        if bloque_html is None:
            continue

        soup = BeautifulSoup(
            bloque_html.html,
            "html.parser",
        )

        tablas = soup.find_all("table")

        if not tablas:
            continue

        print()
        print(
            f"📄 {contenido.titulo}"
        )

        print(
            f"   Sección: {seccion.titulo}"
        )

        print(
            f"   Tablas: {len(tablas)}"
        )

        for indice, tabla in enumerate(
            tablas,
            start=1,
        ):
            total += 1

            print()
            print(
                f"--- TABLA {indice} ---"
            )

            print(
                tabla.prettify()
            )


print()
print("=" * 70)
print(
    f"📊 TOTAL DE TABLAS: {total}"
)
print("=" * 70)
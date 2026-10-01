import json
from collections import Counter

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


print()
print("=" * 70)
print("🔬 PATRONES HTML DEL CURSO")
print("=" * 70)


totales = Counter()


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

        conteo = Counter(
            etiqueta.name
            for etiqueta in soup.find_all()
        )

        totales.update(conteo)

        h2 = len(soup.find_all("h2"))
        h3 = len(soup.find_all("h3"))
        h4 = len(soup.find_all("h4"))
        ol = len(soup.find_all("ol"))
        ul = len(soup.find_all("ul"))
        li = len(soup.find_all("li"))
        table = len(soup.find_all("table"))

        print()
        print(
            f"📄 {contenido.titulo}"
        )

        print(
            f"   h2={h2} | "
            f"h3={h3} | "
            f"h4={h4} | "
            f"ol={ol} | "
            f"ul={ul} | "
            f"li={li} | "
            f"table={table}"
        )


print()
print("=" * 70)
print("📊 TOTALES")
print("=" * 70)

for etiqueta in [
    "h2",
    "h3",
    "h4",
    "p",
    "ol",
    "ul",
    "li",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
]:
    print(
        f"{etiqueta:6} "
        f"{totales[etiqueta]}"
    )
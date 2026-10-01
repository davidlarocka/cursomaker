import json

from models.render_blueprint import CursoRender
from services.content_structure import (
    detectar_estructura_contenido,
)


RUTA_RENDER = "blueprint_render.json"


with open(
    RUTA_RENDER,
    "r",
    encoding="utf-8",
) as archivo:
    render = CursoRender.model_validate(
        json.load(archivo)
    )


estructurados = []
simples = []


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
            simples.append({
                "seccion": seccion.titulo,
                "contenido": contenido.titulo,
                "motivo": "sin bloque HTML",
            })
            continue

        deteccion = detectar_estructura_contenido(
            bloque_html.html
        )

        estructura = deteccion["estructura"]
        tipo = deteccion["tipo"]

        if estructura is None:

            simples.append({
                "seccion": seccion.titulo,
                "contenido": contenido.titulo,
                "motivo": (
                    "sin estructura de lista "
                    "desplegable"
                ),
            })

        else:

            estructurados.append({
                "tipo": tipo,
                "seccion": seccion.titulo,
                "contenido": contenido.titulo,
                "subsecciones": len(
                    estructura.subsecciones
                ),
            })


print()
print("=" * 70)
print("🧩 ANÁLISIS ESTRUCTURAL DEL CURSO")
print("=" * 70)

print(
    f"📄 Total contenidos: "
    f"{len(estructurados) + len(simples)}"
)

print(
    f"🪗 Con estructura desplegable: "
    f"{len(estructurados)}"
)

print(
    f"📃 Contenido simple: "
    f"{len(simples)}"
)


print()
print("=" * 70)
print("🪗 CANDIDATOS A ACORDEÓN")
print("=" * 70)


for item in estructurados:

    print()
    print(
        f"📄 {item['contenido']}"
    )

    print(
        f"   Sección: "
        f"{item['seccion']}"
    )

    print(
        f"   Tipo: "
        f"{item['tipo']}"
    )

    print(
        f"   Subsecciones: "
        f"{item['subsecciones']}"
    )


print()
print("=" * 70)
print("📃 CONTENIDOS SIMPLES")
print("=" * 70)


for item in simples:

    print(
        f"• {item['contenido']}"
    )
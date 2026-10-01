import json

from models.render_blueprint import CursoRender
from services.html_renderer import renderizar_contenido


RUTA_RENDER = "blueprint_render.json"
RUTA_MAPPING = "subsection_image_mapping.json"

OBJETIVOS = [
    "Funciones y responsabilidades del personal en emergencias",
    "Plan de Emergencia de la Tripulación",
]


with open(
    RUTA_RENDER,
    "r",
    encoding="utf-8",
) as archivo:
    curso = CursoRender.model_validate(
        json.load(archivo)
    )


with open(
    RUTA_MAPPING,
    "r",
    encoding="utf-8",
) as archivo:
    datos_mapping = json.load(archivo)


mapping = datos_mapping["asignaciones"]


encontrados = {}


for seccion in curso.secciones:
    for contenido in seccion.contenidos:
        if contenido.titulo in OBJETIVOS:
            encontrados[
                contenido.titulo
            ] = contenido


for titulo in OBJETIVOS:

    if titulo not in encontrados:
        raise RuntimeError(
            f"No encontrado: {titulo}"
        )

    contenido = encontrados[titulo]

    html = renderizar_contenido(
        contenido,
        mapping,
    )

    cantidad_toggles = html.count(
        'class="cm-toggle"'
    )

    cantidad_imagenes = html.count(
        'class="cm-figure"'
    )

    print()
    print("=" * 70)
    print(titulo)
    print("=" * 70)
    print(
        f"🧩 Toggles: {cantidad_toggles}"
    )
    print(
        f"🖼️ Imágenes: {cantidad_imagenes}"
    )

    if not html.strip():
        raise RuntimeError(
            "El renderer produjo HTML vacío."
        )


print()
print("✅ Renderer genérico funcionando.")
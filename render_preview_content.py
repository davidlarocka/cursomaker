import json
from pathlib import Path

from models.render_blueprint import CursoRender
from services.content_structure import (
    detectar_estructura_contenido,
)
from services.html_renderer import (
    renderizar_toggle,
)


RUTA_RENDER = "blueprint_render.json"
RUTA_MAPPING = "subsection_image_mapping.json"
RUTA_SALIDA = Path(
    "previews/plan_emergencia.html"
)

CONTENIDO_OBJETIVO = (
    "Plan de Emergencia de la Tripulación"
)


# ---------------------------------------------------------
# Cargar datos
# ---------------------------------------------------------

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
    mapping = json.load(archivo)


# ---------------------------------------------------------
# Buscar contenido
# ---------------------------------------------------------

contenido_objetivo = None

for seccion in curso.secciones:
    for contenido in seccion.contenidos:
        if contenido.titulo == CONTENIDO_OBJETIVO:
            contenido_objetivo = contenido
            break

    if contenido_objetivo:
        break


if contenido_objetivo is None:
    raise RuntimeError(
        f"No se encontró: {CONTENIDO_OBJETIVO}"
    )


# ---------------------------------------------------------
# Obtener HTML e imágenes
# ---------------------------------------------------------

bloque_html = next(
    (
        bloque
        for bloque in contenido_objetivo.bloques
        if bloque.tipo == "html"
    ),
    None,
)


if bloque_html is None:
    raise RuntimeError(
        "El contenido no tiene bloque HTML."
    )


imagenes = [
    bloque.imagen
    for bloque in contenido_objetivo.bloques
    if (
        bloque.tipo == "imagen"
        and bloque.imagen is not None
    )
]

for imagen in imagenes:
    imagen.ruta = "../" + imagen.ruta


# ---------------------------------------------------------
# Detectar estructura
# ---------------------------------------------------------

deteccion = detectar_estructura_contenido(
    bloque_html.html
)

estructura = deteccion["estructura"]


if estructura is None:
    raise RuntimeError(
        "No se detectó estructura desplegable."
    )


print(
    f"🧩 Estructura detectada: "
    f"{deteccion['tipo']}"
)

print(
    f"📚 Subsecciones: "
    f"{len(estructura.subsecciones)}"
)


# ---------------------------------------------------------
# Agrupar imágenes por subsección
# ---------------------------------------------------------

imagenes_por_subseccion = {
    indice: []
    for indice in range(
        len(estructura.subsecciones)
    )
}


for imagen in imagenes:

    asignacion = mapping[
        "asignaciones"
    ].get(imagen.archivo)

    if asignacion is None:
        raise RuntimeError(
            f"Imagen sin mapping interno: "
            f"{imagen.archivo}"
        )

    indice = asignacion[
        "indice_subseccion"
    ]

    imagenes_por_subseccion[
        indice
    ].append(imagen)


# ---------------------------------------------------------
# Renderizar toggles
# ---------------------------------------------------------

toggles = []

for indice, subseccion in enumerate(
    estructura.subsecciones
):

    toggle = renderizar_toggle(
        numero=indice + 1,
        titulo=subseccion.titulo,
        contenido_html=subseccion.contenido,
        imagenes=imagenes_por_subseccion[
            indice
        ],
        abierto=(indice == 0),
    )

    toggles.append(toggle)


html_toggles = "\n\n".join(toggles)


# ---------------------------------------------------------
# Documento de preview
# ---------------------------------------------------------

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>{contenido_objetivo.titulo}</title>

<style>

body {{
    font-family:
        Arial,
        Helvetica,
        sans-serif;

    max-width: 1000px;
    margin: 40px auto;
    padding: 0 20px;
    line-height: 1.65;
}}

.cm-intro {{
    margin-bottom: 28px;
}}

.cm-toggle {{
    border: 1px solid #ddd;
    border-radius: 10px;
    margin-bottom: 14px;
    overflow: hidden;
}}

.cm-toggle summary {{
    cursor: pointer;
    padding: 16px 18px;
    font-weight: 700;
}}

.cm-toggle-number {{
    display: inline-block;
    margin-right: 10px;
}}

.cm-toggle-body {{
    padding: 4px 20px 20px;
}}

.cm-figure {{
    margin: 24px auto;
    text-align: center;
}}

.cm-figure img {{
    display: block;
    width: 100%;
    max-width: 850px;
    height: auto;
    margin: 0 auto;
    border-radius: 8px;
}}

.cm-figure figcaption {{
    margin-top: 8px;
    font-size: 0.9rem;
    opacity: 0.75;
}}

.cm-table-wrapper {{
    width: 100%;
    overflow-x: auto;
    margin: 20px 0;
}}

.cm-table {{
    width: 100%;
    border-collapse: collapse;
}}

.cm-table th,
.cm-table td {{
    border: 1px solid #ccc;
    padding: 10px 12px;
    text-align: left;
    vertical-align: top;
}}

</style>
</head>

<body>

<h1>
    {contenido_objetivo.titulo}
</h1>

<div class="cm-intro">
    {estructura.introduccion}
</div>

{html_toggles}

</body>
</html>
"""


# ---------------------------------------------------------
# Guardar
# ---------------------------------------------------------

RUTA_SALIDA.parent.mkdir(
    parents=True,
    exist_ok=True,
)

RUTA_SALIDA.write_text(
    html,
    encoding="utf-8",
)


print(
    f"🖼️ Imágenes: {len(imagenes)}"
)

print(
    f"✅ Preview generado: {RUTA_SALIDA}"
)
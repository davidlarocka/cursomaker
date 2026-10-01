import html
import json
from pathlib import Path

from models.render_blueprint import CursoRender


RUTA_RENDER = "blueprint_render.json"
RUTA_SALIDA = "previews/pilot.html"

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
seccion_piloto = None


for seccion in render.secciones:
    for contenido in seccion.contenidos:
        if contenido.titulo == TITULO_PILOTO:
            piloto = contenido
            seccion_piloto = seccion
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


imagenes = [
    bloque.imagen
    for bloque in piloto.bloques
    if bloque.tipo == "imagen"
]


figuras = []


for numero, imagen in enumerate(
    imagenes,
    start=1,
):
    ruta_absoluta = Path(
        imagen.ruta
    ).resolve()

    figuras.append(
        f"""
        <figure class="cm-figure">
            <img
                src="{ruta_absoluta.as_uri()}"
                alt="{html.escape(imagen.alt)}"
                loading="lazy"
            >

            <figcaption>
                <strong>Figura {numero}.</strong>
                {html.escape(imagen.descripcion)}
            </figcaption>
        </figure>
        """
    )


galeria = "\n".join(figuras)


documento = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1"
>

<title>{html.escape(piloto.titulo)}</title>

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    background: #f5f7fa;
    color: #26364a;
    font-family:
        Arial,
        Helvetica,
        sans-serif;
    line-height: 1.6;
}}

.cm-page {{
    max-width: 1400px;
    margin: 40px auto;
    padding: 0 24px;
}}

.cm-module {{
    margin-bottom: 14px;
    padding: 10px 14px;
    background: #eaf0f7;
    border-radius: 8px;
    color: #24558a;
    font-size: 14px;
}}

.cm-title {{
    margin: 0 0 28px;
    color: #173b68;
    font-size: clamp(
        30px,
        4vw,
        48px
    );
    line-height: 1.1;
}}

.cm-layout {{
    display: grid;
    grid-template-columns:
        minmax(0, 1.1fr)
        minmax(320px, 0.9fr);
    gap: 40px;
    align-items: start;
}}

.cm-content {{
    background: white;
    padding: 30px;
    border-radius: 12px;
}}

.cm-content h2,
.cm-content h3 {{
    color: #173b68;
}}

.cm-content ol {{
    padding-left: 24px;
}}

.cm-content li {{
    margin-bottom: 16px;
}}

.cm-gallery {{
    display: grid;
    grid-template-columns:
        repeat(2, minmax(0, 1fr));
    gap: 18px;
}}

.cm-figure {{
    margin: 0;
    overflow: hidden;
    background: white;
    border-radius: 10px;
    box-shadow:
        0 3px 14px
        rgba(0, 0, 0, 0.08);
}}

.cm-figure img {{
    display: block;
    width: 100%;
    height: 230px;
    object-fit: contain;
    background: #eef2f6;
}}

.cm-figure figcaption {{
    padding: 12px 14px 15px;
    font-size: 13px;
    line-height: 1.45;
}}

@media (max-width: 1000px) {{

    .cm-layout {{
        grid-template-columns: 1fr;
    }}

}}

@media (max-width: 600px) {{

    .cm-page {{
        margin: 20px auto;
        padding: 0 14px;
    }}

    .cm-content {{
        padding: 20px;
    }}

    .cm-gallery {{
        grid-template-columns: 1fr;
    }}

    .cm-figure img {{
        height: auto;
    }}

}}

</style>
</head>

<body>

<main class="cm-page">

    <div class="cm-module">
        {html.escape(seccion_piloto.titulo)}
    </div>

    <h1 class="cm-title">
        {html.escape(piloto.titulo)}
    </h1>

    <div class="cm-layout">

        <article class="cm-content">
            {bloque_html.html}
        </article>

        <aside class="cm-gallery">
            {galeria}
        </aside>

    </div>

</main>

</body>
</html>
"""


Path(RUTA_SALIDA).write_text(
    documento,
    encoding="utf-8",
)


print()
print("🎨 PREVIEW GENERADO")
print(
    f"📄 {Path(RUTA_SALIDA).resolve()}"
)
print(
    f"🖼️ Imágenes: {len(imagenes)}"
)
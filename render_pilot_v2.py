import html
import json
from pathlib import Path

from models.render_blueprint import CursoRender
from services.content_structure import (
    detectar_estructura_lista,
)


RUTA_RENDER = "blueprint_render.json"
RUTA_SALIDA = "previews/pilot_v2.html"
RUTA_MAPEO_INTERNO = "pilot_image_mapping.json"

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

estructura = detectar_estructura_lista(
    bloque_html.html
)


with open(
    RUTA_MAPEO_INTERNO,
    "r",
    encoding="utf-8",
) as archivo:
    mapeo_interno = json.load(archivo)


imagenes = [
    bloque.imagen
    for bloque in piloto.bloques
    if bloque.tipo == "imagen"
]


acordeones = []


for indice, subseccion in enumerate(
    estructura.subsecciones
):

    imagenes_subseccion = []

    for imagen in imagenes:

        asignacion = mapeo_interno[
            "imagenes"
        ].get(imagen.archivo)

        if asignacion is None:
            continue

        if (
            asignacion["indice_subseccion"]
            == indice
        ):
            imagenes_subseccion.append(
                imagen
            )


    figuras = []

    for imagen in imagenes_subseccion:

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
                    {html.escape(
                        imagen.descripcion
                    )}
                </figcaption>
            </figure>
            """
        )


    galeria_subseccion = ""

    if figuras:
        galeria_subseccion = (
            '<div class="cm-toggle-gallery">'
            + "\n".join(figuras)
            + "</div>"
        )


    abierto = (
        " open"
        if indice == 0
        else ""
    )


    acordeones.append(
        f"""
        <details
            class="cm-toggle"
            {abierto}
        >
            <summary>
                <span class="cm-number">
                    {indice + 1}
                </span>

                <span class="cm-summary-title">
                    {html.escape(
                        subseccion.titulo
                    )}
                </span>
            </summary>

            <div class="cm-toggle-body">

                <div class="cm-toggle-text">
                    {subseccion.contenido}
                </div>

                {galeria_subseccion}

            </div>
        </details>
        """
    )


acordeones_html = "\n".join(
    acordeones
)

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

.cm-lesson {{
    display: grid;
    gap: 18px;
}}

.cm-introduction {{
    padding: 26px 30px;
    background: white;
    border-radius: 12px;
}}

.cm-introduction h2 {{
    margin-top: 0;
    color: #173b68;
}}

.cm-toggles {{
    display: grid;
    gap: 12px;
}}

.cm-toggle {{
    overflow: hidden;
    background: white;
    border: 1px solid #dfe7f0;
    border-radius: 12px;
}}

.cm-toggle[open] {{
    border-color: #8bbcf2;
}}

.cm-toggle summary {{
    display: flex;
    align-items: center;
    gap: 14px;

    padding: 16px 18px;

    color: #173b68;
    font-weight: 700;

    cursor: pointer;

    list-style: none;
}}

.cm-toggle summary::-webkit-details-marker {{
    display: none;
}}

.cm-toggle summary::after {{
    content: "⌄";

    margin-left: auto;

    font-size: 22px;
    line-height: 1;

    transition: transform 0.2s ease;
}}

.cm-toggle[open] summary::after {{
    transform: rotate(180deg);
}}

.cm-number {{
    display: inline-flex;
    align-items: center;
    justify-content: center;

    flex: 0 0 34px;

    width: 34px;
    height: 34px;

    border-radius: 50%;

    background: #173b68;
    color: white;
}}

.cm-summary-title {{
    font-size: 17px;
}}

.cm-toggle-body {{
    padding:
        0
        20px
        22px
        66px;
}}

.cm-toggle-text {{
    max-width: 900px;
}}

.cm-toggle-gallery {{
    display: grid;

    grid-template-columns:
        repeat(
            auto-fit,
            minmax(220px, 1fr)
        );

    gap: 16px;

    margin-top: 20px;
}}

.cm-toggle-gallery .cm-figure img {{
    height: 240px;
    object-fit: contain;
}}

.cm-toggle-gallery .cm-figure {{
    box-shadow: none;
    border: 1px solid #e3e9ef;
}}

.cm-toggle-gallery figcaption {{
    color: #526273;
}}

@media (max-width: 1000px) {{

    .cm-layout {{
        grid-template-columns: 1fr;
    }}

}}

@media (max-width: 600px) {{
    .cm-toggle-body {{
        padding:
            0
            16px
            18px;
    }}

    .cm-toggle summary {{
        align-items: flex-start;
    }}

    .cm-summary-title {{
        font-size: 15px;
    }}

    .cm-toggle-gallery {{
        grid-template-columns: 1fr;
    }}

    .cm-toggle-gallery .cm-figure img {{
        height: auto;
    }}

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

    <article class="cm-lesson">

        <section class="cm-introduction">
            {estructura.introduccion}
        </section>

        <section class="cm-toggles">
            {acordeones_html}
        </section>

    </article>

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
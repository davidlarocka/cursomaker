from html import escape

from services.content_structure import (
    detectar_estructura_contenido,
)
from services.html_enhancer import (
    mejorar_tablas,
)


def renderizar_imagen(
    imagen,
    modo="local",
):
    alt = escape(
        imagen.descripcion or "",
        quote=True,
    )

    descripcion = escape(
        imagen.descripcion or ""
    )

    if modo == "moodle":
        src = (
            "@@PLUGINFILE@@/"
            + imagen.archivo
        )
    else:
        src = imagen.ruta

    return f"""
<figure class="cm-figure">
    <img
        src="{escape(src, quote=True)}"
        alt="{alt}"
        loading="lazy"
    >
    <figcaption>
        {descripcion}
    </figcaption>
</figure>
""".strip()


def renderizar_toggle(
    numero,
    titulo,
    contenido_html,
    imagenes=None,
    abierto=False,
    modo="local",
):
    imagenes = imagenes or []

    atributo_abierto = (
        " open"
        if abierto
        else ""
    )

    galeria = ""

    if imagenes:
        html_imagenes = "\n".join(
            renderizar_imagen(
                imagen,
                modo=modo,
            )
            for imagen in imagenes
        )

        galeria = f"""
<div class="cm-gallery">
    {html_imagenes}
</div>
""".strip()

    return f"""
<details class="cm-toggle"{atributo_abierto}>
    <summary>
        <span class="cm-toggle-number">
            {numero}
        </span>
        <span class="cm-toggle-title">
            {escape(titulo)}
        </span>
    </summary>

    <div class="cm-toggle-body">
        <div class="cm-toggle-text">
            {contenido_html}
        </div>

        {galeria}
    </div>
</details>
""".strip()

def renderizar_contenido(
    contenido,
    mapping,
    modo="local",
):
    bloque_html = next(
        (
            bloque
            for bloque in contenido.bloques
            if bloque.tipo == "html"
        ),
        None,
    )

    if bloque_html is None:
        raise ValueError(
            f"Contenido sin HTML: {contenido.titulo}"
        )

    imagenes = [
        bloque.imagen
        for bloque in contenido.bloques
        if (
            bloque.tipo == "imagen"
            and bloque.imagen is not None
        )
    ]

    deteccion = detectar_estructura_contenido(
        bloque_html.html
    )

    estructura = deteccion["estructura"]

    # -----------------------------------------
    # Contenido simple
    # -----------------------------------------

    if estructura is None:
        html = mejorar_tablas(
            bloque_html.html
        )

        if imagenes:
            html_imagenes = "\n".join(
                renderizar_imagen(
                    imagen,
                    modo=modo,
                )
                for imagen in imagenes
            )

            html += f"""
<div class="cm-gallery">
    {html_imagenes}
</div>
"""

        return html.strip()

    # -----------------------------------------
    # Contenido estructurado
    # -----------------------------------------

    imagenes_por_subseccion = {
        indice: []
        for indice in range(
            len(estructura.subsecciones)
        )
    }

    for imagen in imagenes:
        asignacion = mapping.get(
            imagen.archivo
        )

        if asignacion is None:
            raise ValueError(
                f"Imagen sin mapping interno: "
                f"{imagen.archivo}"
            )

        indice = asignacion[
            "indice_subseccion"
        ]

        if indice not in imagenes_por_subseccion:
            raise ValueError(
                f"Índice inválido para "
                f"{imagen.archivo}: {indice}"
            )

        imagenes_por_subseccion[
            indice
        ].append(imagen)

    partes = []

    # Introducción anterior a los toggles.
    if estructura.introduccion.strip():
        introduccion = mejorar_tablas(
            estructura.introduccion
        )

        partes.append(
            f"""
<div class="cm-intro">
    {introduccion}
</div>
""".strip()
        )

    # Subsecciones.
    for indice, subseccion in enumerate(
        estructura.subsecciones
    ):
        contenido_html = mejorar_tablas(
            subseccion.contenido
        )

        partes.append(
            renderizar_toggle(
                numero=indice + 1,
                titulo=subseccion.titulo,
                contenido_html=contenido_html,
                imagenes=imagenes_por_subseccion[
                    indice
                ],
                abierto=(indice == 0),
                modo=modo,
            )
        )

    return "\n\n".join(partes)
from bs4 import BeautifulSoup

from models.render_blueprint import (
    EstructuraContenidoDetectada,
    SubseccionDetectada,
)

def capitalizar_inicio_html(contenido):
    """
    Convierte en mayúscula el primer carácter
    alfabético visible del contenido HTML.
    """

    caracteres = list(contenido)

    dentro_etiqueta = False

    for indice, caracter in enumerate(
        caracteres
    ):
        if caracter == "<":
            dentro_etiqueta = True
            continue

        if caracter == ">":
            dentro_etiqueta = False
            continue

        if (
            not dentro_etiqueta
            and caracter.isalpha()
        ):
            caracteres[indice] = (
                caracter.upper()
            )
            break

    return "".join(caracteres)

def detectar_estructura_lista(html_original):
    """
    Detecta una estructura basada en una lista ordenada
    cuyos elementos comienzan con <strong>.

    Ejemplo:

    <p>Introducción...</p>
    <ol>
        <li>
            <strong>Título:</strong>
            contenido...
        </li>
    </ol>
    """

    soup = BeautifulSoup(
        html_original,
        "html.parser",
    )

    lista = soup.find("ol")

    if lista is None:
        raise ValueError(
            "No se encontró una lista ordenada "
            "para convertir en subsecciones."
        )

    # Todo lo anterior a <ol> se considera
    # introducción de la página.
    introduccion_partes = []

    for elemento in list(lista.previous_siblings):
        if (
            getattr(elemento, "name", None)
            or str(elemento).strip()
        ):
            introduccion_partes.append(
                str(elemento)
            )

    introduccion_partes.reverse()

    introduccion = "".join(
        introduccion_partes
    ).strip()

    subsecciones = []

    for item in lista.find_all(
        "li",
        recursive=False,
    ):
        strong = item.find("strong")

        if strong is None:
            continue

        titulo = strong.get_text(
            " ",
            strip=True,
        )

        titulo = titulo.rstrip(":").strip()

        # Eliminamos el título del contenido para
        # evitar mostrarlo dos veces en el toggle.
        strong.extract()

        contenido = "".join(
            str(elemento)
            for elemento in item.contents
        ).strip()
        
        contenido = capitalizar_inicio_html(
            contenido
        )

        subsecciones.append(
            SubseccionDetectada(
                titulo=titulo,
                contenido=contenido,
            )
        )

    if not subsecciones:
        raise ValueError(
            "La lista existe, pero no se detectaron "
            "subsecciones válidas."
        )

    return EstructuraContenidoDetectada(
        introduccion=introduccion,
        subsecciones=subsecciones,
    )
    
def intentar_detectar_estructura_lista(
    html_original,
):
    """
    Intenta detectar una estructura pedagógica
    basada en una lista ordenada.

    Si el contenido no cumple el patrón esperado,
    devuelve None en lugar de lanzar un error.
    """

    try:
        estructura = detectar_estructura_lista(
            html_original
        )

    except ValueError:
        return None

    if len(estructura.subsecciones) < 2:
        return None

    return estructura

def detectar_estructura_encabezados(
    html_original,
):
    """
    Divide un contenido HTML utilizando los <h3>
    como límites de subsecciones.

    Todo lo anterior al primer <h3> se considera
    introducción.
    """

    soup = BeautifulSoup(
        html_original,
        "html.parser",
    )

    encabezados = soup.find_all("h3")

    if len(encabezados) < 2:
        return None

    primer_h3 = encabezados[0]

    introduccion_partes = []

    for elemento in list(
        primer_h3.previous_siblings
    ):
        if (
            getattr(elemento, "name", None)
            or str(elemento).strip()
        ):
            introduccion_partes.append(
                str(elemento)
            )

    introduccion_partes.reverse()

    introduccion = "".join(
        introduccion_partes
    ).strip()

    subsecciones = []

    for encabezado in encabezados:

        titulo = encabezado.get_text(
            " ",
            strip=True,
        )

        contenido_partes = []

        elemento = encabezado.next_sibling

        while elemento is not None:

            if (
                getattr(elemento, "name", None)
                == "h3"
            ):
                break

            if (
                getattr(elemento, "name", None)
                or str(elemento).strip()
            ):
                contenido_partes.append(
                    str(elemento)
                )

            elemento = elemento.next_sibling

        contenido = "".join(
            contenido_partes
        ).strip()

        contenido = capitalizar_inicio_html(
            contenido
        )

        subsecciones.append(
            SubseccionDetectada(
                titulo=titulo,
                contenido=contenido,
            )
        )

    if len(subsecciones) < 2:
        return None

    return EstructuraContenidoDetectada(
        introduccion=introduccion,
        subsecciones=subsecciones,
    )

def detectar_estructura_contenido(
    html_original,
):
    """
    Selecciona automáticamente el detector
    estructural más apropiado.

    Prioridad:
    1. Lista ordenada estructurada.
    2. Encabezados H3.
    3. Sin estructura desplegable.
    """

    estructura_lista = (
        intentar_detectar_estructura_lista(
            html_original
        )
    )

    if estructura_lista is not None:
        return {
            "tipo": "lista",
            "estructura": estructura_lista,
        }

    estructura_encabezados = (
        detectar_estructura_encabezados(
            html_original
        )
    )

    if estructura_encabezados is not None:
        return {
            "tipo": "encabezados",
            "estructura": estructura_encabezados,
        }

    return {
        "tipo": "simple",
        "estructura": None,
    }
    
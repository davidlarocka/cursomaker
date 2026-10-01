from bs4 import BeautifulSoup


def mejorar_tablas(html_original):
    soup = BeautifulSoup(
        html_original,
        "html.parser",
    )

    tablas = soup.find_all("table")

    for tabla in tablas:

        # Añadir clase a la tabla
        clases = tabla.get("class", [])

        if "cm-table" not in clases:
            clases.append("cm-table")

        tabla["class"] = clases

        # Evitar envolverla nuevamente
        padre = tabla.parent

        if (
            padre
            and padre.name == "div"
            and "cm-table-wrapper"
            in padre.get("class", [])
        ):
            continue

        contenedor = soup.new_tag("div")
        contenedor["class"] = [
            "cm-table-wrapper"
        ]

        tabla.wrap(contenedor)

    return str(soup)
from bs4 import BeautifulSoup

from services.html_enhancer import (
    mejorar_tablas,
)


html_original = """
<h3>Ejemplo</h3>

<table>
    <thead>
        <tr>
            <th>Emergencia</th>
            <th>Acción</th>
        </tr>
    </thead>

    <tbody>
        <tr>
            <td>Incendio</td>
            <td>Activar alarma</td>
        </tr>
    </tbody>
</table>
"""


resultado = mejorar_tablas(
    html_original
)


soup = BeautifulSoup(
    resultado,
    "html.parser",
)


tabla = soup.find(
    "table"
)

contenedor = tabla.parent


assert "cm-table" in tabla.get(
    "class",
    []
)

assert (
    contenedor.name
    == "div"
)

assert "cm-table-wrapper" in contenedor.get(
    "class",
    []
)

assert (
    tabla.find("td").get_text(
        strip=True
    )
    == "Incendio"
)


print(
    "✅ Transformación de tablas correcta."
)
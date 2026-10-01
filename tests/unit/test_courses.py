from unittest.mock import patch

from tools.courses import obtener_pagina


def test_obtener_pagina_encuentra_pagina_por_coursemodule_id():
    respuesta_moodle = {
        "pages": [
            {
                "id": 4,
                "coursemodule": 52,
                "course": 6,
                "section": 1,
                "name": "Bienvenida",
                "content": "<h2>Hola</h2>",
                "contentformat": 1,
                "visible": True,
            }
        ],
        "warnings": [],
    }

    with patch(
        "tools.courses._moodle_request",
        return_value=respuesta_moodle
    ):
        resultado = obtener_pagina(
            curso_id=6,
            coursemodule_id=52
        )

    assert resultado["encontrada"] is True
    assert resultado["coursemodule_id"] == 52
    assert resultado["nombre"] == "Bienvenida"
    assert resultado["contenido"] == "<h2>Hola</h2>"


def test_obtener_pagina_devuelve_no_encontrada():
    respuesta_moodle = {
        "pages": [
            {
                "id": 4,
                "coursemodule": 52,
                "course": 6,
                "section": 1,
                "name": "Bienvenida",
                "content": "<h2>Hola</h2>",
                "contentformat": 1,
                "visible": True,
            }
        ],
        "warnings": [],
    }

    with patch(
        "tools.courses._moodle_request",
        return_value=respuesta_moodle
    ):
        resultado = obtener_pagina(
            curso_id=6,
            coursemodule_id=999
        )

    assert resultado["encontrada"] is False
    assert resultado["curso_id"] == 6
    assert resultado["coursemodule_id"] == 999

def test_actualizar_pagina_rechaza_contenido_distinto_en_readback():
    import pytest
    from tools.courses import actualizar_pagina

    with patch("tools.courses._moodle_request", return_value={"coursemoduleid": 52, "courseid": 6}), patch(
        "tools.courses.obtener_pagina",
        return_value={"encontrada": True, "nombre": "Página", "contenido": "<p>Distinto</p>"},
    ):
        with pytest.raises(RuntimeError, match="contenido guardado"):
            actualizar_pagina(52, "Página", "<p>Esperado</p>")


def test_actualizar_pagina_rechaza_nombre_distinto_en_readback():
    import pytest
    from tools.courses import actualizar_pagina

    with patch("tools.courses._moodle_request", return_value={"coursemoduleid": 52, "courseid": 6}), patch(
        "tools.courses.obtener_pagina",
        return_value={"encontrada": True, "nombre": "Otro nombre", "contenido": "<p>Esperado</p>"},
    ):
        with pytest.raises(RuntimeError, match="nombre guardado"):
            actualizar_pagina(52, "Página", "<p>Esperado</p>")


def test_actualizar_pagina_normaliza_urls_pluginfile_en_readback():
    from tools.courses import actualizar_pagina

    with patch("tools.courses._moodle_request", return_value={"coursemoduleid": 52, "courseid": 6}), patch(
        "tools.courses.obtener_pagina", return_value={
            "encontrada": True, "nombre": "Página", "seccion_numero": 1, "visible": False,
            "contenido": '<img src="https://moodle.example/webservice/pluginfile.php/10/mod_page/content/1/imagen.png?token=prueba">',
        },
    ):
        resultado = actualizar_pagina(52, "Página", '<img src="@@PLUGINFILE@@/imagen.png">')
        assert resultado["verificada"] is True

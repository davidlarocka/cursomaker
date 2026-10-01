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
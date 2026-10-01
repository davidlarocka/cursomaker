import hashlib
from html import escape

from tools.courses import _moodle_request


def crear_categoria(nombre, parent=0, courseid=None, idnumber=None):
    """
    Crea una categoría de preguntas en Moodle.

    Si ya existe una categoría con el mismo nombre y parent,
    devuelve la existente.
    """

    params = {"name": nombre, "parent": parent}
    if courseid is not None:
        params = {"name": nombre, "courseid": courseid}
        if idnumber is not None:
            params["idnumber"] = idnumber
    return _moodle_request(
        "local_cursomaker_create_question_category",
        params,
    )


def crear_pregunta(categoryid, name, questiontext, answers):
    """
    Crea una pregunta multichoice en una categoría de Moodle.

    answers debe ser una lista de diccionarios:

    [
        {
            "text": "Respuesta correcta",
            "fraction": 1,
        },
        {
            "text": "Respuesta incorrecta",
            "fraction": 0,
        },
    ]
    """

    if not answers:
        raise ValueError("La pregunta debe tener al menos una respuesta.")

    for answer in answers:
        if "text" not in answer:
            raise ValueError("Cada respuesta debe tener 'text'.")

        if "fraction" not in answer:
            raise ValueError("Cada respuesta debe tener 'fraction'.")

    return _moodle_request(
        "local_cursomaker_create_question",
        {
            "categoryid": categoryid,
            "name": name,
            "questiontext": questiontext,
            "answers": answers,
        },
    )


def crear_pregunta_desde_modelo(categoryid, courseid, id_logico, pregunta):
    """Conversión compartida por quizzes y cargas al banco de preguntas."""
    firma = hashlib.sha256((id_logico + pregunta.model_dump_json()).encode()).hexdigest()[:16]
    resultado = crear_pregunta(
        categoryid, f"CM-{courseid}-{firma}",
        f"<p>{escape(pregunta.enunciado)}</p>",
        [{"text": escape(a.texto), "fraction": 1 if a.correcta else 0}
         for a in pregunta.alternativas],
    )
    if not isinstance(resultado, dict) or not resultado.get("questionid"):
        raise RuntimeError("Moodle no confirmó la creación de la pregunta.")
    return resultado

from tools.courses import _moodle_request


def crear_categoria(nombre, parent=0):
    """
    Crea una categoría de preguntas en Moodle.

    Si ya existe una categoría con el mismo nombre y parent,
    devuelve la existente.
    """

    return _moodle_request(
        "local_cursomaker_create_question_category",
        {
            "name": nombre,
            "parent": parent,
        },
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
from tools.courses import _moodle_request


def crear_quiz(courseid, sectionnum, name, intro=""):
    """
    Crea un cuestionario (Quiz) en una sección de Moodle.
    """

    return _moodle_request(
        "local_cursomaker_create_quiz",
        {
            "courseid": courseid,
            "sectionnum": sectionnum,
            "name": name,
            "intro": intro,
        },
    )


def agregar_pregunta(quizid, questionid, page=1, maxmark=1):
    """
    Agrega una pregunta existente a un Quiz.

    Devuelve el Slot ID real creado por Moodle.
    """

    return _moodle_request(
        "local_cursomaker_add_quiz_question",
        {
            "quizid": quizid,
            "questionid": questionid,
            "page": page,
            "maxmark": maxmark,
        },
    )
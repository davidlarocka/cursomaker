from pathlib import Path

from services.h5p_generator import (
    empaquetar_h5p,
    empaquetar_drag_question,
    empaquetar_fill_in_the_blanks,
)
from tools.h5p import crear_h5p
from tools.courses import _moodle_request


def ejecutar_h5p(
    actividad,
    courseid: int,
    section: int,
    output_dir: str = "output/h5p",
) -> dict:
    """
    Genera, sube y publica una actividad H5P en Moodle.

    Flujo:
        1. Genera el paquete .h5p.
        2. Lo sube al Content Bank.
        3. Crea la actividad H5P en la sección indicada.
    """

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    tipo = actividad.h5p_tipo

    # ---------------------------------------------------------
    # 1. Generar paquete H5P
    # ---------------------------------------------------------

    if tipo == "drag_and_drop":
        filename = "drag-question.h5p"
        ruta_h5p = output / filename

        empaquetar_drag_question(
            actividad,
            ruta_h5p,
        )

    elif tipo == "course_presentation":
        filename = "course-presentation.h5p"
        ruta_h5p = output / filename

        empaquetar_h5p(
            actividad,
            ruta_h5p,
        )

    elif tipo == "fill_in_the_blanks":
        filename = "fill-in-the-blanks.h5p"
        ruta_h5p = output / filename

        empaquetar_fill_in_the_blanks(
            actividad,
            ruta_h5p,
        )

    else:
        raise ValueError(
            f"Tipo H5P no soportado: {tipo}"
        )

    # ---------------------------------------------------------
    # 2. Subir al Content Bank
    # ---------------------------------------------------------

    contenido = crear_h5p(
        courseid=courseid,
        ruta_h5p=str(ruta_h5p),
    )

    contentid = contenido["contentid"]

    # ---------------------------------------------------------
    # 3. Crear actividad H5P en Moodle
    # ---------------------------------------------------------

    resultado = _moodle_request(
        "local_cursomaker_create_h5p_activity",
        {
            "courseid": courseid,
            "section": section,
            "contentid": contentid,
            "name": actividad.titulo,
        },
    )

    if not resultado.get("success"):
        raise RuntimeError(
            f"Moodle no pudo crear la actividad H5P: {resultado}"
        )

    # ---------------------------------------------------------
    # 4. Resultado consolidado
    # ---------------------------------------------------------

    return {
        "success": True,
        "tipo": tipo,
        "titulo": actividad.titulo,
        "courseid": courseid,
        "section": section,
        "contentid": contentid,
        "coursemodule": resultado["coursemodule"],
        "instance": resultado["instance"],
        "filename": resultado["filename"],
        "ruta_h5p": str(ruta_h5p),
    }
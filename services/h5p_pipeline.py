from pathlib import Path
from typing import Any, Dict

from services.h5p_generator import (
    empaquetar_h5p,
    empaquetar_drag_question,
    empaquetar_fill_in_the_blanks,
)
from tools.h5p import crear_h5p
from tools.courses import _moodle_request


def crear_actividad_h5p(
    actividad: Any,
    courseid: int,
    section: int,
    output_dir: str = "output/h5p",
) -> Dict[str, Any]:

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    tipo = (
        getattr(actividad, "h5p_tipo_ejecucion", None)
        or getattr(actividad, "h5p_tipo", None)
    )

    if not tipo:
        raise ValueError(
            f"La actividad '{actividad.titulo}' no tiene tipo H5P definido."
        )

    titulo = actividad.titulo.strip()
    
    # ---------------------------------------------------------
    # Validar recursos requeridos
    # ---------------------------------------------------------

    recursos_faltantes = []

    for recurso in getattr(actividad, "recursos", []):
        if recurso.requerido and not recurso.disponible:
            recursos_faltantes.append({
                "tipo": recurso.tipo,
                "descripcion": recurso.descripcion,
                "archivo": recurso.archivo,
            })

    if recursos_faltantes:
        return {
            "success": False,
            "estado": "pendiente",
            "razon": "recurso_requerido_no_disponible",
            "tipo": tipo,
            "titulo": titulo,
            "recursos_faltantes": recursos_faltantes,
        }

    # ---------------------------------------------------------
    # Generar paquete H5P
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
    elif tipo == "single_choice_set":
        filename = "single-choice-set.h5p"
        ruta_h5p = output / filename

        empaquetar_h5p(
            actividad,
            ruta_h5p,
        )

    else:
        raise ValueError(
            f"Tipo H5P no implementado todavía: {tipo}"
        )

    # ---------------------------------------------------------
    # Subir al Content Bank
    # ---------------------------------------------------------

    content_result = crear_h5p(
        courseid=courseid,
        ruta_h5p=str(ruta_h5p),
    )

    contentid = int(content_result["contentid"])

    # ---------------------------------------------------------
    # Crear actividad Moodle
    # ---------------------------------------------------------

    activity_result = _moodle_request(
        "local_cursomaker_create_h5p_activity",
        {
            "courseid": courseid,
            "section": section,
            "contentid": contentid,
            "name": titulo,
        },
    )

    if activity_result.get("success") is False or not activity_result.get("coursemodule"):
        raise RuntimeError("Moodle no confirmó la creación de la actividad H5P.")
    if activity_result.get("courseid", courseid) != courseid:
        raise RuntimeError("Moodle creó la actividad H5P en otro curso.")

    return {
        "success": True,
        "tipo": tipo,
        "titulo": titulo,
        "courseid": courseid,
        "section": section,
        "contentid": contentid,
        "coursemodule": activity_result["coursemodule"],
        "instance": activity_result["instance"],
        "filename": activity_result["filename"],
        "h5p_path": str(ruta_h5p),
    }

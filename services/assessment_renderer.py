from html import escape


from models.assessment_blueprint import (
    ActividadDesarrollo,
    ActividadDiscusion,
)


def renderizar_actividad_desarrollo(
    actividad: ActividadDesarrollo,
) -> str:
    partes = []

    if actividad.descripcion:
        partes.append(f'<p>{escape(actividad.descripcion.strip())}</p>')

    if actividad.escenario.strip():
        partes.append(
            '<div class="cm-assessment-scenario">'
            '<h4>Situación planteada</h4>'
            f'<p>{escape(actividad.escenario.strip())}</p>'
            '</div>'
        )

    if actividad.instrucciones and actividad.instrucciones.strip():
        partes.append(
            '<div class="cm-assessment-instructions">'
            '<h4>Instrucciones</h4>'
            f'<p>{escape(actividad.instrucciones.strip())}</p>'
            '</div>'
        )

    if actividad.preguntas:
        preguntas = []

        for pregunta in actividad.preguntas:
            preguntas.append(
                '<li>'
                f'{escape(pregunta.enunciado.strip())}'
                '</li>'
            )

        partes.append(
            '<div class="cm-assessment-questions">'
            '<h4>Preguntas</h4>'
            '<ol>'
            + ''.join(preguntas)
            + '</ol>'
            '</div>'
        )

    if not partes:
        raise ValueError(
            f"La actividad {actividad.id_logico} no contiene "
            "información suficiente para renderizarse."
        )

    return (
        '<div class="cm-assessment cm-assessment-development">'
        + ''.join(partes)
        + '</div>'
    )
    
def renderizar_actividad_discusion(
    actividad: ActividadDiscusion,
) -> str:
    partes = []

    if actividad.descripcion:
        partes.append(f'<p>{escape(actividad.descripcion.strip())}</p>')

    if actividad.caso.strip():
        partes.append(
            '<div class="cm-assessment-case">'
            '<h4>Caso de análisis</h4>'
            f'<p>{escape(actividad.caso.strip())}</p>'
            '</div>'
        )

    if actividad.pregunta_debate.strip():
        partes.append(
            '<div class="cm-assessment-debate">'
            '<h4>Pregunta para la discusión</h4>'
            f'<p>{escape(actividad.pregunta_debate.strip())}</p>'
            '</div>'
        )

    if actividad.instrucciones and actividad.instrucciones.strip():
        partes.append(
            '<div class="cm-assessment-instructions">'
            '<h4>Instrucciones</h4>'
            f'<p>{escape(actividad.instrucciones.strip())}</p>'
            '</div>'
        )

    if not partes:
        raise ValueError(
            f"La actividad {actividad.id_logico} no contiene "
            "información suficiente para renderizarse."
        )

    return (
        '<div class="cm-assessment cm-assessment-discussion">'
        + ''.join(partes)
        + '</div>'
    )
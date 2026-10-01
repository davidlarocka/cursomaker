from models.assessment_blueprint import AssessmentBlueprint


def validar_assessment_blueprint(
    blueprint: AssessmentBlueprint,
):
    """
    Ejecuta validaciones deterministas sobre un
    AssessmentBlueprint ya generado.
    """

    errores = []
    advertencias = []

    if not blueprint.modulos:
        errores.append(
            "El blueprint no contiene módulos."
        )

    numeros_modulo = [
        modulo.numero
        for modulo in blueprint.modulos
    ]

    if len(numeros_modulo) != len(set(numeros_modulo)):
        errores.append(
            "Existen números de módulo duplicados."
        )

    ids_logicos = []

    for modulo in blueprint.modulos:
        if not modulo.actividades:
            errores.append(
                f"El módulo {modulo.numero} "
                "no contiene actividades."
            )

        tipos = [
            actividad.tipo
            for actividad in modulo.actividades
        ]

        for tipo_esperado in (
            "desarrollo",
            "discusion",
            "h5p",
            "quiz",
        ):
            cantidad = tipos.count(tipo_esperado)

            if cantidad != 1:
                errores.append(
                    f"El módulo {modulo.numero} debe contener "
                    f"exactamente una actividad de tipo "
                    f"'{tipo_esperado}', pero contiene {cantidad}."
                )

        if modulo.retroalimentacion_final is None:
            advertencias.append(
                f"El módulo {modulo.numero} no contiene "
                "retroalimentación final."
            )

        for actividad in modulo.actividades:
            ids_logicos.append(
                actividad.id_logico
            )

            if actividad.modulo != modulo.numero:
                errores.append(
                    f"La actividad '{actividad.titulo}' declara "
                    f"módulo {actividad.modulo}, pero está dentro "
                    f"del módulo {modulo.numero}."
                )

            if not actividad.paginas_fuente:
                advertencias.append(
                    f"La actividad '{actividad.titulo}' "
                    "no tiene páginas fuente."
                )

            if actividad.tipo == "quiz":
                if not actividad.preguntas:
                    errores.append(
                        f"El quiz '{actividad.titulo}' "
                        "no contiene preguntas."
                    )

            if actividad.tipo == "h5p":
                if actividad.estado == "requiere_recurso":
                    advertencias.append(
                        f"La actividad H5P '{actividad.titulo}' "
                        "requiere intervención humana."
                    )

    if len(ids_logicos) != len(set(ids_logicos)):
        errores.append(
            "Existen id_logico duplicados entre actividades."
        )

    return {
        "valido": len(errores) == 0,
        "errores": errores,
        "advertencias": advertencias,
        "modulos": len(blueprint.modulos),
        "actividades": sum(
            len(modulo.actividades)
            for modulo in blueprint.modulos
        ),
    }
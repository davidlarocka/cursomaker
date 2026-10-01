from typing import Any, Dict

from models.assessment_blueprint import AssessmentBlueprint
from services.h5p_pipeline import crear_actividad_h5p
from tools.courses import obtener_secciones


def ejecutar_assessment(
    blueprint: AssessmentBlueprint,
    courseid: int,
) -> Dict[str, Any]:
    """
    Ejecuta las actividades de un AssessmentBlueprint en Moodle.

    Actualmente:
    - H5P -> implementado
    - desarrollo -> pendiente
    - discusion -> pendiente
    - quiz -> pendiente

    El blueprint es la fuente de verdad.
    """

    print(f"🔧 Preparando ejecución del AssessmentBlueprint en curso {courseid}...")

    # Obtener las secciones reales de Moodle.
    secciones = obtener_secciones(courseid)

    secciones_por_numero = {
        int(seccion["numero"]): seccion
        for seccion in secciones
    }

    resultados = []

    for modulo in blueprint.modulos:

        # Los módulos empiezan en 1 y en este curso corresponden
        # a las secciones Moodle 2, 3, 4 y 5.
        section_number = modulo.numero + 1

        if section_number not in secciones_por_numero:
            raise RuntimeError(
                f"No existe la sección Moodle {section_number} "
                f"para el módulo {modulo.numero}."
            )

        seccion = secciones_por_numero[section_number]

        print(
            f"\n📚 Módulo {modulo.numero}: {modulo.titulo}"
        )
        print(
            f"   Moodle → sección {section_number} "
            f"(ID {seccion['id']}) → {seccion['nombre']}"
        )

        for actividad in modulo.actividades:

            print(
                f"   └─ {actividad.tipo}: {actividad.titulo}"
            )

            if actividad.tipo != "h5p":
                resultados.append({
                    "success": False,
                    "estado": "no_implementado",
                    "modulo": modulo.numero,
                    "modulo_titulo": modulo.titulo,
                    "section": section_number,
                    "sectionid": seccion["id"],
                    "actividad": actividad.titulo,
                    "tipo": actividad.tipo,
                })
                continue

            resultado = crear_actividad_h5p(
                actividad=actividad,
                courseid=courseid,
                section=section_number,
            )

            resultado = crear_actividad_h5p(
                actividad=actividad,
                courseid=courseid,
                section=section_number,
            )

            if resultado.get("estado") == "pendiente":
                print(
                    f"      ⚠ H5P pendiente: "
                    f"{resultado.get('razon')}"
                )

                resultados.append({
                    "success": False,
                    "estado": "pendiente",
                    "modulo": modulo.numero,
                    "modulo_titulo": modulo.titulo,
                    "section": section_number,
                    "sectionid": seccion["id"],
                    "actividad": actividad.titulo,
                    "tipo": actividad.tipo,
                    "resultado": resultado,
                })

                continue

            resultados.append({
                "success": True,
                "estado": "creado",
                "modulo": modulo.numero,
                "modulo_titulo": modulo.titulo,
                "section": section_number,
                "sectionid": seccion["id"],
                "actividad": actividad.titulo,
                "tipo": actividad.tipo,
                "resultado": resultado,
            })

    creadas = [
        r for r in resultados
        if r.get("estado") == "creado"
    ]

    pendientes = [
        r for r in resultados
        if r.get("estado") == "pendiente"
    ]

    no_implementadas = [
        r for r in resultados
        if r.get("estado") == "no_implementado"
    ]

    print()
    print("=" * 60)
    print("=== RESUMEN ASSESSMENT ===")
    print(f"Actividades procesadas: {len(resultados)}")
    print(f"H5P creadas:            {len(creadas)}")
    print(f"Pendientes:              {len(pendientes)}")
    print(f"No implementadas:        {len(no_implementadas)}")
    print("=" * 60)

    return {
        "success": True,
        "courseid": courseid,
        "actividades_procesadas": len(resultados),
        "creadas": len(creadas),
        "pendientes": len(pendientes),
        "no_implementadas": len(no_implementadas),
        "resultados": resultados,
    }

from pathlib import Path

from models.assessment_blueprint import AssessmentBlueprint
from models.assessment_qa import AssessmentQA
from services.assessment_qa import revisar_actividad
from services.documents import (
    extraer_texto_pdf,
    obtener_texto_paginas,
)


PDF_PATH = Path(
    "documents/Actividades de Plataforma OMI 1.41.docx.pdf"
)

BLUEPRINT_PATH = Path(
    "assessment_blueprint.json"
)

OUTPUT_PATH = Path(
    "assessment_qa.json"
)

CHECKPOINT_PATH = Path(
    "assessment_qa_checkpoint.json"
)

def main():
    blueprint = AssessmentBlueprint.model_validate_json(
        BLUEPRINT_PATH.read_text(
            encoding="utf-8"
        )
    )

    documento = extraer_texto_pdf(
        PDF_PATH
    )

    checkpoint = cargar_checkpoint()

    resultados = list(
        checkpoint.resultados
    )

    ids_revisados = {
        resultado.id_logico
        for resultado in resultados
    }

    total = sum(
        len(modulo.actividades)
        for modulo in blueprint.modulos
    )

    print(
        f"🔎 Actividades a revisar: {total}"
    )
    print()

    for modulo in blueprint.modulos:
        print(
            f"📚 Módulo {modulo.numero}: "
            f"{modulo.titulo}"
        )

        for actividad in modulo.actividades:
            if actividad.id_logico in ids_revisados:
                print(
                    f"  ⏭️ {actividad.id_logico}: "
                    "ya revisada"
                )
                continue
            if not actividad.paginas_fuente:
                raise RuntimeError(
                    f"La actividad "
                    f"'{actividad.id_logico}' "
                    "no tiene páginas fuente."
                )

            texto_fuente = obtener_texto_paginas(
                documento,
                actividad.paginas_fuente,
            )

            resultado = revisar_actividad(
                actividad,
                texto_fuente,
            )

            resultados.append(
                resultado
            )
            guardar_checkpoint(
                resultados
            )

            ids_revisados.add(
                actividad.id_logico
            )

            simbolo = {
                "aprobado": "✅",
                "requiere_correccion": "❌",
                "requiere_revision_humana": "⚠️",
            }[resultado.estado]

            print(
                f"  {simbolo} "
                f"{actividad.id_logico}: "
                f"{resultado.estado}"
            )

        print()

    qa = AssessmentQA(
        resultados=resultados
    )

    OUTPUT_PATH.write_text(
        qa.model_dump_json(indent=2),
        encoding="utf-8",
    )

    aprobados = sum(
        r.estado == "aprobado"
        for r in resultados
    )

    correcciones = sum(
        r.estado == "requiere_correccion"
        for r in resultados
    )

    revision_humana = sum(
        r.estado == "requiere_revision_humana"
        for r in resultados
    )

    hallazgos = sum(
        len(r.hallazgos)
        for r in resultados
    )

    print("=" * 70)
    print("📊 RESULTADO QA")
    print("=" * 70)
    print(f"Total: {len(resultados)}")
    print(f"✅ Aprobadas: {aprobados}")
    print(
        f"❌ Requieren corrección: "
        f"{correcciones}"
    )
    print(
        f"⚠️ Revisión humana: "
        f"{revision_humana}"
    )
    print(f"🔎 Hallazgos: {hallazgos}")
    print(f"💾 Archivo: {OUTPUT_PATH}")


def cargar_checkpoint():
    if not CHECKPOINT_PATH.exists():
        return AssessmentQA()

    return AssessmentQA.model_validate_json(
        CHECKPOINT_PATH.read_text(
            encoding="utf-8"
        )
    )


def guardar_checkpoint(resultados):
    qa = AssessmentQA(
        resultados=resultados
    )

    CHECKPOINT_PATH.write_text(
        qa.model_dump_json(indent=2),
        encoding="utf-8",
    )

if __name__ == "__main__":
    main()
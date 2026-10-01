import json

import fitz
import pytest

from models.blueprint import CursoBlueprint
from models.assessment_blueprint import AssessmentBlueprint
from services import orchestrator, image_pipeline, moodle_pipeline, assessment_executor
from tools import courses


@pytest.fixture
def proyecto(tmp_path, monkeypatch):
    monkeypatch.setattr(orchestrator, "PROYECTO_DIR", tmp_path)
    directorio = tmp_path / "documents" / "omi110"
    directorio.mkdir(parents=True)
    (directorio / "config.json").write_text(json.dumps({"nombre": "Curso oficial", "shortname": "omi110"}))
    for nombre in ("manual.pdf", "actividades.pdf"):
        with fitz.open() as pdf:
            pdf.new_page().insert_text((72, 72), "Texto fuente")
            pdf.save(directorio / nombre)
    contexto = orchestrator.preparar_curso(directorio)
    blueprint = CursoBlueprint.model_validate({
        "nombre": "Curso oficial", "shortname": "omi110", "descripcion": "Curso", "objetivos": [],
        "secciones": [{"titulo": "Módulo 1", "contenidos": [{
            "tipo": "pagina", "titulo": "Contenido", "contenido": "<p>Texto fuente</p>", "paginas_fuente": [1],
        }]}],
    })
    (contexto.output_dir / "blueprint.json").write_text(blueprint.model_dump_json())
    actividades = [
        {"tipo": "desarrollo", "id_logico": "desarrollo1", "modulo": 1, "titulo": "Tarea", "escenario": "Caso"},
        {"tipo": "discusion", "id_logico": "discusion1", "modulo": 1, "titulo": "Foro", "caso": "Caso", "pregunta_debate": "Debata"},
        {"tipo": "quiz", "id_logico": "quiz1", "modulo": 1, "titulo": "Test", "preguntas": [{
            "numero": 1, "enunciado": "Pregunta", "alternativas": [
                {"texto": "Correcta", "correcta": True}, {"texto": "Incorrecta", "correcta": False},
            ],
        }]},
        {"tipo": "h5p", "h5p_tipo": "drag_and_drop", "id_logico": "h5p1", "modulo": 1, "titulo": "H5P",
         "parejas": [{"concepto": "A", "definicion": "Uno"}, {"concepto": "B", "definicion": "Dos"}]},
    ]
    assessment = AssessmentBlueprint.model_validate({"curso": "Curso oficial", "documento_fuente": "actividades.pdf",
                                                     "modulos": [{"numero": 1, "titulo": "Módulo 1", "actividades": actividades}]})
    (contexto.output_dir / "assessment_blueprint.json").write_text(assessment.model_dump_json())
    image_pipeline.ejecutar_pipeline_imagenes(contexto)
    return contexto


@pytest.fixture
def moodle(monkeypatch):
    estado = {"cursos": [], "secciones": [], "contenido": {}, "operaciones": [], "siguiente": 10}
    monkeypatch.setattr(courses, "MOODLE_URL", "https://moodle.example.test")
    monkeypatch.setattr(courses, "MOODLE_TOKEN", "token-de-prueba")
    monkeypatch.setattr(courses, "listar_cursos", lambda: estado["cursos"])
    monkeypatch.setattr(courses, "obtener_secciones", lambda courseid: estado["secciones"])
    def crear_curso(nombre, shortname, categoria_id):
        estado["operaciones"].append("curso")
        curso = {"id": 7, "nombre": nombre, "shortname": shortname, "visible": False}
        estado["cursos"].append(curso)
        return curso
    def crear_seccion(courseid, nombre):
        estado["operaciones"].append("seccion")
        seccion = {"id": len(estado["secciones"]) + 1, "numero": len(estado["secciones"]) + 1,
                   "nombre": nombre, "actividades": []}
        estado["secciones"].append(seccion)
        return seccion
    def actividad(tipo, courseid, section, nombre, html=""):
        estado["operaciones"].append(tipo)
        cmid = estado["siguiente"]
        estado["siguiente"] += 1
        destino = next(s for s in estado["secciones"] if s["numero"] == section)
        destino["actividades"].append({"id": cmid, "tipo": tipo, "nombre": nombre})
        estado["contenido"][cmid] = html
        return {"coursemoduleid": cmid, "coursemodule_id": cmid, "instanceid": cmid + 100, "created": True}
    def actualizar(cmid, nombre, html):
        estado["operaciones"].append("actualizar_pagina")
        estado["contenido"][cmid] = html
        return {"verificada": True}
    def obtener(courseid, cmid):
        item = next(a for s in estado["secciones"] for a in s["actividades"] if a["id"] == cmid)
        return {"encontrada": True, "nombre": item["nombre"], "contenido": estado["contenido"][cmid]}
    def h5p(actividad_h5p, courseid, section, output_dir):
        resultado = actividad("h5pactivity", courseid, section, actividad_h5p.titulo)
        return {"success": True, "coursemodule": resultado["coursemoduleid"], "instance": resultado["instanceid"]}
    def categoria(*args, **kwargs):
        estado["operaciones"].append("categoria")
        assert kwargs["courseid"] == 7
        return {"categoryid": 20}
    def pregunta(*args):
        estado["operaciones"].append("pregunta")
        assert args[-1] == [{"text": "Correcta", "fraction": 1}, {"text": "Incorrecta", "fraction": 0}]
        return {"questionid": 30}
    def slot(*args, **kwargs):
        estado["operaciones"].append("slot")
        return {"slotid": 40}
    monkeypatch.setattr(courses, "crear_curso", crear_curso)
    monkeypatch.setattr(courses, "crear_seccion", crear_seccion)
    monkeypatch.setattr(courses, "crear_pagina", lambda *args: actividad("page", *args))
    monkeypatch.setattr(courses, "crear_assignment", lambda *args: actividad("assign", *args))
    monkeypatch.setattr(courses, "crear_foro", lambda *args: actividad("forum", *args))
    monkeypatch.setattr(courses, "crear_quiz", lambda *args: actividad("quiz", *args))
    monkeypatch.setattr(courses, "actualizar_pagina", actualizar)
    monkeypatch.setattr(courses, "obtener_pagina", obtener)
    monkeypatch.setattr(assessment_executor, "crear_actividad_h5p", h5p)
    monkeypatch.setattr(assessment_executor, "crear_categoria", categoria)
    monkeypatch.setattr(assessment_executor, "crear_pregunta", pregunta)
    monkeypatch.setattr(assessment_executor, "agregar_pregunta", slot)
    return estado


def test_ejecuta_curso_completo_y_reanuda_sin_duplicar(proyecto, moodle, monkeypatch):
    monkeypatch.setattr(orchestrator, "generar_content_blueprint", lambda c: pytest.fail("Regeneró contenido"))
    monkeypatch.setattr(orchestrator, "generar_assessment_desde_actividades", lambda c: pytest.fail("Regeneró assessment"))
    resultado = orchestrator.ejecutar_cursomaker(proyecto.directorio, etapa="moodle")
    assert resultado.moodle_resultado["estado"] == "completado"
    assert resultado.moodle_resultado["assessment"]["creadas"] == 4
    assert resultado.moodle_resultado["paginas_verificadas"] == 1
    assert moodle["operaciones"].count("h5pactivity") == 1
    assert moodle["cursos"][0]["visible"] is False
    assert resultado.moodle_report_path.is_file()
    operaciones = list(moodle["operaciones"])
    moodle_pipeline.ejecutar_pipeline_moodle(proyecto)
    assert moodle["operaciones"] == operaciones
    cmid = moodle["secciones"][0]["actividades"][0]["id"]
    moodle["contenido"][cmid] = "Contenido alterado"
    moodle_pipeline.ejecutar_pipeline_moodle(proyecto)
    assert moodle["contenido"][cmid] == "<p>Texto fuente</p>"
    assert moodle["operaciones"].count("actualizar_pagina") == 2


def test_dry_run_no_modifica_moodle(proyecto, moodle):
    resultado = moodle_pipeline.ejecutar_pipeline_moodle(proyecto, dry_run=True)
    assert resultado.moodle_resultado["estado"] == "validado"
    assert moodle["operaciones"] == []


def test_bloquea_curso_visible(proyecto, moodle):
    moodle["cursos"] = [{"id": 7, "nombre": "Curso oficial", "shortname": "omi110", "visible": True}]
    with pytest.raises(RuntimeError, match="oculto"):
        moodle_pipeline.ejecutar_pipeline_moodle(proyecto)
    assert moodle["operaciones"] == []


def test_no_usa_coincidencia_parcial_de_shortname(proyecto, moodle):
    moodle["cursos"] = [{"id": 8, "nombre": "Otro", "shortname": "omi110-otro", "visible": True}]
    moodle_pipeline.ejecutar_pipeline_moodle(proyecto)
    assert len(moodle["cursos"]) == 2
    assert moodle["cursos"][0]["visible"] is True


def test_modulo_sin_destino_falla_antes_de_escribir(proyecto, moodle):
    ruta = proyecto.output_dir / "assessment_blueprint.json"
    datos = json.loads(ruta.read_text())
    datos["modulos"][0]["titulo"] = "Título diferente"
    ruta.write_text(json.dumps(datos))
    with pytest.raises(ValueError, match="modulo_secciones"):
        moodle_pipeline.ejecutar_pipeline_moodle(proyecto)
    assert moodle["operaciones"] == []
    proyecto.config.modulo_secciones = {1: "Módulo 1"}
    moodle_pipeline.ejecutar_pipeline_moodle(proyecto)
    assert proyecto.moodle_resultado["estado"] == "completado"


def test_reanuda_quiz_despues_de_fallo_de_slot(proyecto, moodle, monkeypatch):
    def fallar(*args, **kwargs):
        raise RuntimeError("Fallo slot")
    monkeypatch.setattr(assessment_executor, "agregar_pregunta", fallar)
    with pytest.raises(RuntimeError, match="Fallo slot"):
        moodle_pipeline.ejecutar_pipeline_moodle(proyecto)
    assert moodle["operaciones"].count("pregunta") == 1
    monkeypatch.setattr(assessment_executor, "agregar_pregunta", lambda *args, **kwargs: {"slotid": 40})
    moodle_pipeline.ejecutar_pipeline_moodle(proyecto)
    assert moodle["operaciones"].count("pregunta") == 1
    assert moodle["operaciones"].count("quiz") == 1


def test_checkpoint_de_otro_servidor_no_modifica_moodle(proyecto, moodle, monkeypatch):
    moodle_pipeline.ejecutar_pipeline_moodle(proyecto)
    operaciones = list(moodle["operaciones"])
    monkeypatch.setattr(courses, "MOODLE_URL", "https://otro.example.test")
    with pytest.raises(RuntimeError, match="otro curso o servidor"):
        moodle_pipeline.ejecutar_pipeline_moodle(proyecto)
    assert moodle["operaciones"] == operaciones


def test_render_desactualizado_falla_antes_de_escribir(proyecto, moodle):
    ruta = proyecto.output_dir / "blueprint_render.json"
    datos = json.loads(ruta.read_text())
    datos["secciones"][0]["contenidos"][0]["bloques"][0]["html"] = "HTML alterado"
    ruta.write_text(json.dumps(datos))
    with pytest.raises(ValueError, match="desactualizado"):
        moodle_pipeline.ejecutar_pipeline_moodle(proyecto)
    assert moodle["operaciones"] == []


def test_recurso_faltante_queda_pendiente(proyecto, moodle):
    ruta = proyecto.output_dir / "assessment_blueprint.json"
    datos = json.loads(ruta.read_text())
    datos["modulos"][0]["actividades"][-1]["recursos"] = [{
        "tipo": "imagen", "descripcion": "Recurso ausente", "requerido": True, "disponible": False,
    }]
    ruta.write_text(json.dumps(datos))
    moodle_pipeline.ejecutar_pipeline_moodle(proyecto)
    assert proyecto.moodle_resultado["estado"] == "con_pendientes"
    assert proyecto.moodle_resultado["assessment"]["pendientes"] == 1
    assert "h5pactivity" not in moodle["operaciones"]



def test_cli_dry_run_funciona_desde_otro_directorio(proyecto, tmp_path):
    import subprocess
    import sys
    import shutil
    from pathlib import Path

    original = Path(orchestrator.__file__).resolve().parent.parent
    entrada = tmp_path / "execute_cursomaker.py"
    shutil.copy2(original / "execute_cursomaker.py", entrada)
    for carpeta in ("models", "services", "tools"):
        shutil.copytree(original / carpeta, tmp_path / carpeta, ignore=shutil.ignore_patterns("__pycache__"))
    externo = tmp_path / "directorio_externo"
    externo.mkdir()
    resultado = subprocess.run(
        [sys.executable, str(entrada), str(proyecto.directorio), "--etapa", "moodle", "--dry-run"],
        cwd=externo, text=True, capture_output=True,
    )
    assert resultado.returncode == 0, resultado.stderr
    assert "Moodle: validado" in resultado.stdout
    assert not (proyecto.output_dir / "execution_render_checkpoint.json").exists()

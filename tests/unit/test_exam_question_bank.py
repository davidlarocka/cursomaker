import json

import fitz
import pytest

from services import exam_question_bank as banco
from services import orchestrator


@pytest.fixture
def proyecto(tmp_path, monkeypatch):
    monkeypatch.setattr(orchestrator, "PROYECTO_DIR", tmp_path)
    directorio = tmp_path / "documents" / "omi110"
    directorio.mkdir(parents=True)
    (directorio / "config.json").write_text(json.dumps({"nombre": "OMI", "shortname": "omi110"}))
    (directorio / "manual.pdf").touch()
    (directorio / "actividades.pdf").touch()
    crear_pdf(directorio / "examen.pdf")
    return directorio


def crear_pdf(ruta, texto=None):
    texto = texto or ("Examen final\nP1. Seleccione <uno>\na) A\nb) B\nc) C\nd) D\nCorrecta: B\n"
                      "Preguntas adicionales (Banco de reserva)\nP2. Reserva\na) A\nb) B\nc) C\nd) D\nCorrecta: A")
    with fitz.open() as pdf:
        pdf.new_page().insert_text((50, 50), texto)
        pdf.save(ruta)


@pytest.fixture
def moodle(monkeypatch):
    monkeypatch.setattr(banco.courses, "MOODLE_URL", "https://moodle.example")
    monkeypatch.setattr(banco.courses, "MOODLE_TOKEN", "test")
    monkeypatch.setattr(banco.courses, "listar_cursos", lambda: [{"id": 8, "shortname": "omi110"}])
    llamadas = []

    def request(funcion, params):
        llamadas.append((funcion, params))
        if funcion == "local_cursomaker_create_question_category":
            return {"categoryid": len(llamadas)}
        assert funcion == "local_cursomaker_create_question"
        return {"questionid": len(llamadas)}

    monkeypatch.setattr(banco.questions, "_moodle_request", request)
    return llamadas


def ejecutar(proyecto, dry_run=False):
    return orchestrator.ejecutar_cursomaker(
        proyecto, etapa="banco-examen", examen="examen.pdf", courseid=8, dry_run=dry_run,
    )


def test_carga_y_reanudacion_sin_actividad_ni_duplicados(proyecto, moodle):
    resultado = ejecutar(proyecto)
    assert resultado.banco_examen_resultado["creadas"] == 2
    assert len(moodle) == 4
    preguntas = [p for f, p in moodle if f.endswith("create_question")]
    assert preguntas[0]["categoryid"] != preguntas[1]["categoryid"]
    assert preguntas[0]["questiontext"] == "<p>Seleccione &lt;uno&gt;</p>"
    assert [a["fraction"] for a in preguntas[0]["answers"]] == [0, 1, 0, 0]
    otra = ejecutar(proyecto)
    assert otra.banco_examen_resultado["creadas"] == 0
    assert otra.banco_examen_resultado["omitidas"] == 2
    assert len(moodle) == 4


def test_dry_run_sin_red_y_sin_alterar_blueprints(proyecto, monkeypatch):
    def prohibido(*args, **kwargs):
        pytest.fail("No se permite ejecutar Moodle ni generar contenido/assessment")

    monkeypatch.setattr(banco.courses, "listar_cursos", prohibido)
    monkeypatch.setattr(orchestrator, "generar_content_blueprint", prohibido)
    monkeypatch.setattr(orchestrator, "generar_assessment_desde_actividades", prohibido)
    contexto = orchestrator.preparar_curso(proyecto)
    for nombre in ("blueprint.json", "assessment_blueprint.json"):
        (contexto.output_dir / nombre).write_text("conservar")
    resultado = ejecutar(proyecto, dry_run=True)
    assert resultado.banco_examen_resultado["principales"] == 1
    assert resultado.banco_examen_resultado["reserva"] == 1
    for nombre in ("blueprint.json", "assessment_blueprint.json"):
        assert (contexto.output_dir / nombre).read_text() == "conservar"
    assert not (contexto.output_dir / "question_bank").exists()


def test_cambio_examen_bloquea_antes_de_crear(proyecto, moodle):
    ejecutar(proyecto)
    crear_pdf(proyecto / "examen.pdf", "P1. Otra\na) A\nb) B\nc) C\nd) D\nCorrecta: A")
    with pytest.raises(RuntimeError, match="otro contenido"):
        ejecutar(proyecto)
    assert len(moodle) == 4


def test_timeout_no_reintenta_pregunta_incierta(proyecto, monkeypatch, moodle):
    def fallo(*args):
        raise RuntimeError("timeout")

    monkeypatch.setattr(banco.questions, "crear_pregunta_desde_modelo", fallo)
    with pytest.raises(RuntimeError, match="timeout"):
        ejecutar(proyecto)
    with pytest.raises(RuntimeError, match="incierto"):
        ejecutar(proyecto)
    assert len(moodle) == 1  # Solo se creó la primera categoría.


@pytest.mark.parametrize("texto", [
    "P1. Uno\na) A\nb) B\nc) C\nd) D",  # Sin clave.
    "P2. Uno\na) A\nb) B\nc) C\nd) D\nCorrecta: A",  # Falta P1.
    "P1. Uno\na) A\nb) B\nd) D\nCorrecta: A",  # Falta alternativa.
])
def test_pdf_incompleto_no_escribe_en_moodle(proyecto, moodle, texto):
    crear_pdf(proyecto / "examen.pdf", texto)
    with pytest.raises(ValueError):
        ejecutar(proyecto)
    assert not moodle


def test_curso_equivocado_no_crea_categorias(proyecto, moodle, monkeypatch):
    monkeypatch.setattr(banco.courses, "listar_cursos", lambda: [{"id": 8, "shortname": "otro"}])
    with pytest.raises(RuntimeError, match="no coincide"):
        ejecutar(proyecto)
    assert not moodle


def test_checkpoint_separado_por_servidor(proyecto, moodle, monkeypatch):
    primero = ejecutar(proyecto)
    monkeypatch.setattr(banco.courses, "MOODLE_URL", "https://produccion.example")
    segundo = ejecutar(proyecto)
    assert primero.banco_examen_report_path != segundo.banco_examen_report_path
    assert segundo.banco_examen_resultado["creadas"] == 2


def test_parametros_solo_en_etapa_banco(proyecto):
    with pytest.raises(ValueError, match="requiere"):
        orchestrator.ejecutar_cursomaker(proyecto, etapa="banco-examen")
    with pytest.raises(ValueError, match="solo se admiten"):
        orchestrator.ejecutar_cursomaker(proyecto, etapa="moodle", courseid=8)

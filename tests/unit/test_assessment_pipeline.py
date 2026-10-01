import json

import fitz
import pytest

from models.assessment_blueprint import AssessmentBlueprint
from services import assessment_blueprint_generator as generador
from services import orchestrator


@pytest.fixture
def curso(tmp_path, monkeypatch):
    monkeypatch.setattr(orchestrator, "PROYECTO_DIR", tmp_path)
    directorio = tmp_path / "documents" / "omi110"
    directorio.mkdir(parents=True)
    (directorio / "config.json").write_text(json.dumps({
        "nombre": "Curso oficial", "shortname": "omi110",
    }), encoding="utf-8")
    (directorio / "manual.pdf").touch()
    with fitz.open() as documento:
        documento.new_page().insert_text((72, 72), "Actividad: describir las cargas peligrosas")
        documento.save(directorio / "actividades.pdf")
    return directorio


def assessment():
    return AssessmentBlueprint.model_validate({
        "curso": "Nombre inventado", "documento_fuente": "inventado.pdf",
        "modulos": [{"numero": 1, "titulo": "Introducción", "actividades": [{
            "tipo": "desarrollo", "id_logico": "m1-desarrollo-1", "modulo": 1,
            "titulo": "Describir cargas", "escenario": "Cargas peligrosas",
            "paginas_fuente": [1], "preguntas": [{"numero": 1, "enunciado": "Describa"}],
        }]}],
    })


def test_assessment_extrae_pdf_y_preserva_content_existente(curso, monkeypatch):
    contexto = orchestrator.preparar_curso(curso)
    contenido = contexto.output_dir / "blueprint.json"
    contenido.write_text("contenido anterior", encoding="utf-8")
    textos = []

    def generar(texto):
        textos.append(texto)
        return assessment()

    def no_generar_contenido(contexto):
        pytest.fail("La etapa assessment no debe generar contenido")

    monkeypatch.setattr(generador, "generar_assessment_blueprint", generar)
    monkeypatch.setattr(orchestrator, "generar_content_blueprint", no_generar_contenido)
    resultado = orchestrator.ejecutar_cursomaker(curso, etapa="assessment")
    blueprint = AssessmentBlueprint.model_validate_json(
        resultado.assessment_blueprint_path.read_text(encoding="utf-8")
    )
    assert "--- PÁGINA 1 ---" in textos[0]
    assert "Actividad: describir" in textos[0]
    assert blueprint.curso == "Curso oficial"
    assert blueprint.documento_fuente == "actividades.pdf"
    assert blueprint.modulos[0].actividades[0].paginas_fuente == [1]
    assert contenido.read_text(encoding="utf-8") == "contenido anterior"
    assert resultado.content_blueprint_path is None


def test_default_ejecuta_ambos_en_orden(curso, monkeypatch):
    etapas = []

    def ejecutar(nombre, contexto):
        etapas.append(nombre)
        return contexto.output_dir / nombre

    monkeypatch.setattr(orchestrator, "generar_content_blueprint", lambda c: ejecutar("blueprint.json", c))
    monkeypatch.setattr(orchestrator, "generar_assessment_desde_actividades", lambda c: ejecutar("assessment_blueprint.json", c))
    resultado = orchestrator.ejecutar_cursomaker(curso)
    assert etapas == ["blueprint.json", "assessment_blueprint.json"]
    assert resultado.content_blueprint_path is not None
    assert resultado.assessment_blueprint_path is not None


def test_fallo_conserva_assessment_anterior(curso, monkeypatch):
    contexto = orchestrator.preparar_curso(curso)
    salida = contexto.output_dir / "assessment_blueprint.json"
    anterior = assessment().model_dump_json()
    salida.write_text(anterior, encoding="utf-8")

    def fallar(texto):
        raise RuntimeError("Error del proveedor")

    monkeypatch.setattr(generador, "generar_assessment_blueprint", fallar)
    with pytest.raises(RuntimeError):
        orchestrator.ejecutar_cursomaker(curso, etapa="assessment")
    assert salida.read_text(encoding="utf-8") == anterior


def test_rechaza_documento_sin_texto(curso, monkeypatch):
    with fitz.open() as documento:
        documento.new_page()
        documento.save(curso / "actividades.pdf")
    monkeypatch.setattr(generador, "generar_assessment_blueprint", lambda texto: pytest.fail("Documento vacío enviado al modelo"))
    with pytest.raises(ValueError, match="no contiene texto"):
        orchestrator.ejecutar_cursomaker(curso, etapa="assessment")


def test_rechaza_assessment_sin_actividades(curso, monkeypatch):
    vacio = assessment().model_copy(update={"modulos": []})
    monkeypatch.setattr(generador, "generar_assessment_blueprint", lambda texto: vacio)
    with pytest.raises(ValueError, match="no contiene actividades"):
        orchestrator.ejecutar_cursomaker(curso, etapa="assessment")


def test_rechaza_etapa_desconocida_antes_de_preparar(curso):
    with pytest.raises(ValueError, match="Etapa no soportada"):
        orchestrator.ejecutar_cursomaker(curso, etapa="desconocida")
    assert not (curso.parent.parent / "output").exists()

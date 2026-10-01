import json

import fitz
import pytest

from models.blueprint import CursoBlueprint
from services import blueprint_generator, orchestrator


@pytest.fixture
def curso(tmp_path, monkeypatch):
    monkeypatch.setattr(orchestrator, "PROYECTO_DIR", tmp_path)
    directorio = tmp_path / "documents" / "omi110"
    directorio.mkdir(parents=True)
    (directorio / "config.json").write_text(json.dumps({
        "nombre": "Curso oficial", "shortname": "omi110",
        "descripcion": "Descripción oficial",
    }), encoding="utf-8")
    with fitz.open() as documento:
        documento.new_page().insert_text((72, 72), "Introduccion a cargas peligrosas")
        documento.save(directorio / "manual.pdf")
    (directorio / "actividades.pdf").touch()
    return directorio


def blueprint_generado():
    return CursoBlueprint.model_validate({
        "nombre": "Nombre del modelo", "shortname": "nombre-inventado",
        "descripcion": "Descripción del modelo", "objetivos": ["Aprender"],
        "secciones": [{"titulo": "Introducción", "contenidos": [{
            "tipo": "pagina", "titulo": "Cargas peligrosas",
            "contenido": "<p>Introducción</p>", "paginas_fuente": [1],
        }]}],
    })


def test_pipeline_extrae_pdf_y_guarda_identidad_configurada(curso, monkeypatch):
    textos = []

    def generar(texto):
        textos.append(texto)
        return blueprint_generado()

    monkeypatch.setattr(blueprint_generator, "generar_blueprint", generar)
    contexto = orchestrator.ejecutar_cursomaker(curso)
    resultado = CursoBlueprint.model_validate_json(
        contexto.content_blueprint_path.read_text(encoding="utf-8")
    )
    assert "--- PÁGINA 1 ---" in textos[0]
    assert "Introduccion a cargas peligrosas" in textos[0]
    assert resultado.nombre == "Curso oficial"
    assert resultado.shortname == "omi110"
    assert resultado.descripcion == "Descripción oficial"
    assert resultado.secciones[0].contenidos[0].paginas_fuente == [1]
    assert contexto.content_blueprint_path == contexto.output_dir / "blueprint.json"
    assert not list(contexto.output_dir.glob("*.tmp"))


def test_fallo_de_generacion_conserva_blueprint_anterior(curso, monkeypatch):
    contexto = orchestrator.preparar_curso(curso)
    salida = contexto.output_dir / "blueprint.json"
    anterior = blueprint_generado().model_dump_json()
    salida.write_text(anterior, encoding="utf-8")

    def fallar(texto):
        raise RuntimeError("Fallo del proveedor")

    monkeypatch.setattr(blueprint_generator, "generar_blueprint", fallar)
    with pytest.raises(RuntimeError, match="Fallo del proveedor"):
        orchestrator.ejecutar_cursomaker(curso)
    assert salida.read_text(encoding="utf-8") == anterior


def test_manual_sin_texto_no_llama_al_modelo(curso, monkeypatch):
    with fitz.open() as documento:
        documento.new_page()
        documento.save(curso / "manual.pdf")

    def no_debe_llamarse(texto):
        pytest.fail("No debe enviar documentos vacíos al proveedor")

    monkeypatch.setattr(blueprint_generator, "generar_blueprint", no_debe_llamarse)
    with pytest.raises(ValueError, match="no contiene texto"):
        orchestrator.ejecutar_cursomaker(curso)


def test_rechaza_blueprint_sin_secciones(curso, monkeypatch):
    vacio = blueprint_generado().model_copy(update={"secciones": []})
    monkeypatch.setattr(blueprint_generator, "generar_blueprint", lambda texto: vacio)
    with pytest.raises(ValueError, match="no contiene secciones"):
        orchestrator.ejecutar_cursomaker(curso)
    assert not (curso.parent.parent / "output" / "omi110" / "blueprint.json").exists()

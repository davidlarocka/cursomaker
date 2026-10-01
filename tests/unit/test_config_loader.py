import json

import pytest
from pydantic import ValidationError

from services.config_loader import cargar_config


@pytest.fixture
def curso_dir(tmp_path):
    directorio = tmp_path / "documents" / "omi110"
    directorio.mkdir(parents=True)
    (directorio / "config.json").write_text(
        json.dumps({"nombre": "Cargas peligrosas", "shortname": "omi110"}),
        encoding="utf-8",
    )
    for nombre in ("manual.pdf", "actividades.pdf"):
        (directorio / nombre).touch()
    return directorio


def test_resuelve_documentos_desde_curso_y_no_desde_cwd(curso_dir, monkeypatch):
    monkeypatch.chdir(curso_dir.parent.parent)
    config = cargar_config("documents/omi110")
    assert config.manual == curso_dir / "manual.pdf"
    assert config.actividades == curso_dir / "actividades.pdf"
    assert not (curso_dir.parent.parent / "output").exists()


def test_admite_nombres_de_documento_configurados(curso_dir):
    (curso_dir / "manual.pdf").rename(curso_dir / "fuente.pdf")
    (curso_dir / "config.json").write_text(
        json.dumps({"nombre": "OMI", "shortname": "omi110", "manual": "fuente.pdf"}),
        encoding="utf-8",
    )
    assert cargar_config(curso_dir).manual == curso_dir / "fuente.pdf"


def test_rechaza_documento_ausente(curso_dir):
    (curso_dir / "actividades.pdf").unlink()
    with pytest.raises(FileNotFoundError, match="actividades"):
        cargar_config(curso_dir)


@pytest.mark.parametrize("cambio", [
    {"nombre": " "}, {"shortname": ""}, {"categoria_id": 0},
    {"manual": "manual.txt"}, {"campo_desconocido": True},
])
def test_rechaza_config_invalida(curso_dir, cambio):
    datos = {"nombre": "OMI", "shortname": "omi110", **cambio}
    (curso_dir / "config.json").write_text(json.dumps(datos), encoding="utf-8")
    with pytest.raises(ValidationError):
        cargar_config(curso_dir)


def test_rechaza_json_invalido(curso_dir):
    (curso_dir / "config.json").write_text("{", encoding="utf-8")
    with pytest.raises(ValidationError):
        cargar_config(curso_dir)


def test_rechaza_config_ausente(curso_dir):
    (curso_dir / "config.json").unlink()
    with pytest.raises(FileNotFoundError):
        cargar_config(curso_dir)

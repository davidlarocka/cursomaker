import json

import pytest

from services import orchestrator


def preparar_documentos(proyecto, curso):
    directorio = proyecto / "documents" / curso
    directorio.mkdir(parents=True)
    (directorio / "config.json").write_text(
        json.dumps({"nombre": curso, "shortname": curso}), encoding="utf-8"
    )
    for nombre in ("manual.pdf", "actividades.pdf"):
        (directorio / nombre).touch()
    return directorio


def test_prepara_cursos_sin_mezclar_artefactos(tmp_path, monkeypatch):
    monkeypatch.setattr(orchestrator, "PROYECTO_DIR", tmp_path)
    primero = preparar_documentos(tmp_path, "omi110")
    segundo = preparar_documentos(tmp_path, "omi141")
    monkeypatch.chdir(primero)
    contexto = orchestrator.ejecutar_cursomaker(primero)
    artefacto = contexto.output_dir / "existente.json"
    artefacto.write_text("{}", encoding="utf-8")
    repetido = orchestrator.ejecutar_cursomaker(primero)
    otro = orchestrator.ejecutar_cursomaker(segundo)
    assert repetido == contexto
    assert contexto.assets_dir == tmp_path / "assets" / "omi110"
    assert contexto.assets_dir.is_dir()
    assert contexto.output_dir.is_dir()
    assert otro.output_dir != contexto.output_dir
    assert otro.assets_dir != contexto.assets_dir
    assert artefacto.read_text(encoding="utf-8") == "{}"


def test_no_crea_salidas_si_faltan_documentos(tmp_path, monkeypatch):
    monkeypatch.setattr(orchestrator, "PROYECTO_DIR", tmp_path)
    directorio = preparar_documentos(tmp_path, "omi110")
    (directorio / "manual.pdf").unlink()
    with pytest.raises(FileNotFoundError):
        orchestrator.ejecutar_cursomaker(directorio)
    assert not (tmp_path / "assets").exists()
    assert not (tmp_path / "output").exists()

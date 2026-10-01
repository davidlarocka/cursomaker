import json

import fitz
import pytest

from models.blueprint import AnalisisImagen, CursoBlueprint, ResolucionDestinoImagen
from models.render_blueprint import CursoRender, AsignacionImagenSubseccion
from services import image_pipeline as pipeline, orchestrator
from services.html_renderer import renderizar_contenido


def escribir_manual(ruta, texto="Cargas peligrosas", imagen=True):
    with fitz.open() as pdf:
        pagina = pdf.new_page()
        pagina.insert_text((72, 72), texto)
        if imagen:
            pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 20, 20), 0)
            pixmap.clear_with(120)
            pagina.insert_image(fitz.Rect(72, 100, 172, 200), stream=pixmap.tobytes("png"))
        pdf.save(ruta)


def blueprint(html="<p>Cargas peligrosas</p>", paginas=None):
    return CursoBlueprint.model_validate({
        "nombre": "Curso oficial", "shortname": "omi110", "descripcion": "Curso",
        "objetivos": [], "secciones": [{"titulo": "Introducción", "contenidos": [{
            "tipo": "pagina", "titulo": "Cargas", "contenido": html,
            "paginas_fuente": [1] if paginas is None else paginas,
        }]}],
    })


@pytest.fixture
def curso(tmp_path, monkeypatch):
    monkeypatch.setattr(orchestrator, "PROYECTO_DIR", tmp_path)
    directorio = tmp_path / "documents" / "omi110"
    directorio.mkdir(parents=True)
    (directorio / "config.json").write_text(json.dumps({
        "nombre": "Curso oficial", "shortname": "omi110",
    }), encoding="utf-8")
    escribir_manual(directorio / "manual.pdf")
    (directorio / "actividades.pdf").touch()
    contexto = orchestrator.preparar_curso(directorio)
    (contexto.output_dir / "blueprint.json").write_text(blueprint().model_dump_json(), encoding="utf-8")
    monkeypatch.setattr(pipeline, "analizar_imagen", lambda *args: analisis())
    return contexto


def analisis():
    return AnalisisImagen(es_pedagogica=True, tipo="diagrama", descripcion="Diagrama de cargas",
                          relacion_con_texto="Cargas peligrosas", recomendacion="incluir")


def leer(ruta):
    return json.loads(ruta.read_text(encoding="utf-8"))


def test_extrae_imagen_mapea_y_construye_render_sin_regenerar_blueprints(curso, monkeypatch):
    original = (curso.output_dir / "blueprint.json").read_bytes()
    monkeypatch.setattr(orchestrator, "generar_content_blueprint", lambda c: pytest.fail("Regeneró contenido"))
    monkeypatch.setattr(orchestrator, "generar_assessment_desde_actividades", lambda c: pytest.fail("Regeneró assessment"))
    resultado = orchestrator.ejecutar_cursomaker(curso.directorio, etapa="imagenes")
    inventario = leer(resultado.image_analysis_path)["imagenes"]
    assert len(inventario) == 1
    assert next(iter(inventario.values()))["estado"] == "analizada"
    imagen = next(iter(leer(resultado.image_mapping_path)["imagenes"].values()))
    assert imagen["metodo_asignacion"] == "deterministico"
    assert imagen["pagina"] == 1
    render = CursoRender.model_validate_json(resultado.render_blueprint_path.read_text())
    contenido = render.secciones[0].contenidos[0]
    assert [b.tipo for b in contenido.bloques] == ["html", "imagen"]
    assert contenido.bloques[0].html == "<p>Cargas peligrosas</p>"
    assert contenido.bloques[1].imagen.alt == "Diagrama de cargas"
    assert (curso.assets_dir / contenido.bloques[1].imagen.archivo).is_file()
    assert leer(resultado.subsection_mapping_path)["sin_estructura"]
    assert (curso.output_dir / "blueprint.json").read_bytes() == original
    assert "Diagrama de cargas" in renderizar_contenido(contenido, {})


def test_reanuda_analisis_sin_nueva_llamada(curso, monkeypatch):
    pipeline.ejecutar_pipeline_imagenes(curso)
    monkeypatch.setattr(pipeline, "analizar_imagen", lambda *args: pytest.fail("Repitió análisis"))
    pipeline.ejecutar_pipeline_imagenes(curso)


def test_cambio_del_manual_invalida_analisis(curso, monkeypatch):
    pipeline.ejecutar_pipeline_imagenes(curso)
    llamadas = []
    escribir_manual(curso.config.manual, texto="Nuevo contexto de cargas")
    def analizar(*args):
        llamadas.append(args)
        return analisis()
    monkeypatch.setattr(pipeline, "analizar_imagen", analizar)
    pipeline.ejecutar_pipeline_imagenes(curso)
    assert len(llamadas) == 1
    assert "Nuevo contexto" in llamadas[0][2]


def test_error_visual_guarda_checkpoint_y_permite_reintento(curso, monkeypatch):
    def fallar(*args):
        raise RuntimeError("Fallo simulado")
    monkeypatch.setattr(pipeline, "analizar_imagen", fallar)
    with pytest.raises(RuntimeError, match="Falló el análisis"):
        pipeline.ejecutar_pipeline_imagenes(curso)
    estado = leer(curso.output_dir / "image_analysis.json")
    assert next(iter(estado["imagenes"].values()))["estado"] == "error"
    assert not (curso.output_dir / "blueprint_render.json").exists()
    monkeypatch.setattr(pipeline, "analizar_imagen", lambda *args: analisis())
    pipeline.ejecutar_pipeline_imagenes(curso)
    assert next(iter(leer(curso.image_analysis_path)["imagenes"].values()))["estado"] == "analizada"


def test_manual_sin_imagenes_genera_render_html(curso, monkeypatch):
    escribir_manual(curso.config.manual, imagen=False)
    monkeypatch.setattr(pipeline, "analizar_imagen", lambda *args: pytest.fail("Llamó análisis sin imágenes"))
    resultado = pipeline.ejecutar_pipeline_imagenes(curso)
    assert leer(resultado.image_mapping_path)["imagenes"] == {}
    assert leer(resultado.subsection_mapping_path)["asignaciones"] == {}
    render = CursoRender.model_validate_json(resultado.render_blueprint_path.read_text())
    assert len(render.secciones[0].contenidos[0].bloques) == 1


def test_imagen_sin_destino_bloquea_render(curso):
    (curso.output_dir / "blueprint.json").write_text(blueprint(paginas=[2]).model_dump_json())
    with pytest.raises(RuntimeError, match="no tiene destino"):
        pipeline.ejecutar_pipeline_imagenes(curso)
    assert not (curso.output_dir / "blueprint_render.json").exists()


def test_resuelve_destino_ambiguo_y_subseccion_con_servicios_existentes(curso, monkeypatch):
    html = "<h3>Uno</h3><p>Uno</p><h3>Dos</h3><p>Dos</p>"
    contenido = blueprint(html)
    contenido.secciones[0].contenidos.append(contenido.secciones[0].contenidos[0].model_copy(update={"titulo": "Segundo"}))
    (curso.output_dir / "blueprint.json").write_text(contenido.model_dump_json())
    llamadas = []
    def resolver(imagen, texto, destinos):
        llamadas.append("destino")
        assert len(destinos) == 2
        return ResolucionDestinoImagen(indice_destino=1, justificacion="Segundo contenido")
    def subseccion(imagen, subsecciones):
        llamadas.append("subseccion")
        return AsignacionImagenSubseccion(indice_subseccion=1, justificacion="Segunda subsección")
    monkeypatch.setattr(pipeline, "resolver_destino_imagen", resolver)
    monkeypatch.setattr(pipeline, "asignar_imagen_subseccion", subseccion)
    resultado = pipeline.ejecutar_pipeline_imagenes(curso)
    assert llamadas == ["destino", "subseccion"]
    imagen = next(iter(leer(resultado.image_mapping_path)["imagenes"].values()))
    assert imagen["contenido_numero"] == 2
    mapping = leer(resultado.subsection_mapping_path)["asignaciones"]
    assert next(iter(mapping.values()))["indice_subseccion"] == 1
    render = CursoRender.model_validate_json(resultado.render_blueprint_path.read_text())
    assert "Diagrama de cargas" in renderizar_contenido(render.secciones[0].contenidos[1], mapping)
    pipeline.ejecutar_pipeline_imagenes(curso)
    assert llamadas == ["destino", "subseccion"]


def test_falta_blueprint_falla_antes_de_extraer(curso, monkeypatch):
    (curso.output_dir / "blueprint.json").unlink()
    monkeypatch.setattr(pipeline, "extraer_imagenes_pdf", lambda *args: pytest.fail("Extrajo sin blueprint"))
    with pytest.raises(FileNotFoundError, match="Falta Content Blueprint"):
        pipeline.ejecutar_pipeline_imagenes(curso)


def test_identidad_incompatible_falla_antes_de_analizar(curso):
    datos = blueprint().model_copy(update={"shortname": "otro"})
    (curso.output_dir / "blueprint.json").write_text(datos.model_dump_json())
    with pytest.raises(ValueError, match="no coincide"):
        pipeline.ejecutar_pipeline_imagenes(curso)


def test_imagen_repetida_usa_todas_las_paginas_fuente(curso):
    with fitz.open(curso.config.manual) as origen:
        with fitz.open() as pdf:
            pdf.insert_pdf(origen)
            pdf.insert_pdf(origen)
            pdf.save(curso.directorio / "repetido.pdf")
    (curso.directorio / "repetido.pdf").replace(curso.config.manual)
    (curso.output_dir / "blueprint.json").write_text(blueprint(paginas=[2]).model_dump_json())
    resultado = pipeline.ejecutar_pipeline_imagenes(curso)
    inventario = leer(resultado.image_analysis_path)["imagenes"]
    assert len(inventario) == 1
    assert next(iter(inventario.values()))["paginas"] == [1, 2]
    assert next(iter(leer(resultado.image_mapping_path)["imagenes"].values()))["pagina"] == 2


def test_imagen_descartada_no_se_incorpora_al_render(curso, monkeypatch):
    descartada = analisis().model_copy(update={"es_pedagogica": False, "recomendacion": "descartar"})
    monkeypatch.setattr(pipeline, "analizar_imagen", lambda *args: descartada)
    resultado = pipeline.ejecutar_pipeline_imagenes(curso)
    assert leer(resultado.image_mapping_path)["imagenes"] == {}
    render = CursoRender.model_validate_json(resultado.render_blueprint_path.read_text())
    assert [bloque.tipo for bloque in render.secciones[0].contenidos[0].bloques] == ["html"]

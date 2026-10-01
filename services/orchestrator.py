from pathlib import Path
from typing import Union

from models.contexto_curso import ContextoCurso
from services.config_loader import cargar_config
from services.blueprint_generator import generar_content_blueprint
from services.assessment_blueprint_generator import generar_assessment_desde_actividades
from services.image_pipeline import ejecutar_pipeline_imagenes


PROYECTO_DIR = Path(__file__).resolve().parent.parent


def preparar_curso(curso_dir: Union[str, Path]) -> ContextoCurso:
    """Valida las entradas y prepara los directorios del curso."""
    directorio = Path(curso_dir).resolve()
    config = cargar_config(directorio)
    contexto = ContextoCurso(
        config=config,
        directorio=directorio,
        assets_dir=PROYECTO_DIR / "assets" / directorio.name,
        output_dir=PROYECTO_DIR / "output" / directorio.name,
    )
    contexto.assets_dir.mkdir(parents=True, exist_ok=True)
    contexto.output_dir.mkdir(parents=True, exist_ok=True)
    return contexto


def ejecutar_cursomaker(curso_dir: Union[str, Path], etapa: str = "todo") -> ContextoCurso:
    """Ejecuta las etapas integradas del pipeline oficial."""
    if etapa not in ("todo", "contenido", "assessment", "imagenes"):
        raise ValueError(f"Etapa no soportada: {etapa}")
    contexto = preparar_curso(curso_dir)
    if etapa in ("todo", "contenido"):
        contexto.content_blueprint_path = generar_content_blueprint(contexto)
    if etapa in ("todo", "assessment"):
        contexto.assessment_blueprint_path = generar_assessment_desde_actividades(contexto)
    if etapa in ("todo", "imagenes"):
        contexto = ejecutar_pipeline_imagenes(contexto)
    return contexto

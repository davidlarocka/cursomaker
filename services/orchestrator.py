from pathlib import Path
from typing import Union

from models.contexto_curso import ContextoCurso
from services.config_loader import cargar_config
from services.blueprint_generator import generar_content_blueprint
from services.assessment_blueprint_generator import generar_assessment_desde_actividades
from services.image_pipeline import ejecutar_pipeline_imagenes
from services.moodle_pipeline import ejecutar_pipeline_moodle
from services.exam_question_bank import ejecutar_banco_examen


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


def ejecutar_cursomaker(curso_dir: Union[str, Path], etapa: str = "todo", dry_run: bool = False,
                       examen=None, courseid=None) -> ContextoCurso:
    """Ejecuta las etapas integradas del pipeline oficial."""
    if etapa not in ("todo", "contenido", "assessment", "imagenes", "moodle", "banco-examen"):
        raise ValueError(f"Etapa no soportada: {etapa}")
    if etapa == "banco-examen":
        if not examen or courseid is None:
            raise ValueError("La etapa banco-examen requiere --examen y --course-id.")
    elif examen is not None or courseid is not None:
        raise ValueError("--examen y --course-id solo se admiten con --etapa banco-examen.")
    contexto = preparar_curso(curso_dir)
    if etapa == "banco-examen":
        return ejecutar_banco_examen(contexto, examen, courseid, dry_run=dry_run)
    if etapa in ("todo", "contenido"):
        contexto.content_blueprint_path = generar_content_blueprint(contexto)
    if etapa in ("todo", "assessment"):
        contexto.assessment_blueprint_path = generar_assessment_desde_actividades(contexto)
    if etapa in ("todo", "imagenes"):
        contexto = ejecutar_pipeline_imagenes(contexto)
    if etapa in ("todo", "moodle"):
        contexto = ejecutar_pipeline_moodle(contexto, dry_run=dry_run)
    return contexto

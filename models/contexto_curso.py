from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from models.curso_config import CursoConfig


class ContextoCurso(BaseModel):
    """Configuración y rutas compartidas por las etapas del orquestador."""

    config: CursoConfig
    directorio: Path
    assets_dir: Path
    output_dir: Path
    content_blueprint_path: Optional[Path] = None
    assessment_blueprint_path: Optional[Path] = None
    image_analysis_path: Optional[Path] = None
    image_mapping_path: Optional[Path] = None
    render_blueprint_path: Optional[Path] = None
    subsection_mapping_path: Optional[Path] = None

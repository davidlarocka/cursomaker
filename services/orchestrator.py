from pathlib import Path
from typing import Union

from models.contexto_curso import ContextoCurso
from services.config_loader import cargar_config


PROYECTO_DIR = Path(__file__).resolve().parent.parent


def ejecutar_cursomaker(curso_dir: Union[str, Path]) -> ContextoCurso:
    """Prepara el curso. Las siguientes etapas se integrarán aquí."""
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

from pathlib import Path
from typing import Union

from models.curso_config import CursoConfig


def cargar_config(curso_dir: Union[str, Path]) -> CursoConfig:
    """Carga config.json y resuelve los documentos respecto al directorio del curso.

    No crea carpetas ni ejecuta pipelines. Los errores de lectura y validación
    se propagan para que el punto de entrada pueda informar el fallo.
    """
    directorio = Path(curso_dir).resolve()
    config = CursoConfig.model_validate_json(
        (directorio / "config.json").read_text(encoding="utf-8")
    )

    documentos = {}
    for campo in ("manual", "actividades"):
        ruta = (directorio / getattr(config, campo)).resolve()
        if not ruta.is_file():
            raise FileNotFoundError(f"No existe el documento {campo}: {ruta}")
        documentos[campo] = ruta

    return config.model_copy(update=documentos)

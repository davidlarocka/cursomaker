from pathlib import Path

from pydantic import BaseModel


def guardar_blueprint(ruta: Path, blueprint: BaseModel) -> Path:
    """Publica el JSON completo sin truncar el resultado anterior ante un fallo."""
    temporal = ruta.with_suffix(".json.tmp")
    try:
        temporal.write_text(blueprint.model_dump_json(indent=2), encoding="utf-8")
        temporal.replace(ruta)
    finally:
        temporal.unlink(missing_ok=True)
    return ruta

from pathlib import Path
import json

from pydantic import BaseModel


def guardar_blueprint(ruta: Path, blueprint: BaseModel) -> Path:
    """Publica el JSON completo sin truncar el resultado anterior ante un fallo."""
    return guardar_json(ruta, blueprint.model_dump(mode="json"))


def guardar_json(ruta: Path, datos: dict) -> Path:
    """Guarda blueprints y checkpoints mediante reemplazo del archivo completo."""
    ruta = Path(ruta)
    temporal = ruta.with_suffix(".json.tmp")
    try:
        temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
        temporal.replace(ruta)
    finally:
        temporal.unlink(missing_ok=True)
    return ruta

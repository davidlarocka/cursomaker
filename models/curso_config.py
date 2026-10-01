from pathlib import Path
from typing import Dict

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CursoConfig(BaseModel):
    """Configuración del curso; las credenciales se mantienen en el entorno."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nombre: str = Field(min_length=1)
    shortname: str = Field(min_length=1)
    descripcion: str = ""
    categoria_id: int = Field(default=1, gt=0, strict=True)
    manual: Path = Path("manual.pdf")
    actividades: Path = Path("actividades.pdf")
    modulo_secciones: Dict[int, str] = Field(default_factory=dict)

    @field_validator("modulo_secciones")
    @classmethod
    def validar_modulo_secciones(cls, mapa):
        if any(numero < 1 or not titulo.strip() for numero, titulo in mapa.items()):
            raise ValueError("modulo_secciones requiere números positivos y títulos no vacíos.")
        return {numero: titulo.strip() for numero, titulo in mapa.items()}

    @field_validator("manual", "actividades")
    @classmethod
    def validar_pdf(cls, ruta: Path) -> Path:
        if ruta.suffix.lower() != ".pdf":
            raise ValueError("El documento debe tener extensión .pdf.")
        return ruta

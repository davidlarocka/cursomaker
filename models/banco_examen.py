from typing import List

from pydantic import BaseModel, Field, model_validator

from models.assessment_blueprint import PreguntaSeleccionMultiple


class BancoExamen(BaseModel):
    """Preguntas del examen, independientes de una actividad o sección Moodle."""

    documento_fuente: str
    principales: List[PreguntaSeleccionMultiple] = Field(min_length=1)
    reserva: List[PreguntaSeleccionMultiple] = Field(default_factory=list)

    @model_validator(mode="after")
    def validar_numeracion(self):
        preguntas = self.principales + self.reserva
        if [p.numero for p in preguntas] != list(range(1, len(preguntas) + 1)):
            raise ValueError("El examen debe contener preguntas consecutivas desde P1, sin duplicados.")
        return self

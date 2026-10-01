from typing import List, Literal, Optional

from pydantic import BaseModel, Field


EstadoQA = Literal[
    "aprobado",
    "requiere_correccion",
    "requiere_revision_humana",
]


class HallazgoAssessmentQA(BaseModel):
    tipo: Literal[
        "omision",
        "alteracion",
        "invencion",
        "respuesta_incorrecta",
        "recurso_faltante",
        "otro",
    ]

    descripcion: str

    evidencia_fuente: Optional[str] = None

    correccion_sugerida: Optional[str] = None


class ResultadoActividadQA(BaseModel):
    id_logico: str

    estado: EstadoQA

    justificacion: str

    hallazgos: List[HallazgoAssessmentQA] = Field(
        default_factory=list
    )


class AssessmentQA(BaseModel):
    resultados: List[ResultadoActividadQA] = Field(
        default_factory=list
    )
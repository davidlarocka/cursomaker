from typing import List
from pydantic import BaseModel, Field


class ContenidoBlueprint(BaseModel):
    tipo: str = Field(
        description="Tipo de contenido Moodle. Por ahora: pagina."
    )

    titulo: str = Field(
        description="Título del contenido."
    )

    contenido: str = Field(
        description="Contenido HTML que se utilizará en Moodle."
    )

    paginas_fuente: List[int] = Field(
        description="Páginas del PDF utilizadas como fuente."
    )


class SeccionBlueprint(BaseModel):
    titulo: str = Field(
        description="Título de la sección del curso."
    )

    contenidos: List[ContenidoBlueprint]


class CursoBlueprint(BaseModel):
    nombre: str

    shortname: str

    descripcion: str

    objetivos: List[str]

    secciones: List[SeccionBlueprint]
    
class ValidacionContenido(BaseModel):
    aprobado: bool

    fidelidad_fuente: int = Field(
        ge=0,
        le=100,
        description=(
            "Porcentaje estimado de las afirmaciones del contenido generado "
            "que están respaldadas por la fuente."
        ),
    )

    cobertura_contenido: int = Field(
        ge=0,
        le=100,
        description=(
            "Porcentaje estimado de la información pedagógicamente importante "
            "de la fuente que está representada en el contenido generado."
        ),
    )

    afirmaciones_no_respaldadas: List[str]

    omisiones_importantes: List[str]

    observaciones: List[str]
    
class AnalisisImagen(BaseModel):
    es_pedagogica: bool

    tipo: str = Field(
        description=(
            "Tipo de imagen: fotografia, diagrama, "
            "ilustracion, tabla, grafico, logo, "
            "decoracion u otro."
        )
    )

    descripcion: str = Field(
        description=(
            "Descripción breve y objetiva de lo que "
            "muestra la imagen."
        )
    )

    relacion_con_texto: str = Field(
        description=(
            "Explica brevemente cómo se relaciona "
            "la imagen con el contenido de la página."
        )
    )

    recomendacion: str = Field(
        description=(
            "Una de: incluir, descartar."
        )
    )
    
class ResolucionDestinoImagen(BaseModel):
    indice_destino: int = Field(
        ge=0,
        description=(
            "Índice del destino elegido dentro de "
            "la lista de destinos candidatos."
        ),
    )

    justificacion: str = Field(
        description=(
            "Explicación breve de por qué la imagen "
            "corresponde mejor a ese contenido."
        ),
    )    
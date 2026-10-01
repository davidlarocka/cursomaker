from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ImagenRender(BaseModel):
    archivo: str
    ruta: str
    pagina_fuente: int

    descripcion: str

    alt: str = Field(
        description=(
            "Texto alternativo breve y descriptivo "
            "para accesibilidad."
        )
    )


class BloqueRender(BaseModel):
    tipo: Literal[
        "html",
        "imagen",
        "tabla",
        "toggle",
    ]

    titulo: Optional[str] = None

    html: Optional[str] = None

    imagen: Optional[ImagenRender] = None

    bloques: List["BloqueRender"] = Field(
        default_factory=list
    )


class ContenidoRender(BaseModel):
    titulo: str

    paginas_fuente: List[int]

    bloques: List[BloqueRender]


class SeccionRender(BaseModel):
    titulo: str

    contenidos: List[ContenidoRender]


class CursoRender(BaseModel):
    nombre: str
    shortname: str
    descripcion: str

    secciones: List[SeccionRender]
    
    
class SubseccionDetectada(BaseModel):
    titulo: str

    contenido: str = Field(
        description=(
            "Contenido HTML correspondiente "
            "exclusivamente a esta subsección."
        )
    )


class EstructuraContenidoDetectada(BaseModel):
    introduccion: str = Field(
        description=(
            "HTML introductorio que aparece antes "
            "de las subsecciones."
        )
    )

    subsecciones: List[SubseccionDetectada]
    
class AsignacionImagenSubseccion(BaseModel):
    indice_subseccion: int = Field(
        ge=0,
        description=(
            "Índice de la subsección a la que "
            "mejor corresponde la imagen."
        ),
    )

    justificacion: str = Field(
        description=(
            "Explicación breve de la relación "
            "entre la imagen y la subsección."
        ),
    )

class ImagenSubseccionMapping(BaseModel):
    archivo: str
    contenido: str
    tipo_estructura: str
    indice_subseccion: int
    titulo_subseccion: str
    justificacion: str
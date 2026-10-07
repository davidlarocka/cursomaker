from typing import List, Literal, Optional, Union
from pydantic import BaseModel, Field, model_validator
from pydantic import BaseModel, Field


EstadoActividad = Literal[
    "extraido",
    "requiere_recurso",
    "listo_para_validar",
    "validado",
    "listo_para_ejecutar",
    "ejecutado",
    "verificado",
]


TipoRecurso = Literal[
    "imagen",
    "audio",
    "video",
    "archivo",
]


class RecursoActividad(BaseModel):
    tipo: TipoRecurso

    descripcion: str

    requerido: bool = True

    disponible: bool = False

    archivo: Optional[str] = None

    paginas_fuente: List[int] = Field(
        default_factory=list
    )


class IncidenciaActividad(BaseModel):
    codigo: str

    descripcion: str

    accion_humana: Optional[str] = None


class ActividadBase(BaseModel):
    id_logico: str = Field(
        description=(
            "Identificador estable de la actividad. "
            "No depende del ID de Moodle."
        )
    )

    modulo: int = Field(
        ge=1
    )

    titulo: str = Field(description="Nombre literal de la actividad tal como aparece en el documento fuente; no usar el título del caso o escenario.")

    descripcion: Optional[str] = Field(default=None, description="Título y contexto del caso práctico, si el documento los presenta por separado del nombre de la actividad.")

    paginas_fuente: List[int] = Field(
        default_factory=list
    )

    estado: EstadoActividad = "extraido"

    recursos: List[RecursoActividad] = Field(
        default_factory=list
    )

    incidencias: List[IncidenciaActividad] = Field(
        default_factory=list
    )
    
class AlternativaPregunta(BaseModel):
    texto: str

    correcta: bool = False


class PreguntaSeleccionMultiple(BaseModel):
    numero: int = Field(ge=1)
    enunciado: str
    alternativas: List[AlternativaPregunta]
    retroalimentacion: Optional[str] = None
    paginas_fuente: List[int] = Field(
        default_factory=list
    )
    
    @model_validator(mode="after")
    def validar_pregunta(self):
        if len(self.alternativas) < 2:
            raise ValueError(
                "La pregunta debe tener al menos dos alternativas."
            )

        correctas = sum(
            alternativa.correcta
            for alternativa in self.alternativas
        )

        if correctas != 1:
            raise ValueError(
                "La pregunta debe tener exactamente "
                "una alternativa correcta."
            )

        return self


class QuizModulo(ActividadBase):
    tipo: Literal["quiz"] = "quiz"

    instrucciones: Optional[str] = None

    preguntas: List[PreguntaSeleccionMultiple] = Field(
        default_factory=list
    )
    
class PreguntaDesarrollo(BaseModel):
    numero: int = Field(
        ge=1
    )

    enunciado: str


class ActividadDesarrollo(ActividadBase):
    tipo: Literal["desarrollo"] = "desarrollo"

    escenario: str

    instrucciones: Optional[str] = None

    preguntas: List[PreguntaDesarrollo] = Field(
        default_factory=list
    )
    
class ActividadDiscusion(ActividadBase):
    tipo: Literal["discusion"] = "discusion"

    caso: str

    pregunta_debate: str

    instrucciones: Optional[str] = None

    requiere_interaccion_pares: bool = False

    minimo_respuestas_pares: int = Field(
        default=0,
        ge=0,
    )
    
    @model_validator(mode="after")
    def validar_interaccion(self):
        if (
            self.requiere_interaccion_pares
            and self.minimo_respuestas_pares < 1
        ):
            raise ValueError(
                "Si la actividad requiere interacción entre pares, "
                "debe existir al menos una respuesta a compañeros."
            )

        return self

TipoH5P = Literal[
    "drag_and_drop",
    "course_presentation",
    "image_hotspots",
    "fill_in_the_blanks",
]


TipoH5P = Literal[
    "drag_and_drop",
    "course_presentation",
    "image_hotspots",
    "fill_in_the_blanks",
]

TipoH5PEjecucion = Literal[
    "drag_and_drop",
    "course_presentation",
    "single_choice_set",
    "image_hotspots",
    "fill_in_the_blanks",
]


class ActividadH5P(ActividadBase):
    tipo: Literal["h5p"] = "h5p"

    # Tipo solicitado originalmente por el documento fuente.
    h5p_tipo: TipoH5P

    # Tipo que CursoMaker ejecutará realmente en Moodle.
    # Si es None, se utiliza h5p_tipo.
    h5p_tipo_ejecucion: Optional[TipoH5PEjecucion] = None

    instrucciones: Optional[str] = None
    
class PuntoHotspot(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

    x: Optional[float] = None
    y: Optional[float] = None

class H5PImageHotspots(ActividadH5P):
    h5p_tipo: Literal["image_hotspots"] = "image_hotspots"

    hotspots: List[PuntoHotspot] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def validar_imagen_base(self):
        imagenes = [
            recurso
            for recurso in self.recursos
            if recurso.tipo == "imagen"
            and recurso.requerido
        ]

        imagen_disponible = any(
            recurso.disponible
            and recurso.archivo
            for recurso in imagenes
        )

        codigo = "H5P_IMAGE_HOTSPOTS_SIN_IMAGEN"

        if not imagen_disponible:
            self.estado = "requiere_recurso"

            if not any(
                incidencia.codigo == codigo
                for incidencia in self.incidencias
            ):
                self.incidencias.append(
                    IncidenciaActividad(
                        codigo=codigo,
                        descripcion=(
                            "La actividad Image Hotspots requiere "
                            "una imagen base y no fue encontrada."
                        ),
                        accion_humana=(
                            "Agregar la imagen correspondiente junto "
                            "a esta actividad en el documento y volver "
                            "a procesar la actividad."
                        ),
                    )
                )

        else:
            if self.estado in (
                "extraido",
                "requiere_recurso",
            ):
                self.estado = "listo_para_validar"

            self.incidencias = [
                incidencia
                for incidencia in self.incidencias
                if incidencia.codigo != codigo
            ]

        return self
    
class ParejaDragDrop(BaseModel):
    concepto: str

    definicion: str


class H5PDragAndDrop(ActividadH5P):
    h5p_tipo: Literal["drag_and_drop"] = "drag_and_drop"

    parejas: List[ParejaDragDrop] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def validar_parejas(self):
        if len(self.parejas) < 2:
            raise ValueError(
                "La actividad Drag and Drop debe contener "
                "al menos dos parejas."
            )

        conceptos = [
            pareja.concepto.strip().lower()
            for pareja in self.parejas
        ]

        if len(conceptos) != len(set(conceptos)):
            raise ValueError(
                "La actividad Drag and Drop contiene "
                "conceptos duplicados."
            )

        return self
    
class SituacionCoursePresentation(BaseModel):
    numero: int = Field(
        ge=1
    )

    situacion: str

    respuesta_correcta: str

    retroalimentacion: Optional[str] = None


class H5PCoursePresentation(ActividadH5P):
    h5p_tipo: Literal["course_presentation"] = "course_presentation"

    situaciones: List[SituacionCoursePresentation] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def validar_situaciones(self):
        if len(self.situaciones) < 1:
            raise ValueError(
                "La actividad Course Presentation debe contener "
                "al menos una situación."
            )

        numeros = [
            situacion.numero
            for situacion in self.situaciones
        ]

        if len(numeros) != len(set(numeros)):
            raise ValueError(
                "La actividad Course Presentation contiene "
                "números de situación duplicados."
            )

        return self
    
class EspacioEnBlanco(BaseModel):
    numero: int = Field(
        ge=1
    )

    respuestas_aceptadas: List[str]

    @model_validator(mode="after")
    def validar_respuestas(self):
        respuestas = [
            respuesta.strip()
            for respuesta in self.respuestas_aceptadas
            if respuesta.strip()
        ]

        if not respuestas:
            raise ValueError(
                "Un espacio en blanco debe tener "
                "al menos una respuesta aceptada."
            )

        if len(respuestas) != len(set(respuestas)):
            raise ValueError(
                "Un espacio en blanco contiene "
                "respuestas aceptadas duplicadas."
            )

        self.respuestas_aceptadas = respuestas

        return self


class H5PFillInTheBlanks(ActividadH5P):
    h5p_tipo: Literal["fill_in_the_blanks"] = "fill_in_the_blanks"

    texto: str

    espacios: List[EspacioEnBlanco] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def validar_espacios(self):
        if not self.espacios:
            raise ValueError(
                "La actividad Fill in the Blanks debe contener "
                "al menos un espacio en blanco."
            )

        numeros = [
            espacio.numero
            for espacio in self.espacios
        ]

        if len(numeros) != len(set(numeros)):
            raise ValueError(
                "La actividad Fill in the Blanks contiene "
                "números de espacio duplicados."
            )

        return self
    
class RetroalimentacionModulo(BaseModel):
    texto: str

    paginas_fuente: List[int] = Field(
        default_factory=list
    )


ActividadEvaluacion = Union[
    ActividadDesarrollo,
    ActividadDiscusion,
    H5PDragAndDrop,
    H5PCoursePresentation,
    H5PImageHotspots,
    H5PFillInTheBlanks,
    QuizModulo,
]


class ModuloAssessment(BaseModel):
    numero: int = Field(
        ge=1
    )

    titulo: str

    actividades: List[ActividadEvaluacion] = Field(
        default_factory=list
    )

    retroalimentacion_final: Optional[
        RetroalimentacionModulo
    ] = None


class AssessmentBlueprint(BaseModel):
    curso: str

    documento_fuente: str

    modulos: List[ModuloAssessment] = Field(
        default_factory=list
    )
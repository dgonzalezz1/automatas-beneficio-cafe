"""Caso de aplicación: control de lotes en un beneficio húmedo de café en Guatemala.

El proceso se modela con un autómata finito no determinista (AFND).

Alfabeto:
    1 = la etapa aprueba el control de calidad y el lote avanza
    0 = el lote no cumple el control de calidad y se envía a reproceso

El no determinismo aparece al terminar la fermentación y el lavado: un lote
aprobado (1) puede enviarse a secado al sol en patio o a secado mecánico en
guardiola, según la disponibilidad de patios y el clima del día.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from motor.finitos import AutomataFinito

SIGNIFICADO_SIMBOLOS = {
    "1": "Aprobado: el lote supera el control de calidad de la etapa",
    "0": "Reproceso: el lote no cumple el control de calidad",
}


@dataclass
class EjemploCadena:
    cadena: str
    descripcion: str


@dataclass
class Caso:
    titulo: str
    contexto: str
    significado_simbolos: dict[str, str]
    automata: AutomataFinito
    ejemplos: list[EjemploCadena]
    cadena_sugerida: str
    notas: list[str] = field(default_factory=list)


def afnd_beneficio() -> AutomataFinito:
    return AutomataFinito(
        estados=["q0", "q1", "q2", "q3", "q4", "q5"],
        alfabeto=["0", "1"],
        transiciones={
            "q0": {"1": ["q1"], "0": ["q0"]},
            "q1": {"1": ["q2"], "0": ["q0"]},
            "q2": {"1": ["q3", "q4"], "0": ["q1"]},
            "q3": {"1": ["q5"], "0": ["q4"]},
            "q4": {"1": ["q5"], "0": ["q4"]},
            "q5": {"1": ["q5"], "0": ["q5"]},
        },
        inicial="q0",
        finales={"q5"},
        descripciones={
            "q0": "Recepción y clasificación del café cereza",
            "q1": "Despulpado",
            "q2": "Fermentación y lavado",
            "q3": "Secado al sol en patio",
            "q4": "Secado mecánico en guardiola",
            "q5": "Trillado y empaque para exportación",
        },
    )


def caso_beneficio() -> Caso:
    return Caso(
        titulo="Control de lotes en un beneficio húmedo de café",
        contexto=(
            "Cada lote de café cereza recorre las etapas del beneficio húmedo. Al final de cada "
            "etapa se registra el resultado del control de calidad: 1 si el lote aprueba y 0 si "
            "debe reprocesarse. Al terminar la fermentación y el lavado, un lote aprobado puede "
            "enviarse a secado al sol en patio o a secado mecánico en guardiola; ese mismo evento "
            "con dos destinos posibles hace que el modelo sea no determinista. Si el clima impide "
            "terminar el secado al sol (0), el lote pasa a la guardiola. El lote es exportable "
            "cuando alcanza la etapa de trillado y empaque."
        ),
        significado_simbolos=SIGNIFICADO_SIMBOLOS,
        automata=afnd_beneficio(),
        ejemplos=[
            EjemploCadena("1111", "Lote sin reprocesos"),
            EjemploCadena("11101", "Secado al sol interrumpido por lluvia"),
            EjemploCadena("1110001", "Secado mecánico prolongado"),
            EjemploCadena("110111", "Reproceso en fermentación"),
            EjemploCadena("11001", "Lote devuelto a recepción"),
            EjemploCadena("111", "Lote todavía en secado"),
        ],
        cadena_sugerida="11101",
        notas=[
            "La simulación mantiene el conjunto de todas las etapas posibles del lote en cada paso.",
            "La cadena se acepta si al menos un camino termina en la etapa de trillado y empaque.",
        ],
    )

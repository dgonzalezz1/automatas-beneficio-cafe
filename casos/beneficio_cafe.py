"""Casos de aplicación: beneficio húmedo de café en Guatemala.

Convención del alfabeto en los autómatas finitos:
    1 = la etapa aprueba el control de calidad y el lote avanza
    0 = el lote no cumple el control y se envía a reproceso
"""

from __future__ import annotations

from dataclasses import dataclass, field

from motor.finitos import EPSILON, AutomataFinito
from motor.pila import AutomataPila, ReglaPila
from motor.turing import MaquinaTuring, ReglaTuring

SIGNIFICADO_BINARIO = {
    "1": "Aprobado: el lote supera el control de calidad y avanza",
    "0": "Reproceso: el lote no cumple el control de calidad",
}


@dataclass
class Caso:
    clave: str
    metodo: str
    titulo: str
    contexto: str
    significado_simbolos: dict[str, str]
    automata: object
    cadenas_ejemplo: list[str]
    cadena_sugerida: str
    notas: list[str] = field(default_factory=list)


def afd_flujo_normal() -> AutomataFinito:
    return AutomataFinito(
        estados=["q0", "q1", "q2", "q3", "q4"],
        alfabeto=["0", "1"],
        transiciones={
            "q0": {"1": ["q1"], "0": ["q0"]},
            "q1": {"1": ["q2"], "0": ["q0"]},
            "q2": {"1": ["q3"], "0": ["q1"]},
            "q3": {"1": ["q4"], "0": ["q2"]},
            "q4": {"1": ["q4"], "0": ["q4"]},
        },
        inicial="q0",
        finales={"q4"},
        descripciones={
            "q0": "Recepción y clasificación del café cereza",
            "q1": "Despulpado",
            "q2": "Fermentación y lavado",
            "q3": "Secado",
            "q4": "Trillado y empaque para exportación",
        },
    )


def afnd_secado() -> AutomataFinito:
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


def afnd_epsilon_lavado() -> AutomataFinito:
    return AutomataFinito(
        estados=["q0", "q1", "q2", "q3", "q4", "q5", "q6"],
        alfabeto=["0", "1"],
        transiciones={
            "q0": {"1": ["q1"], "0": ["q0"]},
            "q1": {"1": ["q2"], "0": ["q0"]},
            "q2": {"1": ["q3"], "0": ["q2"]},
            "q3": {EPSILON: ["q4"]},
            "q4": {"1": ["q5"], "0": ["q3"]},
            "q5": {"1": ["q6"], "0": ["q5"]},
            "q6": {"1": ["q6"], "0": ["q6"]},
        },
        inicial="q0",
        finales={"q6"},
        descripciones={
            "q0": "Recepción y clasificación del café cereza",
            "q1": "Despulpado",
            "q2": "Fermentación",
            "q3": "Lavado",
            "q4": "Escurrido (ocurre sin evento después del lavado)",
            "q5": "Secado",
            "q6": "Trillado y empaque para exportación",
        },
    )


def pila_bodega() -> AutomataPila:
    return AutomataPila(
        estados=["q0", "q1"],
        alfabeto=["0", "1"],
        simbolos_pila=["Z", "S"],
        reglas=[
            ReglaPila("q0", "1", "Z", "q1", "SZ"),
            ReglaPila("q1", "1", "S", "q1", "SS"),
            ReglaPila("q1", "0", "S", "q1", ""),
            ReglaPila("q1", EPSILON, "Z", "q0", "Z"),
        ],
        inicial="q0",
        simbolo_inicial_pila="Z",
        finales={"q0"},
        descripciones={
            "q0": "Bodega cuadrada: no hay sacos pendientes de despacho",
            "q1": "Bodega con sacos en existencia",
        },
    )


def turing_totalizador() -> MaquinaTuring:
    return MaquinaTuring(
        estados=["q0", "q1", "q2", "q3"],
        alfabeto=["0", "1"],
        reglas=[
            ReglaTuring("q0", "1", "q0", "1", "D"),
            ReglaTuring("q0", "0", "q1", "1", "D"),
            ReglaTuring("q1", "1", "q1", "1", "D"),
            ReglaTuring("q1", "_", "q2", "_", "I"),
            ReglaTuring("q2", "1", "q3", "_", "N"),
        ],
        inicial="q0",
        finales={"q3"},
        descripciones={
            "q0": "Recorre los sacos del primer turno",
            "q1": "Unió los turnos; recorre los sacos del segundo turno",
            "q2": "Llegó al final de la cinta; corrige el saco agregado",
            "q3": "Total de producción calculado",
        },
    )


METODOS = [
    "AFD",
    "AFND",
    "AFND-ε y conversión a AFD",
    "Lema de Arden",
    "Autómata de Pila",
    "Máquina de Turing",
]


def casos() -> list[Caso]:
    return [
        Caso(
            clave="afd",
            metodo="AFD",
            titulo="Flujo normal de un lote en el beneficio",
            contexto=(
                "Cada lote de café cereza recorre cinco etapas. Al final de cada etapa se "
                "registra el resultado del control de calidad. Con 1 el lote avanza; con 0 "
                "regresa a la etapa anterior para reproceso. El lote se considera exportable "
                "cuando alcanza la etapa de trillado y empaque."
            ),
            significado_simbolos=SIGNIFICADO_BINARIO,
            automata=afd_flujo_normal(),
            cadenas_ejemplo=["1111", "1101", "11011", "110111", "0111"],
            cadena_sugerida="110111",
        ),
        Caso(
            clave="afnd",
            metodo="AFND",
            titulo="Selección del tipo de secado",
            contexto=(
                "Cuando el lote aprueba la fermentación y el lavado, puede enviarse a secado "
                "al sol en patio o a secado mecánico en guardiola. El mismo evento (1) tiene "
                "dos destinos posibles, por lo que el modelo es no determinista. Si el clima "
                "impide el secado al sol (0), el lote pasa a la guardiola."
            ),
            significado_simbolos=SIGNIFICADO_BINARIO,
            automata=afnd_secado(),
            cadenas_ejemplo=["1111", "11101", "11001", "1110001"],
            cadena_sugerida="11101",
            notas=[
                "La simulación mantiene el conjunto de todas las etapas posibles en cada paso.",
                "La cadena se acepta si al menos un camino termina en la etapa de exportación.",
            ],
        ),
        Caso(
            clave="afnd_e",
            metodo="AFND-ε y conversión a AFD",
            titulo="Escurrido automático después del lavado",
            contexto=(
                "Después del lavado, el café pasa al escurrido sin que se registre ningún "
                "evento de control: es una transición ε. Para que la planta pueda automatizar "
                "el control, el modelo se convierte a un AFD equivalente mediante la "
                "cerradura ε y el método de subconjuntos."
            ),
            significado_simbolos=SIGNIFICADO_BINARIO,
            automata=afnd_epsilon_lavado(),
            cadenas_ejemplo=["11111", "111011", "1110111", "110111"],
            cadena_sugerida="1110111",
        ),
        Caso(
            clave="arden",
            metodo="Lema de Arden",
            titulo="Norma de calidad del proceso como expresión regular",
            contexto=(
                "A partir del AFD del flujo normal se plantea una ecuación por etapa. "
                "Resolviendo el sistema con el Lema de Arden se obtiene una expresión regular "
                "que describe todas las secuencias de controles con las que un lote llega a "
                "exportación. Esa expresión sirve como norma documentada del proceso."
            ),
            significado_simbolos=SIGNIFICADO_BINARIO,
            automata=afd_flujo_normal(),
            cadenas_ejemplo=["1111", "1101", "110111"],
            cadena_sugerida="110111",
        ),
        Caso(
            clave="pila",
            metodo="Autómata de Pila",
            titulo="Control de existencias en la bodega de café pergamino",
            contexto=(
                "Cada saco que ingresa a bodega se registra con 1 y cada saco despachado con 0. "
                "Un despacho sin existencia es un error, y al cierre del día la bodega debe "
                "quedar cuadrada. Un autómata finito no puede contar sacos sin límite; la pila "
                "guarda un símbolo S por cada saco en existencia."
            ),
            significado_simbolos={
                "1": "Ingreso de un saco a bodega",
                "0": "Despacho de un saco",
            },
            automata=pila_bodega(),
            cadenas_ejemplo=["1100", "101100", "1110000", "100", "0110"],
            cadena_sugerida="110100",
        ),
        Caso(
            clave="turing",
            metodo="Máquina de Turing",
            titulo="Totalizador de producción de dos turnos",
            contexto=(
                "La producción de cada turno se escribe en la cinta en notación unaria, un 1 "
                "por saco, y los turnos se separan con un 0. La máquina transforma la cinta "
                "hasta dejar un solo bloque de unos con el total del día."
            ),
            significado_simbolos={
                "1": "Un saco producido",
                "0": "Separador entre el primer y el segundo turno",
            },
            automata=turing_totalizador(),
            cadenas_ejemplo=["111011", "11011", "1111101"],
            cadena_sugerida="111011",
        ),
    ]


def caso_por_metodo(metodo: str) -> Caso:
    for caso in casos():
        if caso.metodo == metodo:
            return caso
    raise KeyError(metodo)


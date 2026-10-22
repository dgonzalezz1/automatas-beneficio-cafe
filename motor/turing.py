"""Máquina de Turing determinista apoyada en automata-lib."""

from __future__ import annotations

from dataclasses import dataclass, field

from automata.base.exceptions import RejectionException
from automata.tm.dtm import DTM

BLANCO = "_"
MOVIMIENTOS = {"D": "R", "I": "L", "N": "N"}
MOVIMIENTOS_VISIBLES = {"D": "Derecha", "I": "Izquierda", "N": "Sin mover"}


@dataclass
class ReglaTuring:
    estado: str
    lee: str
    siguiente: str
    escribe: str
    mueve: str  # D, I o N


@dataclass
class MaquinaTuring:
    estados: list[str]
    alfabeto: list[str]
    reglas: list[ReglaTuring]
    inicial: str
    finales: set[str]
    descripciones: dict[str, str] = field(default_factory=dict)

    def simbolos_cinta(self) -> set[str]:
        simbolos = set(self.alfabeto) | {BLANCO}
        for r in self.reglas:
            simbolos |= {r.lee, r.escribe}
        return simbolos

    def a_lib(self) -> DTM:
        transiciones: dict = {}
        for r in self.reglas:
            if r.mueve not in MOVIMIENTOS:
                raise ValueError(f"Movimiento inválido '{r.mueve}': use D, I o N.")
            por_estado = transiciones.setdefault(r.estado, {})
            if r.lee in por_estado:
                raise ValueError(f"Hay dos reglas para ({r.estado}, {r.lee}).")
            por_estado[r.lee] = (r.siguiente, r.escribe, MOVIMIENTOS[r.mueve])
        return DTM(
            states=set(self.estados),
            input_symbols=set(self.alfabeto),
            tape_symbols=self.simbolos_cinta(),
            transitions=transiciones,
            initial_state=self.inicial,
            blank_symbol=BLANCO,
            final_states=set(self.finales),
        )


@dataclass
class PasoTuring:
    numero: int
    estado: str
    cinta: list[str]
    posicion: int


@dataclass
class ResultadoTuring:
    aceptada: bool
    pasos: list[PasoTuring]
    salida: str
    motivo: str


def simular_turing(maquina: MaquinaTuring, cadena: str, limite: int = 500) -> ResultadoTuring:
    invalidos = sorted({c for c in cadena if c not in maquina.alfabeto})
    if invalidos:
        raise ValueError("La cadena contiene símbolos fuera del alfabeto: " + ", ".join(invalidos))

    dtm = maquina.a_lib()
    pasos: list[PasoTuring] = []
    aceptada = False
    motivo = ""
    try:
        for i, config in enumerate(dtm.read_input_stepwise(cadena or BLANCO)):
            pasos.append(
                PasoTuring(i, config.state, list(config.tape.tape), config.tape.current_position)
            )
            if i >= limite:
                motivo = f"La máquina superó {limite} pasos sin detenerse; se interrumpe la ejecución."
                break
        else:
            aceptada = True
    except RejectionException:
        ultimo = pasos[-1]
        simbolo = ultimo.cinta[ultimo.posicion] if 0 <= ultimo.posicion < len(ultimo.cinta) else BLANCO
        motivo = (
            f"La máquina se detuvo en {ultimo.estado} leyendo '{simbolo}', "
            "que no es un estado de aceptación."
        )

    salida = "".join(pasos[-1].cinta).strip(BLANCO) if pasos else ""
    if aceptada:
        motivo = f"La máquina se detuvo en el estado de aceptación {pasos[-1].estado}."
    return ResultadoTuring(aceptada, pasos, salida, motivo)


__all__ = ["MaquinaTuring", "ReglaTuring", "simular_turing", "BLANCO", "MOVIMIENTOS_VISIBLES"]

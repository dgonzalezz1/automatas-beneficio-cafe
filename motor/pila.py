"""Autómata de pila determinista apoyado en automata-lib.

Cada regla se escribe como una fila: estado, símbolo leído (vacío = λ),
tope de la pila, estado siguiente y cadena que se apila (vacía = desapilar).
La cadena que se apila se escribe con el nuevo tope a la izquierda, como en
la notación del curso: "SZ" deja S en el tope y Z debajo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from automata.base.exceptions import RejectionException
from automata.pda.dpda import DPDA

from .finitos import EPSILON


@dataclass
class ReglaPila:
    estado: str
    lee: str
    tope: str
    siguiente: str
    apila: str


@dataclass
class AutomataPila:
    estados: list[str]
    alfabeto: list[str]
    simbolos_pila: list[str]
    reglas: list[ReglaPila]
    inicial: str
    simbolo_inicial_pila: str
    finales: set[str]
    descripciones: dict[str, str] = field(default_factory=dict)

    def a_lib(self) -> DPDA:
        transiciones: dict = {}
        for r in self.reglas:
            por_lectura = transiciones.setdefault(r.estado, {}).setdefault(r.lee, {})
            if r.tope in por_lectura:
                raise ValueError(
                    f"Hay dos reglas para ({r.estado}, {r.lee or 'λ'}, {r.tope}); "
                    "el autómata de pila debe ser determinista."
                )
            # automata-lib espera la pila con el nuevo tope en la primera posición
            por_lectura[r.tope] = (r.siguiente, tuple(r.apila) if r.apila else "")
        return DPDA(
            states=set(self.estados),
            input_symbols=set(self.alfabeto),
            stack_symbols=set(self.simbolos_pila),
            transitions=transiciones,
            initial_state=self.inicial,
            initial_stack_symbol=self.simbolo_inicial_pila,
            final_states=set(self.finales),
            acceptance_mode="final_state",
        )


@dataclass
class PasoPila:
    numero: int
    estado: str
    leido: str
    restante: str
    pila: str  # tope a la izquierda


@dataclass
class ResultadoPila:
    aceptada: bool
    pasos: list[PasoPila]
    motivo: str


def simular_pila(automata: AutomataPila, cadena: str) -> ResultadoPila:
    invalidos = sorted({c for c in cadena if c not in automata.alfabeto})
    if invalidos:
        raise ValueError("La cadena contiene símbolos fuera del alfabeto: " + ", ".join(invalidos))

    maquina = automata.a_lib()
    pasos: list[PasoPila] = []
    anterior_restante = cadena
    try:
        for i, config in enumerate(maquina.read_input_stepwise(cadena)):
            restante = config.remaining_input
            leido = anterior_restante[: len(anterior_restante) - len(restante)] if i else ""
            if i and not leido:
                leido = "λ"
            pila = "".join(reversed(config.stack.stack))
            pasos.append(PasoPila(i, config.state, leido, restante or "λ", pila or "vacía"))
            anterior_restante = restante
        aceptada = True
    except RejectionException:
        aceptada = False

    if aceptada:
        motivo = (
            f"Se consumió toda la cadena y el autómata terminó en {pasos[-1].estado}, "
            "estado de aceptación."
        )
    else:
        ultimo = pasos[-1] if pasos else None
        if ultimo and ultimo.restante != "λ":
            motivo = (
                f"En {ultimo.estado} con tope {ultimo.pila[0]} no existe regla para leer "
                f"'{ultimo.restante[0]}'; la cadena se rechaza."
            )
        else:
            motivo = "Se consumió la cadena pero el autómata no quedó en un estado de aceptación."
    if aceptada != maquina.accepts_input(cadena):
        raise RuntimeError("La simulación no coincide con automata-lib.")
    return ResultadoPila(aceptada, pasos, motivo)


__all__ = ["AutomataPila", "ReglaPila", "simular_pila", "EPSILON"]

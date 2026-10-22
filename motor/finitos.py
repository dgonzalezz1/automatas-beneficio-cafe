"""Autómatas finitos: AFD, AFND y AFND-epsilon.

La simulación de aceptación se apoya en automata-lib. La cerradura epsilon y la
construcción por subconjuntos se calculan aquí de forma explícita para poder
mostrar cada paso del procedimiento en la interfaz.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from automata.fa.dfa import DFA
from automata.fa.nfa import NFA

EPSILON = ""
EPSILON_VISIBLE = "ε"


@dataclass
class AutomataFinito:
    """Definición formal (Q, Σ, δ, q0, F) de un autómata finito.

    ``transiciones[estado][simbolo]`` es una lista de estados destino. El símbolo
    vacío ``""`` representa una transición epsilon.
    """

    estados: list[str]
    alfabeto: list[str]
    transiciones: dict[str, dict[str, list[str]]]
    inicial: str
    finales: set[str]
    descripciones: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.validar()

    def validar(self) -> None:
        if not self.estados:
            raise ValueError("El autómata debe tener al menos un estado.")
        if not self.alfabeto:
            raise ValueError("El alfabeto no puede estar vacío.")
        if EPSILON in self.alfabeto:
            raise ValueError("El alfabeto no puede contener la cadena vacía.")
        if self.inicial not in self.estados:
            raise ValueError(f"El estado inicial {self.inicial} no pertenece a Q.")
        for final in self.finales:
            if final not in self.estados:
                raise ValueError(f"El estado final {final} no pertenece a Q.")
        for origen, por_simbolo in self.transiciones.items():
            if origen not in self.estados:
                raise ValueError(f"El estado {origen} no pertenece a Q.")
            for simbolo, destinos in por_simbolo.items():
                if simbolo != EPSILON and simbolo not in self.alfabeto:
                    raise ValueError(f"El símbolo '{simbolo}' no pertenece al alfabeto.")
                for destino in destinos:
                    if destino not in self.estados:
                        raise ValueError(f"El estado {destino} no pertenece a Q.")

    # Clasificación

    def tiene_epsilon(self) -> bool:
        return any(
            destinos for t in self.transiciones.values() for s, destinos in t.items() if s == EPSILON
        )

    def es_determinista(self) -> bool:
        if self.tiene_epsilon():
            return False
        return all(
            len(destinos) <= 1 for t in self.transiciones.values() for destinos in t.values()
        )

    def es_completo(self) -> bool:
        return self.es_determinista() and all(
            len(self.destinos(e, s)) == 1 for e in self.estados for s in self.alfabeto
        )

    def tipo(self) -> str:
        if self.tiene_epsilon():
            return "AFND-ε"
        return "AFD" if self.es_determinista() else "AFND"

    def destinos(self, estado: str, simbolo: str) -> list[str]:
        return list(self.transiciones.get(estado, {}).get(simbolo, []))

    # Conversión a automata-lib

    def a_afd_lib(self) -> DFA:
        if not self.es_determinista():
            raise ValueError("El autómata no es determinista.")
        transiciones = {
            e: {s: self.destinos(e, s)[0] for s in self.alfabeto if self.destinos(e, s)}
            for e in self.estados
        }
        return DFA(
            states=set(self.estados),
            input_symbols=set(self.alfabeto),
            transitions=transiciones,
            initial_state=self.inicial,
            final_states=set(self.finales),
            allow_partial=True,
        )

    def a_afnd_lib(self) -> NFA:
        transiciones = {
            e: {s: set(d) for s, d in self.transiciones.get(e, {}).items() if d}
            for e in self.estados
        }
        return NFA(
            states=set(self.estados),
            input_symbols=set(self.alfabeto),
            transitions=transiciones,
            initial_state=self.inicial,
            final_states=set(self.finales),
        )

    def acepta(self, cadena: str) -> bool:
        """Decide la pertenencia de la cadena usando automata-lib."""
        if self.es_determinista():
            return self.a_afd_lib().accepts_input(cadena)
        return self.a_afnd_lib().accepts_input(cadena)

    # Procedimientos explicados paso a paso

    def cerradura_epsilon(self, estados: set[str]) -> set[str]:
        """Conjunto de estados alcanzables usando solo transiciones epsilon."""
        cerradura = set(estados)
        pendientes = list(estados)
        while pendientes:
            actual = pendientes.pop()
            for destino in self.destinos(actual, EPSILON):
                if destino not in cerradura:
                    cerradura.add(destino)
                    pendientes.append(destino)
        return cerradura

    def mover(self, estados: set[str], simbolo: str) -> set[str]:
        return {d for e in estados for d in self.destinos(e, simbolo)}

    def ordenar(self, estados: set[str]) -> list[str]:
        return sorted(estados, key=self.estados.index)

    def nombre_conjunto(self, estados: set[str]) -> str:
        if not estados:
            return "∅"
        return "{" + ", ".join(self.ordenar(estados)) + "}"


@dataclass
class Paso:
    numero: int
    simbolo: str
    origen: str
    destino: str


@dataclass
class ResultadoSimulacion:
    aceptada: bool
    pasos: list
    recorrido: list
    motivo: str


def validar_cadena(automata: AutomataFinito, cadena: str) -> None:
    invalidos = sorted({c for c in cadena if c not in automata.alfabeto})
    if invalidos:
        raise ValueError(
            "La cadena contiene símbolos fuera del alfabeto: " + ", ".join(invalidos)
        )


def simular_afd(automata: AutomataFinito, cadena: str) -> ResultadoSimulacion:
    """Recorre la cadena símbolo por símbolo sobre un AFD."""
    validar_cadena(automata, cadena)
    if not automata.es_determinista():
        raise ValueError("Este método requiere un AFD: cada estado debe tener un solo destino por símbolo.")

    actual = automata.inicial
    pasos: list[Paso] = []
    recorrido = [actual]
    for i, simbolo in enumerate(cadena, start=1):
        destinos = automata.destinos(actual, simbolo)
        if not destinos:
            motivo = (
                f"No existe transición desde {actual} con el símbolo {simbolo}; "
                "la cadena se rechaza."
            )
            return ResultadoSimulacion(False, pasos, recorrido, motivo)
        siguiente = destinos[0]
        pasos.append(Paso(i, simbolo, actual, siguiente))
        recorrido.append(siguiente)
        actual = siguiente

    aceptada = actual in automata.finales
    if aceptada != automata.acepta(cadena):
        raise RuntimeError("La simulación no coincide con automata-lib.")
    motivo = (
        f"La cadena termina en {actual}, que es un estado de aceptación."
        if aceptada
        else f"La cadena termina en {actual}, que no es un estado de aceptación."
    )
    return ResultadoSimulacion(aceptada, pasos, recorrido, motivo)


@dataclass
class PasoNoDeterminista:
    numero: int
    simbolo: str
    origen: set[str]
    movimiento: set[str]
    destino: set[str]


def simular_afnd(automata: AutomataFinito, cadena: str) -> ResultadoSimulacion:
    """Mantiene el conjunto de estados activos, incluyendo la cerradura epsilon."""
    validar_cadena(automata, cadena)
    activos = automata.cerradura_epsilon({automata.inicial})
    recorrido = [activos]
    pasos: list[PasoNoDeterminista] = []
    for i, simbolo in enumerate(cadena, start=1):
        movimiento = automata.mover(activos, simbolo)
        siguientes = automata.cerradura_epsilon(movimiento)
        pasos.append(PasoNoDeterminista(i, simbolo, activos, movimiento, siguientes))
        recorrido.append(siguientes)
        activos = siguientes
        if not activos:
            break

    alcanzados_finales = activos & automata.finales
    aceptada = bool(alcanzados_finales) and len(pasos) == len(cadena)
    if aceptada != automata.acepta(cadena):
        raise RuntimeError("La simulación no coincide con automata-lib.")
    if not activos:
        motivo = "El conjunto de estados activos quedó vacío; ningún camino puede continuar."
    elif aceptada:
        motivo = (
            "Al terminar la cadena, el conjunto activo contiene el estado de aceptación "
            + ", ".join(automata.ordenar(alcanzados_finales))
            + "."
        )
    else:
        motivo = "Al terminar la cadena, ningún estado activo es de aceptación."
    return ResultadoSimulacion(aceptada, pasos, recorrido, motivo)


@dataclass
class FilaSubconjuntos:
    nombre: str
    conjunto: set[str]
    transiciones: dict[str, str]
    es_inicial: bool
    es_final: bool


def construccion_subconjuntos(
    automata: AutomataFinito,
) -> tuple[list[FilaSubconjuntos], AutomataFinito]:
    """Convierte un AFND o AFND-ε en un AFD equivalente por el método de subconjuntos.

    Devuelve la tabla del procedimiento y el AFD resultante. Los estados nuevos se
    nombran A, B, C... en el orden en que se descubren. El conjunto vacío solo
    aparece si algún estado no tiene transición, y se nombra "∅" como estado sumidero.
    """
    inicial = frozenset(automata.cerradura_epsilon({automata.inicial}))
    nombres: dict[frozenset, str] = {inicial: "A"}
    orden = [inicial]
    filas: list[FilaSubconjuntos] = []
    i = 0
    while i < len(orden):
        conjunto = orden[i]
        transiciones: dict[str, str] = {}
        for simbolo in automata.alfabeto:
            destino = frozenset(automata.cerradura_epsilon(automata.mover(set(conjunto), simbolo)))
            if destino not in nombres:
                nombres[destino] = "∅" if not destino else _nombre_letra(
                    len([n for n in nombres if n])
                )
                orden.append(destino)
            transiciones[simbolo] = nombres[destino]
        filas.append(
            FilaSubconjuntos(
                nombre=nombres[conjunto],
                conjunto=set(conjunto),
                transiciones=transiciones,
                es_inicial=conjunto == inicial,
                es_final=bool(set(conjunto) & automata.finales),
            )
        )
        i += 1

    estados = [f.nombre for f in filas]
    afd = AutomataFinito(
        estados=estados,
        alfabeto=list(automata.alfabeto),
        transiciones={f.nombre: {s: [d] for s, d in f.transiciones.items()} for f in filas},
        inicial="A",
        finales={f.nombre for f in filas if f.es_final},
        descripciones={f.nombre: automata.nombre_conjunto(f.conjunto) for f in filas},
    )

    referencia = DFA.from_nfa(automata.a_afnd_lib())
    if not _equivalentes(afd.a_afd_lib(), referencia):
        raise RuntimeError("El AFD construido no es equivalente al de automata-lib.")
    return filas, afd


def _nombre_letra(indice: int) -> str:
    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if indice < len(letras):
        return letras[indice]
    return letras[indice % len(letras)] + str(indice // len(letras))


def _equivalentes(a: DFA, b: DFA) -> bool:
    return a == b

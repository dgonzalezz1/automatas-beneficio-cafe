"""Obtención de la expresión regular de un autómata finito mediante el Lema de Arden.

Lema de Arden: si X = A·X + B y A no contiene la cadena vacía, la solución
única es X = A*·B.

Cada estado qi se asocia con una incógnita Xi que representa el lenguaje de
las cadenas que llevan de qi a un estado de aceptación:

    Xi = Σ a·Xj   (por cada transición qi --a--> qj)
         + λ      (si qi es de aceptación)

El sistema se resuelve eliminando incógnitas desde la última hasta la del
estado inicial. La solución de X0 es la expresión regular del autómata.
"""

from __future__ import annotations

from dataclasses import dataclass

from .finitos import EPSILON, AutomataFinito

LAMBDA = "λ"


# Expresiones regulares con simplificación algebraica básica


class Regex:
    precedencia = 3

    def texto(self, contexto: int = 0) -> str:
        t = self._texto()
        return f"({t})" if self.precedencia < contexto else t

    def _texto(self) -> str:  # pragma: no cover - abstracto
        raise NotImplementedError

    def __str__(self) -> str:
        return self.texto()

    def __eq__(self, otro: object) -> bool:
        return isinstance(otro, Regex) and str(self) == str(otro)

    def __hash__(self) -> int:
        return hash(str(self))


class Vacio(Regex):
    def _texto(self) -> str:
        return "∅"


class Lambda(Regex):
    def _texto(self) -> str:
        return LAMBDA


class Simbolo(Regex):
    def __init__(self, simbolo: str) -> None:
        self.simbolo = simbolo

    def _texto(self) -> str:
        return self.simbolo


class Union(Regex):
    precedencia = 1

    def __init__(self, partes: list[Regex]) -> None:
        self.partes = partes

    def _texto(self) -> str:
        return " + ".join(p.texto(1) for p in self.partes)


class Concat(Regex):
    precedencia = 2

    def __init__(self, partes: list[Regex]) -> None:
        self.partes = partes

    def _texto(self) -> str:
        return "".join(p.texto(2) for p in self.partes)


class Estrella(Regex):
    def __init__(self, base: Regex) -> None:
        self.base = base

    def _texto(self) -> str:
        return self.base.texto(3) + "*"


def union(*partes: Regex) -> Regex:
    planas: list[Regex] = []
    for p in partes:
        if isinstance(p, Vacio):
            continue
        for q in p.partes if isinstance(p, Union) else [p]:
            if q not in planas:
                planas.append(q)
    # λ + A·A* = A* y λ + A* = A*
    if any(isinstance(p, Lambda) for p in planas):
        for p in planas:
            if isinstance(p, Estrella):
                planas = [q for q in planas if not isinstance(q, Lambda)]
                break
    if not planas:
        return Vacio()
    if len(planas) == 1:
        return planas[0]
    planas.sort(key=lambda r: (isinstance(r, Lambda), str(r)))
    return Union(planas)


def concat(*partes: Regex) -> Regex:
    planas: list[Regex] = []
    for p in partes:
        if isinstance(p, Vacio):
            return Vacio()
        if isinstance(p, Lambda):
            continue
        planas.extend(p.partes if isinstance(p, Concat) else [p])
    # A*A* = A*
    reducidas: list[Regex] = []
    for p in planas:
        if reducidas and isinstance(p, Estrella) and p == reducidas[-1]:
            continue
        reducidas.append(p)
    if not reducidas:
        return Lambda()
    if len(reducidas) == 1:
        return reducidas[0]
    return Concat(reducidas)


def estrella(base: Regex) -> Regex:
    if isinstance(base, (Vacio, Lambda)):
        return Lambda()
    if isinstance(base, Estrella):
        return base
    return Estrella(base)


# Sistema de ecuaciones


@dataclass
class Ecuacion:
    """Xi = Σ coeficientes[j]·Xj + constante"""

    incognita: str
    coeficientes: dict[str, Regex]
    constante: Regex

    def texto(self) -> str:
        terminos = [
            f"{coef.texto(2)}{var}" if not isinstance(coef, Lambda) else var
            for var, coef in self.coeficientes.items()
            if not isinstance(coef, Vacio)
        ]
        if not isinstance(self.constante, Vacio):
            terminos.append(self.constante.texto(1))
        return f"{self.incognita} = " + (" + ".join(terminos) if terminos else "∅")

    def copia(self) -> "Ecuacion":
        return Ecuacion(self.incognita, dict(self.coeficientes), self.constante)


@dataclass
class PasoArden:
    titulo: str
    explicacion: str
    ecuaciones: list[str]


@dataclass
class ResultadoArden:
    ecuaciones_iniciales: list[str]
    pasos: list[PasoArden]
    expresion: str


def plantear_ecuaciones(automata: AutomataFinito) -> dict[str, Ecuacion]:
    if automata.tiene_epsilon():
        raise ValueError(
            "El Lema de Arden se aplica sobre un AFD o AFND sin transiciones ε. "
            "Convierta primero el AFND-ε a AFD."
        )
    variable = {e: f"X{i}" for i, e in enumerate(automata.estados)}
    ecuaciones: dict[str, Ecuacion] = {}
    for estado in automata.estados:
        coeficientes: dict[str, Regex] = {}
        for simbolo in automata.alfabeto:
            for destino in automata.destinos(estado, simbolo):
                var = variable[destino]
                coeficientes[var] = union(coeficientes.get(var, Vacio()), Simbolo(simbolo))
        constante: Regex = Lambda() if estado in automata.finales else Vacio()
        ecuaciones[variable[estado]] = Ecuacion(variable[estado], coeficientes, constante)
    return ecuaciones


def _aplicar_arden(ec: Ecuacion) -> tuple[Ecuacion, str | None]:
    """Elimina la recursión Xi = A·Xi + B  ->  Xi = A*·B."""
    a = ec.coeficientes.get(ec.incognita)
    if a is None or isinstance(a, Vacio):
        return ec, None
    a_estrella = estrella(a)
    nueva = Ecuacion(
        ec.incognita,
        {
            var: concat(a_estrella, coef)
            for var, coef in ec.coeficientes.items()
            if var != ec.incognita
        },
        concat(a_estrella, ec.constante),
    )
    explicacion = (
        f"{ec.incognita} aparece en ambos lados con A = {a}. "
        f"Por el Lema de Arden, {ec.incognita} = ({a})*·B."
    )
    return nueva, explicacion


def _sustituir(destino: Ecuacion, valor: Ecuacion) -> Ecuacion:
    """Reemplaza la incógnita de ``valor`` dentro de ``destino``."""
    coef = destino.coeficientes.get(valor.incognita)
    if coef is None:
        return destino
    nuevos = {v: c for v, c in destino.coeficientes.items() if v != valor.incognita}
    for var, c in valor.coeficientes.items():
        nuevos[var] = union(nuevos.get(var, Vacio()), concat(coef, c))
    constante = union(destino.constante, concat(coef, valor.constante))
    return Ecuacion(destino.incognita, nuevos, constante)


def resolver(automata: AutomataFinito) -> ResultadoArden:
    ecuaciones = plantear_ecuaciones(automata)
    iniciales = [e.texto() for e in ecuaciones.values()]
    pasos: list[PasoArden] = []
    inicial = "X0"
    orden = [v for v in ecuaciones if v != inicial][::-1]

    for var in orden:
        ec, explicacion = _aplicar_arden(ecuaciones[var])
        ecuaciones[var] = ec
        if explicacion:
            pasos.append(PasoArden(f"Resolver {var} con el Lema de Arden", explicacion, [ec.texto()]))
        afectadas = [
            otra for otra, e in ecuaciones.items() if otra != var and var in e.coeficientes
        ]
        for otra in afectadas:
            ecuaciones[otra] = _sustituir(ecuaciones[otra], ec)
        del ecuaciones[var]
        if afectadas:
            pasos.append(
                PasoArden(
                    f"Sustituir {var}",
                    f"Se reemplaza {var} en las ecuaciones de " + ", ".join(afectadas) + ".",
                    [ecuaciones[o].texto() for o in afectadas],
                )
            )

    final, explicacion = _aplicar_arden(ecuaciones[inicial])
    if explicacion:
        pasos.append(PasoArden(f"Resolver {inicial} con el Lema de Arden", explicacion, [final.texto()]))
    expresion = str(final.constante)
    pasos.append(
        PasoArden(
            "Resultado",
            "La solución de X0 es la expresión regular del lenguaje aceptado.",
            [f"X0 = {expresion}"],
        )
    )
    return ResultadoArden(iniciales, pasos, expresion)


def expresion_a_python(expresion: str) -> str:
    """Traduce la notación del curso a la sintaxis de expresiones regulares de Python."""
    if expresion == "∅":
        return r"(?!)"
    return expresion.replace(" + ", "|").replace(LAMBDA, "")


__all__ = ["resolver", "plantear_ecuaciones", "expresion_a_python", "ResultadoArden", "EPSILON"]

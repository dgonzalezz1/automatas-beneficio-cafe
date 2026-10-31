"""Generación de diagramas en lenguaje DOT (Graphviz).

La interfaz entrega el texto DOT a Streamlit, que lo dibuja en el navegador,
por lo que no se necesita instalar Graphviz en el equipo.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .finitos import EPSILON, EPSILON_VISIBLE, AutomataFinito

COLOR_PRINCIPAL = "#1F3A5F"
COLOR_RESALTE = "#9A6B12"
COLOR_TEXTO = "#1E1E1E"
COLOR_BORDE = "#4A4A4A"
COLOR_FONDO_ACTIVO = "#E8EEF5"


def _encabezado() -> list[str]:
    return [
        "digraph automata {",
        '  rankdir=LR; bgcolor="transparent";',
        f'  node [shape=circle fontname="Helvetica" fontsize=12 color="{COLOR_BORDE}" '
        f'fontcolor="{COLOR_TEXTO}" style=filled fillcolor="white" width=0.7 fixedsize=true];',
        f'  edge [fontname="Helvetica" fontsize=11 color="{COLOR_BORDE}" fontcolor="{COLOR_TEXTO}"];',
        '  __inicio [shape=point width=0.08 color="#4A4A4A"];',
    ]


def _nodo(estado: str, final: bool, activo: bool, etiqueta: str | None = None) -> str:
    atributos = [f'label="{etiqueta or estado}"']
    if final:
        atributos.append("shape=doublecircle")
    if activo:
        atributos.append(
            f'fillcolor="{COLOR_PRINCIPAL}" fontcolor="white" color="{COLOR_PRINCIPAL}" penwidth=2'
        )
    return f'  "{estado}" [{" ".join(atributos)}];'


def _aristas(
    etiquetas: dict[tuple[str, str], list[str]], resaltadas: set[tuple[str, str]]
) -> list[str]:
    lineas = []
    for (origen, destino), simbolos in etiquetas.items():
        etiqueta = ", ".join(simbolos)
        estilo = (
            f' color="{COLOR_RESALTE}" fontcolor="{COLOR_RESALTE}" penwidth=2.4'
            if (origen, destino) in resaltadas
            else ""
        )
        lineas.append(f'  "{origen}" -> "{destino}" [label="{etiqueta}"{estilo}];')
    return lineas


def dot_finito(
    automata: AutomataFinito,
    activos: Iterable[str] = (),
    resaltadas: Iterable[tuple[str, str]] = (),
) -> str:
    activos = set(activos)
    lineas = _encabezado()
    for estado in automata.estados:
        lineas.append(_nodo(estado, estado in automata.finales, estado in activos))
    lineas.append(f'  __inicio -> "{automata.inicial}";')

    etiquetas: dict[tuple[str, str], list[str]] = defaultdict(list)
    for origen in automata.estados:
        for simbolo, destinos in automata.transiciones.get(origen, {}).items():
            for destino in destinos:
                etiquetas[(origen, destino)].append(
                    EPSILON_VISIBLE if simbolo == EPSILON else simbolo
                )
    lineas += _aristas(etiquetas, set(resaltadas))
    lineas.append("}")
    return "\n".join(lineas)


__all__ = ["dot_finito"]

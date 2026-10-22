import re

import pytest

from casos.beneficio_cafe import (
    afd_flujo_normal,
    afnd_epsilon_lavado,
    afnd_secado,
    casos,
    clase_volkswagen_afd,
    clase_volkswagen_afnd,
    ejercicios_clase,
    pila_bodega,
    turing_totalizador,
)
from motor.arden import expresion_a_python, resolver
from motor.finitos import construccion_subconjuntos, simular_afd, simular_afnd
from motor.graficos import dot_finito, dot_pila, dot_turing
from motor.pila import simular_pila
from motor.turing import simular_turing


def todas_las_cadenas(alfabeto, largo_maximo):
    cadenas = [""]
    nivel = [""]
    for _ in range(largo_maximo):
        nivel = [c + s for c in nivel for s in alfabeto]
        cadenas += nivel
    return cadenas


@pytest.mark.parametrize(
    "cadena, esperado, recorrido",
    [
        ("1111", True, ["q0", "q1", "q2", "q3", "q4"]),
        ("1101", False, ["q0", "q1", "q2", "q0", "q1"]),
        ("1110", False, ["q0", "q1", "q2", "q3", "q0"]),
        ("01111", True, ["q0", "q4", "q4", "q4", "q4", "q4"]),
        ("11111", True, ["q0", "q1", "q2", "q3", "q4", "q4"]),
    ],
)
def test_ejercicio_de_clase(cadena, esperado, recorrido):
    resultado = simular_afd(clase_volkswagen_afd(), cadena)
    assert resultado.aceptada is esperado
    assert resultado.recorrido == recorrido


def test_afd_cafe():
    afd = afd_flujo_normal()
    assert afd.tipo() == "AFD" and afd.es_completo()
    assert simular_afd(afd, "110111").aceptada
    assert not simular_afd(afd, "11011").aceptada


def test_simbolo_fuera_del_alfabeto():
    with pytest.raises(ValueError):
        simular_afd(afd_flujo_normal(), "1121")


def test_afnd_cafe():
    afnd = afnd_secado()
    assert afnd.tipo() == "AFND"
    r = simular_afnd(afnd, "11101")
    assert r.aceptada
    assert r.recorrido[3] == {"q3", "q4"}
    assert not simular_afnd(afnd, "11001").aceptada


def test_afnd_epsilon_cerradura():
    a = afnd_epsilon_lavado()
    assert a.tipo() == "AFND-ε"
    assert a.cerradura_epsilon({"q3"}) == {"q3", "q4"}
    assert simular_afnd(a, "1110111").aceptada


@pytest.mark.parametrize(
    "automata", [afnd_secado(), afnd_epsilon_lavado(), clase_volkswagen_afnd()]
)
def test_subconjuntos_equivalente(automata):
    filas, afd = construccion_subconjuntos(automata)
    assert afd.tipo() == "AFD"
    for cadena in todas_las_cadenas(automata.alfabeto, 8):
        assert afd.acepta(cadena) == automata.acepta(cadena), cadena


@pytest.mark.parametrize(
    "automata",
    [afd_flujo_normal(), afnd_secado(), clase_volkswagen_afd(), clase_volkswagen_afnd()],
)
def test_arden_reconoce_el_mismo_lenguaje(automata):
    resultado = resolver(automata)
    patron = re.compile(expresion_a_python(resultado.expresion))
    for cadena in todas_las_cadenas(automata.alfabeto, 9):
        assert bool(patron.fullmatch(cadena)) == automata.acepta(cadena), (
            cadena,
            resultado.expresion,
        )


@pytest.mark.parametrize(
    "cadena, esperado",
    [("1100", True), ("101100", True), ("", True), ("100", False), ("0110", False), ("110", False)],
)
def test_pila_bodega(cadena, esperado):
    assert simular_pila(pila_bodega(), cadena).aceptada is esperado


@pytest.mark.parametrize("a, b", [(3, 2), (1, 1), (5, 1), (2, 4)])
def test_turing_suma(a, b):
    r = simular_turing(turing_totalizador(), "1" * a + "0" + "1" * b)
    assert r.aceptada
    assert r.salida == "1" * (a + b)


def test_turing_rechaza_sin_separador():
    assert not simular_turing(turing_totalizador(), "111").aceptada


def test_diagramas_y_casos():
    for caso in casos() + ejercicios_clase():
        assert caso.cadena_sugerida
    assert "doublecircle" in dot_finito(afd_flujo_normal(), activos={"q4"})
    assert "SZ" in dot_pila(pila_bodega())
    assert "q3" in dot_turing(turing_totalizador())

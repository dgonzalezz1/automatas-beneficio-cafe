import pytest

from casos.beneficio_cafe import afnd_beneficio, caso_beneficio
from motor.finitos import AutomataFinito, construccion_subconjuntos, simular_afd, simular_afnd
from motor.graficos import dot_finito


def todas_las_cadenas(alfabeto, largo_maximo):
    cadenas = [""]
    nivel = [""]
    for _ in range(largo_maximo):
        nivel = [c + s for c in nivel for s in alfabeto]
        cadenas += nivel
    return cadenas


def test_el_caso_es_un_afnd():
    afnd = afnd_beneficio()
    assert afnd.tipo() == "AFND"
    assert afnd.destinos("q2", "1") == ["q3", "q4"]


@pytest.mark.parametrize(
    "cadena, recorrido, esperado",
    [
        ("1111", [{"q0"}, {"q1"}, {"q2"}, {"q3", "q4"}, {"q5"}], True),
        ("11101", [{"q0"}, {"q1"}, {"q2"}, {"q3", "q4"}, {"q4"}, {"q5"}], True),
        ("11001", [{"q0"}, {"q1"}, {"q2"}, {"q1"}, {"q0"}, {"q1"}], False),
        ("111", [{"q0"}, {"q1"}, {"q2"}, {"q3", "q4"}], False),
    ],
)
def test_recorrido_por_conjuntos(cadena, recorrido, esperado):
    r = simular_afnd(afnd_beneficio(), cadena)
    assert r.recorrido == recorrido
    assert r.aceptada is esperado


def test_ejemplos_del_caso_coinciden_con_su_descripcion():
    caso = caso_beneficio()
    aceptadas = {e.cadena for e in caso.ejemplos if caso.automata.acepta(e.cadena)}
    assert aceptadas == {"1111", "11101", "1110001", "110111"}
    assert caso.automata.acepta(caso.cadena_sugerida)


def test_simbolo_fuera_del_alfabeto():
    with pytest.raises(ValueError):
        simular_afnd(afnd_beneficio(), "1121")


def test_conjunto_vacio_rechaza():
    afnd = AutomataFinito(
        estados=["q0", "q1"], alfabeto=["0", "1"],
        transiciones={"q0": {"1": ["q0", "q1"]}}, inicial="q0", finales={"q1"},
    )
    r = simular_afnd(afnd, "10")
    assert not r.aceptada
    assert r.recorrido[-1] == set()


def test_subconjuntos_del_caso():
    filas, afd = construccion_subconjuntos(afnd_beneficio())
    assert [(f.nombre, sorted(f.conjunto)) for f in filas] == [
        ("A", ["q0"]), ("B", ["q1"]), ("C", ["q2"]), ("D", ["q3", "q4"]), ("E", ["q4"]), ("F", ["q5"]),
    ]
    assert afd.finales == {"F"}


def test_afd_equivalente_reconoce_el_mismo_lenguaje():
    afnd = afnd_beneficio()
    _, afd = construccion_subconjuntos(afnd)
    for cadena in todas_las_cadenas(afnd.alfabeto, 9):
        assert simular_afd(afd, cadena).aceptada == simular_afnd(afnd, cadena).aceptada, cadena


def test_diagrama():
    dot = dot_finito(afnd_beneficio(), activos={"q3", "q4"})
    assert "doublecircle" in dot and '"q2" -> "q3"' in dot and '"q2" -> "q4"' in dot

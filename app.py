"""Simulador de un autómata finito no determinista (AFND) aplicado al beneficio húmedo de café.

Ejecución:  streamlit run app.py
"""

from __future__ import annotations

import html
import time

import pandas as pd
import streamlit as st
from automata.base.exceptions import AutomatonException

from casos.beneficio_cafe import caso_beneficio
from motor.finitos import AutomataFinito, construccion_subconjuntos, simular_afd, simular_afnd
from motor.graficos import dot_finito

MODO_CASO = "Caso de estudio: beneficio de café"
MODO_MANUAL = "Autómata personalizado"

st.set_page_config(
    page_title="Simulador AFND | Beneficio de Café",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    #MainMenu, footer {visibility: hidden;}
    .block-container {padding-top: 1.4rem; max-width: 1200px;}
    h2, h3 {color: #1F3A5F; font-weight: 600;}

    .banda {background: linear-gradient(120deg, #1F3A5F 0%, #2E4F7A 60%, #3B6191 100%);
        color: #FFFFFF; border-radius: 10px; padding: 1.6rem 2rem 1.4rem 2rem; margin-bottom: 1.4rem;}
    .banda .institucion {font-size: 0.78rem; letter-spacing: 0.12em; text-transform: uppercase;
        opacity: 0.85;}
    .banda .titulo {font-size: 2rem; font-weight: 700; margin: 0.35rem 0 0.2rem 0; line-height: 1.2;}
    .banda .subtitulo {font-size: 1.05rem; opacity: 0.92;}
    .banda .etiqueta-metodo {display: inline-block; margin-top: 0.8rem; padding: 0.2rem 0.75rem;
        border: 1px solid rgba(255,255,255,0.55); border-radius: 999px; font-size: 0.8rem;
        letter-spacing: 0.06em;}

    .tarjetas {display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 0.8rem; margin: 0.4rem 0 1rem 0;}
    .tarjeta {background: #FFFFFF; border: 1px solid #DDE3EA; border-radius: 8px;
        padding: 0.8rem 1rem; box-shadow: 0 1px 2px rgba(31,58,95,0.06);}
    .tarjeta .rotulo {font-size: 0.75rem; color: #5A6573; text-transform: uppercase;
        letter-spacing: 0.08em;}
    .tarjeta .valor {font-size: 1.35rem; font-weight: 600; color: #1F3A5F; margin-top: 0.2rem;
        word-break: break-all;}

    .resultado {border-radius: 8px; padding: 1rem 1.2rem; margin: 0.4rem 0 1.2rem 0;
        border: 1px solid; display: flex; gap: 1rem; align-items: center;}
    .resultado .sello {font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
        padding: 0.45rem 0.9rem; border-radius: 6px; color: #FFFFFF; white-space: nowrap;}
    .resultado.aceptada {background: #F1F7F2; border-color: #B9D3BF; color: #1F3F27;}
    .resultado.aceptada .sello {background: #2E5E3A;}
    .resultado.rechazada {background: #FAF1F1; border-color: #E2BDBD; color: #4F1E1E;}
    .resultado.rechazada .sello {background: #7A2E2E;}
    .resultado.invalido {background: #FBF6EC; border-color: #E5D3A8; color: #5A4310;}
    .resultado.invalido .sello {background: #8A6A1F;}

    .linea {display: flex; flex-wrap: wrap; align-items: center; gap: 0.35rem; margin: 0.6rem 0 1rem 0;}
    .conjunto {border: 1px solid #1F3A5F; color: #1F3A5F; border-radius: 6px; padding: 0.25rem 0.55rem;
        font-family: "Cambria Math", "Times New Roman", serif; font-size: 0.95rem; background: #FFFFFF;}
    .conjunto.actual {background: #1F3A5F; color: #FFFFFF;}
    .conjunto.vacio {border-color: #7A2E2E; color: #7A2E2E;}
    .flecha {color: #9A6B12; font-size: 0.85rem; font-weight: 600;}

    .etapas {display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.2rem 0 0.8rem 0;}
    .etapa {background: #E8EEF5; border-left: 4px solid #1F3A5F; border-radius: 4px;
        padding: 0.35rem 0.7rem; font-size: 0.9rem; color: #1E1E1E;}
    .etapa b {color: #1F3A5F;}

    .formal {background: #F7F9FB; border: 1px solid #DDE3EA; border-radius: 8px; padding: 1rem 1.2rem;
        font-family: "Cambria Math", "Times New Roman", serif; font-size: 1.05rem; line-height: 1.8;}
    .pie {margin-top: 2.5rem; padding-top: 0.8rem; border-top: 1px solid #DDE3EA; font-size: 0.8rem;
        color: #5A6573;}
    </style>
    """,
    unsafe_allow_html=True,
)


# Componentes de presentación


def tarjetas(datos: list[tuple[str, str]]) -> None:
    celdas = "".join(
        f'<div class="tarjeta"><div class="rotulo">{html.escape(r)}</div>'
        f'<div class="valor">{html.escape(v)}</div></div>'
        for r, v in datos
    )
    st.markdown(f'<div class="tarjetas">{celdas}</div>', unsafe_allow_html=True)


def resultado(clase: str, sello: str, texto: str) -> None:
    st.markdown(
        f'<div class="resultado {clase}"><span class="sello">{sello}</span>'
        f"<span>{html.escape(texto)}</span></div>",
        unsafe_allow_html=True,
    )


def tabla(filas: list[dict]) -> None:
    if filas:
        st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")


def conjunto(automata: AutomataFinito, estados: set[str]) -> str:
    return automata.nombre_conjunto(estados)


# Definición del autómata


def editor_afnd() -> AutomataFinito | None:
    st.markdown("### Definición del autómata")
    st.caption(
        "Indique el número de nodos y el alfabeto, y escriba en cada celda el estado o los estados "
        "destino separados por comas. Deje vacía la celda si no hay transición. El estado inicial es q0."
    )
    c1, c2 = st.columns(2)
    n = int(c1.number_input("Número de nodos", min_value=1, max_value=12, value=4))
    alfabeto = [s.strip() for s in c2.text_input("Alfabeto (separado por comas)", value="0, 1").split(",") if s.strip()]
    if not alfabeto or any(len(s) != 1 for s in alfabeto) or len(set(alfabeto)) != len(alfabeto):
        resultado("invalido", "Dato inválido", "Cada símbolo del alfabeto debe ser un solo carácter y no repetirse.")
        return None
    estados = [f"q{i}" for i in range(n)]
    base = pd.DataFrame(
        [{"Estado": e, "Descripción": "", **{s: "" for s in alfabeto}, "Aceptación": i == n - 1}
         for i, e in enumerate(estados)]
    )
    editada = st.data_editor(
        base, hide_index=True, width="stretch", disabled=["Estado"], key=f"tabla_{n}_{''.join(alfabeto)}",
    )
    transiciones = {}
    for _, fila in editada.iterrows():
        transiciones[fila["Estado"]] = {
            s: [d.strip() for d in str(fila[s] or "").split(",") if d.strip()]
            for s in alfabeto
            if str(fila[s] or "").strip()
        }
    try:
        return AutomataFinito(
            estados=estados,
            alfabeto=alfabeto,
            transiciones=transiciones,
            inicial="q0",
            finales={f["Estado"] for _, f in editada.iterrows() if f["Aceptación"]},
            descripciones={f["Estado"]: f["Descripción"] for _, f in editada.iterrows() if f["Descripción"]},
        )
    except ValueError as e:
        resultado("invalido", "Dato inválido", str(e))
        return None


# Barra lateral

with st.sidebar:
    st.markdown("### Configuración")
    modo = st.radio("Modo de análisis", [MODO_CASO, MODO_MANUAL])
    st.divider()
    st.markdown("**Método de solución**")
    st.markdown("Autómata finito no determinista (AFND)")
    st.caption(
        "El AFND admite varios destinos para un mismo símbolo. La cadena se acepta si al menos "
        "un camino termina en un estado de aceptación."
    )


# Encabezado

st.markdown(
    """
    <div class="banda">
      <div class="institucion">Universidad Mariano Gálvez de Guatemala · Autómatas y Lenguajes Formales</div>
      <div class="titulo">Simulador de Autómata Finito No Determinista</div>
      <div class="subtitulo">Control de lotes en un beneficio húmedo de café en Guatemala</div>
      <span class="etiqueta-metodo">MÉTODO DE SOLUCIÓN: AFND</span>
    </div>
    """,
    unsafe_allow_html=True,
)


# Modelo

caso = caso_beneficio() if modo == MODO_CASO else None
if caso:
    automata = caso.automata
else:
    automata = editor_afnd()
    if automata is None:
        st.stop()

# Parámetros de análisis

st.markdown("### Parámetros de análisis")
clave_cadena = f"cadena_{modo}"
if clave_cadena not in st.session_state:
    st.session_state[clave_cadena] = caso.cadena_sugerida if caso else ""

if caso:
    def _usar_ejemplo() -> None:
        elegido = st.session_state.get("ejemplo")
        if elegido:
            st.session_state[clave_cadena] = elegido

    st.pills(
        "Cadenas de ejemplo",
        [e.cadena for e in caso.ejemplos],
        format_func=lambda c: f"{c}  ·  {next(e.descripcion for e in caso.ejemplos if e.cadena == c)}",
        key="ejemplo",
        on_change=_usar_ejemplo,
    )

col_cadena, _ = st.columns([2, 3])
cadena = col_cadena.text_input("Cadena a analizar", key=clave_cadena).strip()

tarjetas([
    ("Número de nodos", str(len(automata.estados))),
    ("Alfabeto", "{" + ", ".join(automata.alfabeto) + "}"),
    ("Cadena a analizar", cadena or "λ (vacía)"),
    ("Método de solución", "AFND"),
])

try:
    simulacion = simular_afnd(automata, cadena)
except (ValueError, AutomatonException) as e:
    resultado("invalido", "Dato inválido", str(e))
    st.stop()

if simulacion.aceptada:
    resultado("aceptada", "Cadena aceptada", simulacion.motivo)
else:
    resultado("rechazada", "Cadena rechazada", simulacion.motivo)


pestanas = st.tabs(
    ["Recorrido de la cadena", "Definición formal", "Equivalencia con AFD"]
    + (["Caso de estudio"] if caso else [])
)

# Recorrido

with pestanas[0]:
    total = len(simulacion.pasos)
    c1, c2 = st.columns([4, 1])
    paso = c1.slider("Paso del recorrido", 0, total, total, key=f"paso_{cadena}") if total else 0
    reproducir = c2.button("Reproducir recorrido", width="stretch")
    lienzo = st.empty()

    def dibujar(k: int) -> None:
        activos = simulacion.recorrido[k]
        resaltadas: set[tuple[str, str]] = set()
        if k:
            p = simulacion.pasos[k - 1]
            resaltadas = {(o, d) for o in p.origen for d in automata.destinos(o, p.simbolo)}
        with lienzo.container():
            st.graphviz_chart(dot_finito(automata, activos, resaltadas), width="content")
            piezas = []
            for i, estados in enumerate(simulacion.recorrido):
                if i:
                    piezas.append(f'<span class="flecha">{html.escape(simulacion.pasos[i - 1].simbolo)} →</span>')
                clase = "conjunto" + (" actual" if i == k else "") + (" vacio" if not estados else "")
                piezas.append(f'<span class="{clase}">{html.escape(conjunto(automata, estados))}</span>')
            st.markdown(f'<div class="linea">{"".join(piezas)}</div>', unsafe_allow_html=True)
            if activos:
                etapas = "".join(
                    f'<span class="etapa"><b>{e}</b> {html.escape(automata.descripciones.get(e, ""))}</span>'
                    for e in automata.ordenar(activos)
                )
                st.markdown(
                    f"**Etapas posibles del lote en el paso {k}**<div class='etapas'>{etapas}</div>",
                    unsafe_allow_html=True,
                )

    if reproducir:
        for k in range(len(simulacion.recorrido)):
            dibujar(k)
            time.sleep(0.9)
    else:
        dibujar(min(paso, len(simulacion.recorrido) - 1))

    filas = [{"Paso": 0, "Entrada": "—", "Desde": "—", "Estados activos": conjunto(automata, simulacion.recorrido[0])}]
    filas += [
        {"Paso": p.numero, "Entrada": p.simbolo,
         "Desde": conjunto(automata, p.origen), "Estados activos": conjunto(automata, p.destino)}
        for p in simulacion.pasos
    ]
    st.markdown("**Tabla de recorrido**")
    tabla(filas)

# Definición formal

with pestanas[1]:
    st.markdown(
        f"""<div class="formal">
        M = (Q, Σ, δ, q<sub>0</sub>, F)<br>
        Q = {{{", ".join(automata.estados)}}}<br>
        Σ = {{{", ".join(automata.alfabeto)}}}<br>
        q<sub>0</sub> = {automata.inicial}<br>
        F = {{{", ".join(automata.ordenar(automata.finales))}}}<br>
        δ : Q × Σ → P(Q)
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown("**Matriz de transición** (→ estado inicial, * estado de aceptación)")
    filas = []
    for e in automata.estados:
        fila = {"Estado": ("→ " if e == automata.inicial else "") + ("* " if e in automata.finales else "") + e}
        for s in automata.alfabeto:
            fila[f"δ(·, {s})"] = conjunto(automata, set(automata.destinos(e, s)))
        if automata.descripciones.get(e):
            fila["Etapa"] = automata.descripciones[e]
        filas.append(fila)
    tabla(filas)
    no_det = [
        f"δ({e}, {s}) = {conjunto(automata, set(automata.destinos(e, s)))}"
        for e in automata.estados for s in automata.alfabeto if len(automata.destinos(e, s)) > 1
    ]
    if no_det:
        st.markdown("**Transiciones no deterministas:** " + ";  ".join(no_det))
    else:
        st.caption("Este autómata no tiene transiciones con más de un destino; se comporta como un AFD.")

# Equivalencia con AFD

with pestanas[2]:
    st.write(
        "Todo AFND tiene un AFD equivalente. Por el método de subconjuntos, cada estado del AFD "
        "representa un conjunto de estados del AFND."
    )
    try:
        filas_sub, afd = construccion_subconjuntos(automata)
    except (ValueError, RuntimeError, AutomatonException) as e:
        resultado("invalido", "Dato inválido", str(e))
    else:
        tabla([
            {"Estado AFD": ("→ " if f.es_inicial else "") + ("* " if f.es_final else "") + f.nombre,
             "Conjunto del AFND": conjunto(automata, f.conjunto),
             **{f"Con {s}": f.transiciones[s] for s in automata.alfabeto}}
            for f in filas_sub
        ])
        st.graphviz_chart(dot_finito(afd), width="content")
        r = simular_afd(afd, cadena)
        st.markdown(
            f"**Comprobación:** en el AFD equivalente, la cadena recorre {', '.join(r.recorrido)} y "
            f"resulta {'aceptada' if r.aceptada else 'rechazada'}, igual que en el AFND."
        )

# Caso de estudio

if caso:
    with pestanas[3]:
        st.markdown(f"#### {caso.titulo}")
        st.write(caso.contexto)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Estados: etapas del proceso**")
            tabla([{"Estado": e, "Etapa": d} for e, d in automata.descripciones.items()])
        with c2:
            st.markdown("**Alfabeto: eventos registrados**")
            tabla([{"Símbolo": s, "Significado": d} for s, d in caso.significado_simbolos.items()])
            st.markdown("**Cadenas de ejemplo**")
            tabla([{"Cadena": e.cadena, "Situación": e.descripcion,
                    "Resultado": "Aceptada" if automata.acepta(e.cadena) else "Rechazada"}
                   for e in caso.ejemplos])
        for nota in caso.notas:
            st.caption(nota)

st.markdown(
    '<div class="pie">Proyecto final · Autómatas y Lenguajes Formales · Universidad Mariano Gálvez de Guatemala</div>',
    unsafe_allow_html=True,
)

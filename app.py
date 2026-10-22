"""Simulador de autómatas aplicado al beneficio húmedo de café.

Ejecución:  streamlit run app.py
"""

from __future__ import annotations

import re
import time

import pandas as pd
import streamlit as st
from automata.base.exceptions import AutomatonException

from casos.beneficio_cafe import METODOS, Caso, caso_por_metodo, ejercicios_clase
from motor.arden import expresion_a_python, resolver
from motor.finitos import (
    EPSILON,
    EPSILON_VISIBLE,
    AutomataFinito,
    construccion_subconjuntos,
    simular_afd,
    simular_afnd,
)
from motor.graficos import dot_finito, dot_pila, dot_turing
from motor.pila import AutomataPila, ReglaPila, simular_pila
from motor.turing import BLANCO, MOVIMIENTOS_VISIBLES, MaquinaTuring, ReglaTuring, simular_turing

ORIGEN_CASO = "Caso de aplicación: beneficio de café"
ORIGEN_CLASE = "Ejercicio de clase"
ORIGEN_MANUAL = "Definición manual"

st.set_page_config(
    page_title="Simulador de Autómatas | Beneficio de Café",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    #MainMenu, footer {visibility: hidden;}
    .block-container {padding-top: 2rem; max-width: 1200px;}
    h1, h2, h3 {color: #1F3A5F; font-weight: 600;}
    .encabezado {border-bottom: 2px solid #1F3A5F; padding-bottom: 0.6rem; margin-bottom: 1.2rem;}
    .encabezado .institucion {font-size: 0.85rem; color: #5A5A5A; letter-spacing: 0.04em;
        text-transform: uppercase;}
    .encabezado .titulo {font-size: 1.9rem; font-weight: 600; color: #1F3A5F; margin: 0.2rem 0;}
    .encabezado .subtitulo {font-size: 1.05rem; color: #3A3A3A;}
    .resultado {padding: 0.9rem 1.1rem; border-radius: 4px; margin: 0.6rem 0 1rem 0;
        border-left: 5px solid; font-size: 1rem;}
    .resultado.aceptada {background: #EEF4EE; border-color: #2E5E3A; color: #1F3F27;}
    .resultado.rechazada {background: #F7EEEE; border-color: #7A2E2E; color: #4F1E1E;}
    .resultado .etiqueta {font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;}
    .formal {font-family: "Cambria Math", "Times New Roman", serif; font-size: 1.05rem;}
    .cinta {display: flex; gap: 2px; margin: 0.4rem 0 1rem 0; flex-wrap: wrap;}
    .celda {width: 2.2rem; height: 2.2rem; border: 1px solid #4A4A4A; display: flex;
        align-items: center; justify-content: center; font-family: monospace; font-size: 1.1rem;}
    .celda.cabezal {background: #1F3A5F; color: white; border-color: #1F3A5F;}
    .pila {display: inline-flex; flex-direction: column; gap: 2px; margin: 0.4rem 0;}
    .pila .celda {width: 3rem;}
    .pila .celda.tope {background: #1F3A5F; color: white;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="encabezado">
      <div class="institucion">Universidad Mariano Gálvez de Guatemala · Autómatas y Lenguajes Formales</div>
      <div class="titulo">Simulador de Autómatas</div>
      <div class="subtitulo">Aplicación al proceso de beneficio húmedo de café en Guatemala</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# Utilidades de presentación


def mostrar_resultado(aceptada: bool, motivo: str) -> None:
    clase = "aceptada" if aceptada else "rechazada"
    texto = "Cadena aceptada" if aceptada else "Cadena rechazada"
    st.markdown(
        f'<div class="resultado {clase}"><span class="etiqueta">{texto}.</span> {motivo}</div>',
        unsafe_allow_html=True,
    )


def mostrar_error(mensaje: str) -> None:
    st.markdown(
        f'<div class="resultado rechazada"><span class="etiqueta">Dato inválido.</span> '
        f"{mensaje}</div>",
        unsafe_allow_html=True,
    )


def tabla(filas: list[dict]) -> None:
    if not filas:
        st.caption("La cadena está vacía; no hay pasos que mostrar.")
        return
    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")


def mostrar_contexto(caso: Caso, descripciones: dict[str, str]) -> None:
    st.subheader(caso.titulo)
    st.write(caso.contexto)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Estados (etapas del proceso)**")
        tabla([{"Estado": e, "Etapa": d} for e, d in descripciones.items()])
    with col2:
        st.markdown("**Alfabeto (eventos registrados)**")
        tabla([{"Símbolo": s, "Significado": d} for s, d in caso.significado_simbolos.items()])
        st.markdown("**Cadenas de ejemplo:** " + ", ".join(caso.cadenas_ejemplo))
    for nota in caso.notas:
        st.caption(nota)


def parametros(numero_nodos: int, alfabeto: list[str], metodo: str, clave: str, sugerida: str):
    """Los cuatro parámetros que solicita el enunciado del proyecto."""
    st.markdown("### Parámetros de análisis")
    c1, c2, c3, c4 = st.columns([1, 1, 1.4, 1.6])
    c1.metric("Número de nodos", numero_nodos)
    c2.metric("Alfabeto", "{" + ", ".join(alfabeto) + "}")
    cadena = c3.text_input("Cadena a analizar", value=sugerida, key=f"cadena_{clave}")
    c4.markdown(
        f"<div style='font-size:0.875rem'>Método de solución</div>"
        f"<div style='font-size:1.35rem; padding-top:0.45rem'>{metodo}</div>",
        unsafe_allow_html=True,
    )
    return cadena.strip()


def definicion_formal(estados, alfabeto, inicial, finales, extra: str = "") -> None:
    st.markdown("### Definición formal")
    st.markdown(
        f"""<div class="formal">
        Q = {{{", ".join(estados)}}}<br>
        Σ = {{{", ".join(alfabeto)}}}<br>
        q<sub>0</sub> = {inicial}<br>
        F = {{{", ".join(sorted(finales))}}}{extra}
        </div>""",
        unsafe_allow_html=True,
    )


def matriz_transicion(automata: AutomataFinito) -> None:
    simbolos = list(automata.alfabeto) + ([EPSILON] if automata.tiene_epsilon() else [])
    filas = []
    for estado in automata.estados:
        marca = ("→ " if estado == automata.inicial else "") + ("* " if estado in automata.finales else "")
        fila = {"Estado": marca + estado}
        for s in simbolos:
            destinos = automata.destinos(estado, s)
            nombre = EPSILON_VISIBLE if s == EPSILON else s
            fila[f"δ(·, {nombre})"] = automata.nombre_conjunto(set(destinos)) if len(destinos) != 1 else destinos[0]
            if not destinos:
                fila[f"δ(·, {nombre})"] = "—"
        if automata.descripciones.get(estado):
            fila["Etapa"] = automata.descripciones[estado]
        filas.append(fila)
    st.markdown("**Matriz de función de transición** (→ estado inicial, * estado de aceptación)")
    tabla(filas)


def control_pasos(total: int, clave: str):
    c1, c2 = st.columns([4, 1])
    paso = c1.slider("Paso del recorrido", 0, total, total, key=f"paso_{clave}") if total else 0
    reproducir = c2.button("Reproducir recorrido", key=f"play_{clave}", width="content")
    return paso, st.empty(), reproducir


# Editor de autómatas finitos


def editor_finito(metodo: str, permite_epsilon: bool) -> AutomataFinito | None:
    st.markdown("### Definición del autómata")
    c1, c2 = st.columns(2)
    n = c1.number_input("Número de nodos", min_value=1, max_value=15, value=4, key=f"n_{metodo}")
    alfabeto_txt = c2.text_input("Alfabeto (símbolos separados por comas)", value="0, 1", key=f"alf_{metodo}")
    alfabeto = [s.strip() for s in alfabeto_txt.split(",") if s.strip()]
    if any(len(s) != 1 for s in alfabeto):
        mostrar_error("Cada símbolo del alfabeto debe ser un solo carácter.")
        return None
    estados = [f"q{i}" for i in range(int(n))]
    columnas = alfabeto + ([EPSILON_VISIBLE] if permite_epsilon else [])
    base = pd.DataFrame(
        [{"Estado": e, "Etapa": "", **{c: "" for c in columnas}, "Aceptación": i == len(estados) - 1}
         for i, e in enumerate(estados)]
    )
    st.caption(
        "Escriba el estado destino en cada celda. Para varios destinos (AFND) sepárelos con comas. "
        "Deje la celda vacía si no hay transición. El estado inicial es q0."
    )
    editada = st.data_editor(
        base, hide_index=True, width="stretch", disabled=["Estado"],
        key=f"tabla_{metodo}_{n}_{','.join(columnas)}",
    )
    transiciones: dict[str, dict[str, list[str]]] = {}
    for _, fila in editada.iterrows():
        por_simbolo = {}
        for c in columnas:
            destinos = [d.strip() for d in str(fila[c] or "").split(",") if d.strip()]
            if destinos:
                por_simbolo[EPSILON if c == EPSILON_VISIBLE else c] = destinos
        transiciones[fila["Estado"]] = por_simbolo
    try:
        return AutomataFinito(
            estados=estados,
            alfabeto=alfabeto,
            transiciones=transiciones,
            inicial="q0",
            finales={f["Estado"] for _, f in editada.iterrows() if f["Aceptación"]},
            descripciones={f["Estado"]: f["Etapa"] for _, f in editada.iterrows() if f["Etapa"]},
        )
    except ValueError as e:
        mostrar_error(str(e))
        return None


# Vistas por método


def vista_afd(automata: AutomataFinito, cadena: str, clave: str) -> None:
    if not automata.es_determinista():
        mostrar_error(
            "El autómata tiene estados con más de un destino para el mismo símbolo o transiciones ε. "
            "Utilice el método AFND o AFND-ε."
        )
        return
    definicion_formal(automata.estados, automata.alfabeto, automata.inicial, automata.finales)
    matriz_transicion(automata)
    try:
        r = simular_afd(automata, cadena)
    except ValueError as e:
        mostrar_error(str(e))
        return

    st.markdown("### Recorrido de la cadena")
    paso, lienzo, reproducir = control_pasos(len(r.pasos), clave)

    def dibujar(k: int) -> None:
        resaltada = {(r.pasos[k - 1].origen, r.pasos[k - 1].destino)} if k else set()
        lienzo.graphviz_chart(dot_finito(automata, {r.recorrido[k]}, resaltada), width="content")

    if reproducir:
        for k in range(len(r.recorrido)):
            dibujar(k)
            time.sleep(0.8)
    else:
        dibujar(paso)

    st.markdown("**Recorrido:** " + " → ".join(r.recorrido))
    tabla(
        [{"Paso": p.numero, "Estado actual": p.origen, "Entrada": p.simbolo, "Estado siguiente": p.destino,
          "Etapa": automata.descripciones.get(p.destino, "")} for p in r.pasos]
    )
    mostrar_resultado(r.aceptada, r.motivo)


def vista_afnd(automata: AutomataFinito, cadena: str, clave: str) -> None:
    if automata.tiene_epsilon():
        mostrar_error("El autómata tiene transiciones ε. Utilice el método AFND-ε y conversión a AFD.")
        return
    definicion_formal(automata.estados, automata.alfabeto, automata.inicial, automata.finales)
    matriz_transicion(automata)
    simulacion_conjuntos(automata, cadena, clave)


def simulacion_conjuntos(automata: AutomataFinito, cadena: str, clave: str) -> bool | None:
    try:
        r = simular_afnd(automata, cadena)
    except ValueError as e:
        mostrar_error(str(e))
        return None
    st.markdown("### Recorrido con conjuntos de estados activos")
    paso, lienzo, reproducir = control_pasos(len(r.pasos), clave)

    def dibujar(k: int) -> None:
        resaltadas = set()
        if k:
            p = r.pasos[k - 1]
            resaltadas = {(o, d) for o in p.origen for d in automata.destinos(o, p.simbolo)}
        lienzo.graphviz_chart(dot_finito(automata, r.recorrido[k], resaltadas), width="content")

    if reproducir:
        for k in range(len(r.recorrido)):
            dibujar(k)
            time.sleep(0.8)
    else:
        dibujar(min(paso, len(r.recorrido) - 1))

    filas = [{"Paso": 0, "Entrada": "—", "Estados activos": automata.nombre_conjunto(r.recorrido[0])}]
    for p in r.pasos:
        fila = {"Paso": p.numero, "Entrada": p.simbolo, "Estados activos": automata.nombre_conjunto(p.destino)}
        if automata.tiene_epsilon():
            fila = {"Paso": p.numero, "Entrada": p.simbolo,
                    "Mover(S, a)": automata.nombre_conjunto(p.movimiento),
                    "Estados activos": automata.nombre_conjunto(p.destino)}
        filas.append(fila)
    tabla(filas)
    mostrar_resultado(r.aceptada, r.motivo)
    return r.aceptada


def vista_afnd_epsilon(automata: AutomataFinito, cadena: str, clave: str) -> None:
    definicion_formal(automata.estados, automata.alfabeto, automata.inicial, automata.finales)
    matriz_transicion(automata)

    if automata.tiene_epsilon():
        st.markdown("### Paso 1. Cerradura ε de cada estado")
        tabla([{"Estado": e, "Cerradura ε": automata.nombre_conjunto(automata.cerradura_epsilon({e}))}
               for e in automata.estados])
    else:
        st.info("El autómata no tiene transiciones ε; la cerradura ε de cada estado es el propio estado.")

    st.markdown("### Paso 2. Construcción por subconjuntos")
    try:
        filas, afd = construccion_subconjuntos(automata)
    except ValueError as e:
        mostrar_error(str(e))
        return
    tabla(
        [{"Estado AFD": ("→ " if f.es_inicial else "") + ("* " if f.es_final else "") + f.nombre,
          "Conjunto del AFND": automata.nombre_conjunto(f.conjunto),
          **{f"Con {s}": f.transiciones[s] for s in automata.alfabeto}} for f in filas]
    )
    st.caption(
        "Cada estado del AFD representa un conjunto de estados del AFND. Un estado del AFD es de "
        "aceptación si su conjunto contiene algún estado de aceptación del AFND."
    )

    st.markdown("**Autómata original**")
    st.graphviz_chart(dot_finito(automata), width="content")
    st.markdown("**AFD equivalente**")
    st.graphviz_chart(dot_finito(afd), width="content")

    st.markdown("### Paso 3. Análisis de la cadena en el AFD resultante")
    try:
        r = simular_afd(afd, cadena)
    except ValueError as e:
        mostrar_error(str(e))
        return
    paso, lienzo, reproducir = control_pasos(len(r.pasos), clave)

    def dibujar(k: int) -> None:
        resaltada = {(r.pasos[k - 1].origen, r.pasos[k - 1].destino)} if k else set()
        lienzo.graphviz_chart(dot_finito(afd, {r.recorrido[k]}, resaltada), width="content")

    if reproducir:
        for k in range(len(r.recorrido)):
            dibujar(k)
            time.sleep(0.8)
    else:
        dibujar(paso)
    tabla([{"Paso": p.numero, "Estado actual": f"{p.origen} = {afd.descripciones[p.origen]}",
            "Entrada": p.simbolo, "Estado siguiente": f"{p.destino} = {afd.descripciones[p.destino]}"}
           for p in r.pasos])
    mostrar_resultado(r.aceptada, r.motivo)


def vista_arden(automata: AutomataFinito, cadena: str) -> None:
    if automata.tiene_epsilon():
        mostrar_error("Convierta primero el AFND-ε a AFD; el Lema de Arden se aplica sin transiciones ε.")
        return
    definicion_formal(automata.estados, automata.alfabeto, automata.inicial, automata.finales)
    matriz_transicion(automata)
    st.graphviz_chart(dot_finito(automata), width="content")

    st.markdown("### Enunciado del Lema de Arden")
    st.latex(r"X = A\,X + B \;\;\Longrightarrow\;\; X = A^{*}B \qquad (\lambda \notin A)")
    st.write(
        "Se asocia una incógnita Xi a cada estado qi. Cada transición qi con el símbolo a hacia qj "
        "aporta el término a·Xj, y cada estado de aceptación aporta λ."
    )

    r = resolver(automata)
    st.markdown("### Sistema de ecuaciones")
    st.code("\n".join(r.ecuaciones_iniciales), language=None)
    st.markdown("### Resolución paso a paso")
    for i, p in enumerate(r.pasos, start=1):
        st.markdown(f"**{i}. {p.titulo}.** {p.explicacion}")
        st.code("\n".join(p.ecuaciones), language=None)

    st.markdown("### Expresión regular obtenida")
    st.code(r.expresion, language=None)

    if cadena:
        invalidos = sorted({c for c in cadena if c not in automata.alfabeto})
        if invalidos:
            mostrar_error("La cadena contiene símbolos fuera del alfabeto: " + ", ".join(invalidos))
            return
        coincide = bool(re.fullmatch(expresion_a_python(r.expresion), cadena))
        if coincide != automata.acepta(cadena):
            mostrar_error("La expresión obtenida no coincide con el autómata para esta cadena.")
            return
        motivo = (
            f"La cadena {cadena} pertenece al lenguaje descrito por la expresión regular, "
            "y el autómata también la acepta."
            if coincide
            else f"La cadena {cadena} no pertenece al lenguaje de la expresión regular, "
            "y el autómata también la rechaza."
        )
        mostrar_resultado(coincide, motivo)


def editor_pila() -> AutomataPila | None:
    st.markdown("### Definición del autómata de pila")
    c1, c2, c3 = st.columns(3)
    n = c1.number_input("Número de nodos", min_value=1, max_value=10, value=2, key="n_pila")
    alfabeto = [s.strip() for s in c2.text_input("Alfabeto", "0, 1", key="alf_pila").split(",") if s.strip()]
    inicial_pila = c3.text_input("Símbolo inicial de la pila", "Z", key="z_pila").strip() or "Z"
    estados = [f"q{i}" for i in range(int(n))]
    finales = st.multiselect("Estados de aceptación", estados, default=[estados[0]], key="f_pila")
    st.caption(
        "Cada fila es una regla δ(estado, lee, tope) = (siguiente, apila). Deje 'Lee' vacío para una "
        "transición λ y 'Apila' vacío para desapilar. En 'Apila' el primer símbolo queda en el tope."
    )
    base = pd.DataFrame([{"Estado": "q0", "Lee": "1", "Tope": inicial_pila, "Siguiente": "q0", "Apila": inicial_pila}])
    editada = st.data_editor(base, num_rows="dynamic", hide_index=True, width="stretch", key=f"reglas_pila_{n}")
    reglas = [
        ReglaPila(str(f["Estado"]).strip(), str(f["Lee"] or "").strip(), str(f["Tope"]).strip(),
                  str(f["Siguiente"]).strip(), str(f["Apila"] or "").strip())
        for _, f in editada.iterrows() if str(f["Estado"] or "").strip()
    ]
    simbolos_pila = sorted({inicial_pila} | {r.tope for r in reglas} | {c for r in reglas for c in r.apila})
    return AutomataPila(estados, alfabeto, simbolos_pila, reglas, "q0", inicial_pila, set(finales))


def vista_pila(automata: AutomataPila, cadena: str, clave: str) -> None:
    definicion_formal(
        automata.estados, automata.alfabeto, automata.inicial, automata.finales,
        extra=f"<br>Γ = {{{', '.join(automata.simbolos_pila)}}}<br>Z<sub>0</sub> = {automata.simbolo_inicial_pila}",
    )
    st.markdown("**Reglas de transición** δ(estado, lee, tope) = (siguiente, apila)")
    tabla([{"Estado": r.estado, "Lee": r.lee or "λ", "Tope": r.tope, "Siguiente": r.siguiente,
            "Apila": r.apila or "λ (desapila)", "Etapa": automata.descripciones.get(r.siguiente, "")}
           for r in automata.reglas])
    try:
        r = simular_pila(automata, cadena)
    except ValueError as e:
        mostrar_error(str(e))
        return

    st.markdown("### Recorrido de la cadena")
    paso, lienzo, reproducir = control_pasos(len(r.pasos) - 1, clave)

    def dibujar(k: int) -> None:
        p = r.pasos[k]
        with lienzo.container():
            c1, c2 = st.columns([3, 1])
            c1.graphviz_chart(dot_pila(automata, p.estado), width="content")
            celdas = "".join(
                f'<div class="celda{" tope" if i == 0 else ""}">{s}</div>'
                for i, s in enumerate(p.pila if p.pila != "vacía" else "")
            )
            c2.markdown(f"**Pila** (tope arriba)<div class='pila'>{celdas}</div>", unsafe_allow_html=True)
            c2.markdown(f"**Entrada restante:** {p.restante}")

    if reproducir:
        for k in range(len(r.pasos)):
            dibujar(k)
            time.sleep(0.8)
    else:
        dibujar(paso)
    tabla([{"Paso": p.numero, "Estado": p.estado, "Lee": p.leido or "—", "Entrada restante": p.restante,
            "Pila (tope a la izquierda)": p.pila} for p in r.pasos])
    mostrar_resultado(r.aceptada, r.motivo)


def editor_turing() -> MaquinaTuring:
    st.markdown("### Definición de la máquina de Turing")
    c1, c2 = st.columns(2)
    n = c1.number_input("Número de nodos", min_value=1, max_value=10, value=2, key="n_tm")
    alfabeto = [s.strip() for s in c2.text_input("Alfabeto", "0, 1", key="alf_tm").split(",") if s.strip()]
    estados = [f"q{i}" for i in range(int(n))]
    finales = st.multiselect("Estados de aceptación", estados, default=[estados[-1]], key="f_tm")
    st.caption(
        f"Cada fila es una regla δ(estado, lee) = (siguiente, escribe, mueve). Use '{BLANCO}' para la "
        "celda en blanco y D, I o N para mover a la derecha, a la izquierda o no mover."
    )
    base = pd.DataFrame([{"Estado": "q0", "Lee": BLANCO, "Siguiente": estados[-1], "Escribe": BLANCO, "Mueve": "N"}])
    editada = st.data_editor(
        base, num_rows="dynamic", hide_index=True, width="stretch", key=f"reglas_tm_{n}",
        column_config={"Mueve": st.column_config.SelectboxColumn(options=["D", "I", "N"], required=True)},
    )
    reglas = [
        ReglaTuring(str(f["Estado"]).strip(), str(f["Lee"]).strip(), str(f["Siguiente"]).strip(),
                    str(f["Escribe"]).strip(), str(f["Mueve"]).strip())
        for _, f in editada.iterrows() if str(f["Estado"] or "").strip()
    ]
    return MaquinaTuring(estados, alfabeto, reglas, "q0", set(finales))


def vista_turing(maquina: MaquinaTuring, cadena: str, clave: str) -> None:
    definicion_formal(
        maquina.estados, maquina.alfabeto, maquina.inicial, maquina.finales,
        extra=f"<br>Γ = {{{', '.join(sorted(maquina.simbolos_cinta()))}}}<br>Blanco = {BLANCO}",
    )
    st.markdown("**Reglas de transición** δ(estado, lee) = (siguiente, escribe, mueve)")
    tabla([{"Estado": r.estado, "Lee": r.lee, "Siguiente": r.siguiente, "Escribe": r.escribe,
            "Mueve": MOVIMIENTOS_VISIBLES.get(r.mueve, r.mueve)}
           for r in maquina.reglas])
    try:
        r = simular_turing(maquina, cadena)
    except ValueError as e:
        mostrar_error(str(e))
        return

    st.markdown("### Ejecución sobre la cinta")
    paso, lienzo, reproducir = control_pasos(len(r.pasos) - 1, clave)

    def dibujar(k: int) -> None:
        p = r.pasos[k]
        celdas = "".join(
            f'<div class="celda{" cabezal" if i == p.posicion else ""}">{s}</div>'
            for i, s in enumerate(p.cinta)
        )
        with lienzo.container():
            st.markdown(f"**Cinta** (cabezal resaltado), estado {p.estado}<div class='cinta'>{celdas}</div>",
                        unsafe_allow_html=True)
            st.graphviz_chart(dot_turing(maquina, p.estado), width="content")

    if reproducir:
        for k in range(len(r.pasos)):
            dibujar(k)
            time.sleep(0.6)
    else:
        dibujar(paso)
    tabla([{"Paso": p.numero, "Estado": p.estado, "Cinta": "".join(p.cinta), "Posición del cabezal": p.posicion}
           for p in r.pasos])
    if r.aceptada:
        st.markdown(f"**Contenido final de la cinta:** {r.salida}  ({len(r.salida)} símbolos)")
    mostrar_resultado(r.aceptada, r.motivo)


# Barra lateral


with st.sidebar:
    st.markdown("### Configuración")
    metodo = st.radio("Método de solución", METODOS, key="metodo")
    origenes = [ORIGEN_CASO]
    if any(c.metodo == metodo for c in ejercicios_clase()):
        origenes.append(ORIGEN_CLASE)
    origenes.append(ORIGEN_MANUAL)
    origen = st.radio("Origen del modelo", origenes, key=f"origen_{metodo}")
    st.divider()
    st.caption(
        "Convención del caso de aplicación: 1 indica que el lote aprueba el control de calidad "
        "de la etapa; 0 indica que el lote se envía a reproceso."
    )


# Contenido principal

if origen == ORIGEN_MANUAL:
    if metodo in ("AFD", "AFND", "AFND-ε y conversión a AFD", "Lema de Arden"):
        automata = editor_finito(metodo, permite_epsilon=metodo == "AFND-ε y conversión a AFD")
        if automata is None:
            st.stop()
        cadena = parametros(len(automata.estados), automata.alfabeto, metodo, f"manual_{metodo}", "")
    elif metodo == "Autómata de Pila":
        automata = editor_pila()
        cadena = parametros(len(automata.estados), automata.alfabeto, metodo, "manual_pila", "")
    else:
        automata = editor_turing()
        cadena = parametros(len(automata.estados), automata.alfabeto, metodo, "manual_tm", "")
    clave = f"manual_{metodo}"
else:
    if origen == ORIGEN_CLASE:
        caso = next(c for c in ejercicios_clase() if c.metodo == metodo)
    else:
        caso = caso_por_metodo(metodo)
    automata = caso.automata
    mostrar_contexto(caso, automata.descripciones)
    cadena = parametros(len(automata.estados), automata.alfabeto, metodo, caso.clave, caso.cadena_sugerida)
    clave = caso.clave

try:
    if metodo == "AFD":
        vista_afd(automata, cadena, clave)
    elif metodo == "AFND":
        vista_afnd(automata, cadena, clave)
    elif metodo == "AFND-ε y conversión a AFD":
        vista_afnd_epsilon(automata, cadena, clave)
    elif metodo == "Lema de Arden":
        vista_arden(automata, cadena)
    elif metodo == "Autómata de Pila":
        vista_pila(automata, cadena, clave)
    else:
        vista_turing(automata, cadena, clave)
except (ValueError, KeyError, AutomatonException) as e:
    mostrar_error(str(e))

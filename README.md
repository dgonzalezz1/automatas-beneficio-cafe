# Simulador de Autómatas: beneficio húmedo de café

Proyecto final del curso Autómatas y Lenguajes Formales, Universidad Mariano Gálvez de Guatemala.

La aplicación modela el proceso de un beneficio húmedo de café en Guatemala con los métodos vistos en el curso. Cada estado representa una etapa del proceso y cada símbolo del alfabeto un evento registrado. En los autómatas finitos, 1 significa que el lote aprueba el control de calidad de la etapa y 0 que se envía a reproceso.

| Método | Caso de aplicación |
| --- | --- |
| AFD | Flujo normal de un lote: recepción, despulpado, fermentación y lavado, secado, trillado y empaque |
| AFND | Selección del tipo de secado: al sol en patio o mecánico en guardiola |
| AFND-ε y conversión a AFD | Escurrido automático después del lavado (transición ε), cerradura ε y método de subconjuntos |
| Lema de Arden | Expresión regular de todas las secuencias de control que llevan un lote a exportación |
| Autómata de Pila | Control de existencias de sacos en bodega: cada despacho debe tener un ingreso previo |
| Máquina de Turing | Totalizador de producción: suma en notación unaria los sacos de dos turnos |

La aplicación solicita los cuatro parámetros del enunciado: número de nodos, alfabeto, cadena a analizar y método de solución. Además de los casos del beneficio, incluye el ejercicio de clase del proceso Volkswagen y un modo de definición manual para analizar cualquier autómata.

## Requisitos

- Python 3.10 o superior
- Conexión a internet solo para instalar dependencias

## Instalación y ejecución

```bash
git clone https://github.com/dgonzalezz1/automatas-beneficio-cafe.git
cd automatas-beneficio-cafe
python -m venv .venv
```

Activar el entorno virtual:

- Windows: `.venv\Scripts\activate`
- macOS y Linux: `source .venv/bin/activate`

Instalar dependencias y ejecutar:

```bash
pip install -r requirements.txt
streamlit run app.py
```

La aplicación se abre en el navegador en `http://localhost:8501`.

## Guía de prueba

1. Seleccione un método de solución en la barra lateral.
2. Elija el origen del modelo: caso de aplicación, ejercicio de clase o definición manual.
3. Escriba la cadena a analizar. Cada caso muestra cadenas de ejemplo aceptadas y rechazadas.
4. Use el control "Paso del recorrido" o el botón "Reproducir recorrido" para ver la evolución del autómata.

Cadenas sugeridas para la verificación:

| Método | Aceptadas | Rechazadas |
| --- | --- | --- |
| AFD | 1111, 110111 | 1101, 11011 |
| AFND | 11101, 1110001 | 11001 |
| AFND-ε | 11111, 1110111 | 110111 |
| Autómata de Pila | 1100, 110100 | 100, 0110 |
| Máquina de Turing | 111011 (resultado 11111) | 111 |
| Ejercicio de clase (AFD) | 1111, 01111, 11111 | 1101, 1110 |

## Pruebas automáticas

```bash
python -m pytest
```

Las pruebas verifican el ejercicio de clase, la equivalencia entre cada AFND y su AFD por subconjuntos, que la expresión regular obtenida con el Lema de Arden reconoce exactamente el mismo lenguaje que el autómata, y los casos del autómata de pila y la máquina de Turing.

## Arquitectura

```
app.py                  Interfaz de usuario (Streamlit)
motor/finitos.py        AFD, AFND, AFND-ε, cerradura ε y construcción por subconjuntos
motor/arden.py          Sistema de ecuaciones y resolución con el Lema de Arden
motor/pila.py           Autómata de pila determinista
motor/turing.py         Máquina de Turing determinista
motor/graficos.py       Diagramas en lenguaje DOT (Graphviz)
casos/beneficio_cafe.py Casos del beneficio de café y ejercicios de clase
tests/                  Pruebas automáticas
```

El motor es independiente de la interfaz. La aceptación de cadenas se valida con la biblioteca automata-lib, y los procedimientos que se explican en clase (cerradura ε, subconjuntos y Lema de Arden) se calculan paso a paso en el propio código para mostrarlos en pantalla.

## Equipo

| Integrante | Usuario de GitHub |
| --- | --- |
| Diego (Team Leader) | dgonzalezz1 |
| Martín Maldonado | cvmaldonado |
| Por confirmar | Davidxon92 |
| Roberto Alejandro Iguardia | alejandroIguardia |

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

La aplicación solicita los cuatro parámetros del enunciado: número de nodos, alfabeto, cadena a analizar y método de solución. Además de los casos del beneficio, incluye un modo de definición manual para analizar cualquier autómata.

## Versión en línea

La aplicación está publicada en Streamlit Community Cloud y se puede usar sin instalar nada:

https://automatas-beneficio-cafe.streamlit.app/

Si la página muestra un aviso de que la aplicación está en reposo, presione el botón para activarla y espere unos 30 segundos.

## Requisitos

- Python 3.11 o superior (probado con 3.11, 3.13 y 3.14). Python 3.10 no es compatible porque Streamlit 1.66 exige 3.11.
- Git, o bien descargar el proyecto como ZIP desde GitHub (botón "Code", opción "Download ZIP").
- Conexión a internet solo para instalar dependencias.
- No es necesario instalar Graphviz: los diagramas se dibujan en el navegador.

En Windows, al instalar Python desde python.org marque la casilla "Add python.exe to PATH".

## Instalación y ejecución

Verifique la versión de Python (en Windows también puede usar `py --version`; en macOS y Linux, `python3 --version`):

```bash
python --version
```

Descargue el proyecto y cree el entorno virtual:

```bash
git clone https://github.com/dgonzalezz1/automatas-beneficio-cafe.git
cd automatas-beneficio-cafe
python -m venv .venv
```

En macOS y Linux use `python3 -m venv .venv`. En Windows, si `python` no se reconoce, use `py -m venv .venv`.

Activar el entorno virtual:

- Windows, PowerShell: `.venv\Scripts\Activate.ps1`
- Windows, Símbolo del sistema (cmd): `.venv\Scripts\activate.bat`
- macOS y Linux: `source .venv/bin/activate`

Si PowerShell indica que la ejecución de scripts está deshabilitada, ejecute una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, confirme y vuelva a activar el entorno. Al quedar activo, la línea de comandos muestra `(.venv)` al inicio.

Instalar dependencias y ejecutar:

```bash
pip install -r requirements.txt
streamlit run app.py
```

La aplicación se abre en el navegador en `http://localhost:8501`. Para detenerla, presione `Ctrl+C` en la terminal. Si el puerto 8501 está ocupado, use `streamlit run app.py --server.port 8502`.

Para volver a ejecutarla otro día basta con entrar a la carpeta del proyecto, activar el entorno virtual y ejecutar `streamlit run app.py`; no es necesario reinstalar.

### Problemas frecuentes

| Mensaje | Solución |
| --- | --- |
| `python` no se reconoce como comando | Reinstale Python marcando "Add python.exe to PATH", o use `py` en lugar de `python` |
| `No matching distribution found for streamlit==1.66.1` | La versión de Python es menor que 3.11; instale una versión más reciente |
| `streamlit` no se reconoce como comando | El entorno virtual no está activo; actívelo, o ejecute `python -m streamlit run app.py` |
| `ModuleNotFoundError: No module named 'automata'` | Las dependencias se instalaron fuera del entorno virtual; actívelo y repita `pip install -r requirements.txt` |

## Guía de prueba

1. Seleccione un método de solución en la barra lateral.
2. Elija el origen del modelo: caso de aplicación (beneficio de café) o definición manual.
3. Escriba la cadena a analizar. Cada caso muestra cadenas de ejemplo aceptadas y rechazadas.
4. Use el control "Paso del recorrido" o el botón "Reproducir recorrido" para ver la evolución del autómata.

Cadenas sugeridas para la verificación:

| Método | Aceptadas | Rechazadas |
| --- | --- | --- |
| AFD | 1111, 110111 | 1101, 11011 |
| AFND | 11101, 1110001 | 11001 |
| AFND-ε | 11111, 1110111 | 1101 |
| Autómata de Pila | 1100, 110100 | 100, 0110 |
| Lema de Arden | 1111, 110111 | 1101 |
| Máquina de Turing | 111011 (resultado 11111) | 111 |

## Pruebas automáticas

Con el entorno virtual activo:

```bash
python -m pytest
```

El resultado esperado es `25 passed`.

Las pruebas verifican el recorrido del AFD del beneficio, la equivalencia entre cada AFND y su AFD por subconjuntos, que la expresión regular obtenida con el Lema de Arden reconoce exactamente el mismo lenguaje que el autómata, y los casos del autómata de pila y la máquina de Turing.

## Arquitectura

```
app.py                  Interfaz de usuario (Streamlit)
motor/finitos.py        AFD, AFND, AFND-ε, cerradura ε y construcción por subconjuntos
motor/arden.py          Sistema de ecuaciones y resolución con el Lema de Arden
motor/pila.py           Autómata de pila determinista
motor/turing.py         Máquina de Turing determinista
motor/graficos.py       Diagramas en lenguaje DOT (Graphviz)
casos/beneficio_cafe.py Casos del beneficio de café
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

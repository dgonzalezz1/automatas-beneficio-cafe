# Simulador de Autómatas: beneficio húmedo de café

Proyecto final del curso Autómatas y Lenguajes Formales, Universidad Mariano Gálvez de Guatemala.

La aplicación modela el control de lotes de un beneficio húmedo de café en Guatemala con un autómata finito no determinista (AFND), el método indicado por el catedrático. Cada estado representa una etapa del proceso y cada símbolo un evento registrado: 1 significa que el lote aprueba el control de calidad de la etapa y 0 que se envía a reproceso.

| Estado | Etapa |
| --- | --- |
| q0 (inicial) | Recepción y clasificación del café cereza |
| q1 | Despulpado |
| q2 | Fermentación y lavado |
| q3 | Secado al sol en patio |
| q4 | Secado mecánico en guardiola |
| q5 (aceptación) | Trillado y empaque para exportación |

El no determinismo está en δ(q2, 1) = {q3, q4}: un lote aprobado después del lavado puede ir a secado al sol o a secado mecánico. La aplicación simula todos los caminos posibles a la vez (conjunto de estados activos) y muestra también el AFD equivalente obtenido por el método de subconjuntos.

La aplicación solicita los parámetros del enunciado: número de nodos, alfabeto, cadena a analizar y método de solución (AFND). Además del caso del beneficio, incluye el modo "Autómata personalizado" para definir y analizar cualquier AFND.

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

1. Elija el modo en la barra lateral: caso de estudio (beneficio de café) o autómata personalizado.
2. Escriba la cadena a analizar o seleccione una cadena de ejemplo.
3. Use el control "Paso del recorrido" o el botón "Reproducir recorrido" para ver la evolución del conjunto de estados activos.
4. Revise las pestañas "Definición formal", "Equivalencia con AFD" y "Caso de estudio".

Cadenas sugeridas para la verificación:

| Cadena | Resultado | Situación |
| --- | --- | --- |
| 1111 | Aceptada | Lote sin reprocesos |
| 11101 | Aceptada | Secado al sol interrumpido por lluvia |
| 1110001 | Aceptada | Secado mecánico prolongado |
| 110111 | Aceptada | Reproceso en fermentación |
| 11001 | Rechazada | Lote devuelto a recepción |
| 111 | Rechazada | Lote todavía en secado |

## Pruebas automáticas

Con el entorno virtual activo:

```bash
python -m pytest
```

El resultado esperado es `11 passed`.

Las pruebas verifican el recorrido por conjuntos del AFND del beneficio, el resultado de cada cadena de ejemplo, la tabla de subconjuntos y que el AFND y su AFD equivalente aceptan exactamente las mismas cadenas hasta longitud 9.

## Arquitectura

```
app.py                  Interfaz de usuario (Streamlit)
motor/finitos.py        Simulación del AFND y construcción por subconjuntos
motor/graficos.py       Diagramas en lenguaje DOT (Graphviz)
casos/beneficio_cafe.py AFND del beneficio de café y cadenas de ejemplo
tests/                  Pruebas automáticas
```

El motor es independiente de la interfaz. La aceptación de cadenas se valida con la biblioteca automata-lib, y los procedimientos que se explican en clase (recorrido por conjuntos y método de subconjuntos) se calculan paso a paso en el propio código para mostrarlos en pantalla.

## Equipo

| Integrante | Usuario de GitHub |
| --- | --- |
| Diego (Team Leader) | dgonzalezz1 |
| Martín Maldonado | cvmaldonado |
| Por confirmar | Davidxon92 |
| Roberto Alejandro Iguardia | alejandroIguardia |

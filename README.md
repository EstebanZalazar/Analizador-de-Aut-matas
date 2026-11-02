# Analizador de Autómatas (JFLAP)

Programa de consola, escrito en **Python**, que lee autómatas diseñados en [JFLAP](https://www.jflap.org/) (archivos `.jff`) y **analiza si una cadena es aceptada o rechazada**, mostrando el recorrido paso a paso.

Con un único programa se pueden analizar tres tipos de autómatas. El tipo se detecta solo, a partir del contenido del archivo:

| Tipo | Etiqueta `<type>` del .jff | Qué se simula | Criterio de aceptación |
|---|---|---|---|
| Autómata finito | `fa` | AFD, AFND y AFND con transiciones λ | Terminar la cadena en un estado final |
| Autómata de pila | `pda` | Deterministas y no deterministas | Estado final (si el autómata tiene finales) o pila vacía (si no tiene) |
| Máquina de Turing | `turing` | Determinista | Alcanzar un estado final |

Proyecto desarrollado en el marco de la materia *Autómatas y Lenguajes*. Los autómatas de ejemplo (carpeta `recursos/`) corresponden a los ejercicios de los trabajos prácticos.

## Requisitos

- **Python 3.8 o superior** (probado con Python 3.13).
- No hay que instalar nada más: solo usa la biblioteca estándar (`xml.etree.ElementTree` para leer los `.jff`).

## Descarga y ejecución

```bash
git clone https://github.com/EstebanZalazar/Analizador-de-Automatas.git
cd Analizador-de-Automatas/Automatas
python main.py          # en Linux/macOS, si hace falta: python3 main.py
```

> Si no tenés Git: en la página del repositorio, **Code → Download ZIP**, descomprimí y ejecutá `main.py` desde la carpeta `Automatas/`.

### Cómo se usa

1. El programa pide el **nombre del autómata**. Alcanza con escribir el nombre de un archivo de `recursos/`, con o sin extensión (`AP_Ej1d` o `AP_Ej1d.jff`). También acepta la ruta a cualquier `.jff` propio.
2. Muestra el autómata cargado: estados, alfabeto, estado inicial, finales y tabla de transiciones.
3. Pide una **cadena** (si se presiona Enter sin escribir nada, se analiza la cadena vacía).
4. Informa **ACEPTADA** o **RECHAZADA**, con el motivo y el recorrido paso a paso.
5. Permite probar más cadenas con el mismo autómata o cargar otro.

**Prueba rápida sin menús** (Linux/macOS), pasando las respuestas por entrada estándar:

```bash
printf 'AP_Ej1d\n01#10\nn\nn\n' | python3 main.py
```

## Ejemplos para probar

Escribí el nombre del archivo cuando el programa lo pida y luego cada cadena. Todos los resultados de las tablas fueron verificados ejecutando el programa.

### Autómatas finitos

| Archivo | Qué reconoce | ✅ Aceptadas | ❌ Rechazadas |
|---|---|---|---|
| `AF_Ej1a` | Cadenas binarias que **terminan en `000`** | `000`, `1000` | `100`, `0001` |
| `AF_Ej1g` | Cantidad **par de unos** (alfabeto `{1}`) | `11`, `1111`, *(vacía)* | `1`, `111` |
| `AF_Ej2a` | Números **divisibles por 3** (cadenas de dígitos) | `123`, `9` | `124`, `1000` |
| `AF_Ej4b` | Cualquier mezcla de `a` y `b`, con **a lo sumo una `c` al final** | `abac`, `c`, *(vacía)* | `cc`, `abcab` |
| `AF_Ej6` | **AFND con transiciones λ**: repeticiones de `ab` o `c` | `abcab`, `c`, *(vacía)* | `ac` |
| `AFND` | AFND: la traza muestra el *conjunto* de estados activos en cada paso | `ab`, `aab`, `aba` | `a`, `ba` |

### Autómatas de pila

| Archivo | Qué reconoce | ✅ Aceptadas | ❌ Rechazadas |
|---|---|---|---|
| `AP_Ej1a` | `0ⁿ1ᵐ` con **n ≤ m** | `01`, `011`, `0011` | `001`, `10` |
| `AP_Ej1b` | `0ⁿ1ᵐ` con **n ≥ m** | `01`, `001`, `0011`, `0001` | `011` |
| `AP_Ej1c` | `0ⁿ1ᵐ0ⁿ` | `010`, `0110` | `0100`, `01` |
| `AP_Ej1d` | `α#αᴿ` (una cadena, `#` y la misma cadena **invertida**) | `0#0`, `01#10`, `0110#0110` | `01#01` |

### Máquinas de Turing

En estos casos, además del veredicto, se muestra la **cinta final** y el movimiento del cabezal en cada paso.

| Archivo | Qué hace / reconoce | Entrada → resultado |
|---|---|---|
| `MT_Ej1` | **Suma 1** a un número binario | `1011` → cinta final `1100` · `111` → `1000` |
| `MT_Ej3` | **Complementa** los bits (0↔1) | `1010` → cinta final `0101` |
| `MT_Ej4` | `0⁺1²⁺` (uno o más ceros seguidos de dos o más unos) | ✅ `011`, `0011`, `0111` · ❌ `01`, `1` |
| `MT_Ej7` | Cadenas de `x` e `y` que **alternan** y tienen longitud par | ✅ `xy`, `xyxy`, `yx` · ❌ `xx`, `xyx` |
| `MT_Ej8` | `abc(bc)⁺` | ✅ `abcbc`, `abcbcbc` · ❌ `abc`, `abcb` |

## Ejemplo de salida

Autómata de pila `AP_Ej1d` con la cadena `01#10` (la pila se muestra con el tope a la izquierda):

```text
Paso Estado  Entrada restante    Pila (tope a la izq.)   Transicion
0    q0      01#10               Z
1    q1      1#10                0Z                      (q0, 0, λ) -> (q1, 0)
2    q1      #10                 10Z                     (q1, 1, λ) -> (q1, 1)
3    q2      10                  10Z                     (q1, #, λ) -> (q2, λ)
4    q2      0                   0Z                      (q2, 1, 1) -> (q2, λ)
5    q2      λ                   Z                       (q2, 0, 0) -> (q2, λ)
6    q0      λ                   (vacia)                 (q2, λ, Z) -> (q0, λ)

Resultado: ACEPTADA (se consumio la cadena y se llego al estado final q0)
```

Máquina de Turing `MT_Ej1` (suma 1 a `1011`):

```text
Paso   Estado  Cinta
0      q0      [1] 0  1  1
1      q0       1 [0] 1  1    (q0, 1 -> 1, R)
...
5      q1       1  0  1 [1]   (q0, λ -> λ, L)
6      q1       1  0 [1] 0    (q1, 1 -> 0, L)
7      q1       1 [0] 0  0    (q1, 1 -> 0, L)
8      q2       1 [1] 0  0    (q1, 0 -> 1, S)

Cinta final: '1100'
Resultado: ACEPTADA (se alcanzo el estado final q2)
```

Cuando el rechazo se debe a que no existe un camino, el programa lo explica. Por ejemplo, en `AF_Ej6` con la cadena `ac`:

```text
Resultado: RECHAZADA (no hay transicion para el simbolo 'c' desde {q2, q3})
```

## Probar autómatas propios

1. Diseñá un autómata finito, de pila o una máquina de Turing en JFLAP y guardalo como `.jff`.
2. Ejecutá el programa e ingresá la ruta del archivo (o copialo a `recursos/` y escribí solo su nombre).

El programa valida el archivo y avisa con un mensaje claro si hay un problema: XML inválido, tipo no soportado, falta de estado inicial, estados repetidos o transiciones que apuntan a estados inexistentes. Si la cadena contiene símbolos que no pertenecen al alfabeto del autómata, también lo informa.

## Cómo está construido

```text
Automatas/
├── main.py              # Punto de entrada
├── interfaz.py          # Interfaz de consola (no conoce ningún tipo de autómata)
├── nucleo/
│   ├── lector_jff.py    # Lectura y validación del XML de JFLAP (ElementTree)
│   ├── modelo.py        # Estructuras comunes: Automata, Resultado, ErrorAutomata
│   ├── registro.py      # Tabla de despacho: valor de <type> -> módulo que lo simula
│   └── comun.py         # Utilidades compartidas (símbolo vacío λ, orden de estados)
└── tipos/
    ├── af.py            # Autómatas finitos
    ├── ap.py            # Autómatas de pila
    └── mt.py            # Máquinas de Turing
recursos/                # Autómatas .jff de ejemplo
```

- **Un módulo por tipo, mismo contrato.** Cada módulo de `tipos/` expone las mismas funciones (`construir_delta`, `simular`, `mostrar_resumen`, `mostrar_traza`), así que la interfaz funciona igual para los tres. Para agregar un tipo nuevo alcanza con crear su módulo e incluirlo en `registro.py`.
- **Autómatas finitos:** se mantiene el conjunto de estados posibles en cada paso (construcción de subconjuntos "al vuelo") y se calcula la clausura λ, por lo que el mismo código sirve para AFD, AFND y AFND-λ.
- **Autómatas de pila:** búsqueda en anchura sobre configuraciones `(estado, posición, pila)`, explorando todas las ramas. Funciona con autómatas deterministas y no deterministas, devuelve el camino de aceptación más corto y tiene límites de exploración para no colgarse ante bucles infinitos.
- **Máquinas de Turing:** simulación determinista con cinta y cabezal; rechaza archivos con transiciones duplicadas y corta ante un posible bucle infinito.
- **Una sola representación de la función de transición** (`delta`, un diccionario con tuplas como claves) construida directamente desde el XML.

## Alcance de los ejemplos

Los autómatas de pila de `recursos/` (`AP_Ej1a` a `AP_Ej1c`) modelan los casos con **n ≥ 1 y m ≥ 1** (más la cadena vacía); por ejemplo, `AP_Ej1a` rechaza `1` aunque en el lenguaje abstracto `0ⁿ1ᵐ` con n = 0 sería válida. Es una característica del diseño de esos `.jff`, no del simulador, que aplica las transiciones tal como están definidas en el archivo.

## Autor

**Esteban Zalazar** — [github.com/EstebanZalazar](https://github.com/EstebanZalazar)

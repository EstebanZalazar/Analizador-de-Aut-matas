"""
Analizador de cadenas para Maquinas de Turing disenadas en JFLAP (.jff).

Flujo:
  1. El usuario ingresa el nombre del automata (.jff).
  2. Se leen estados, transiciones, estado inicial y estados finales.
  3. El usuario ingresa una cadena.
  4. Se simula la maquina sobre la cinta y se informa si es ACEPTADA o RECHAZADA.
"""
import os
import xml.etree.ElementTree as ET

CARPETA_RECURSOS = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "recursos")
)
BLANCO = "_"          # simbolo interno para la celda en blanco (en el .jff es <read/> vacio)
MAX_PASOS = 100000    # proteccion contra maquinas que nunca se detienen


# ---------------------------------------------------------------------------
# Lectura del .jff
# ---------------------------------------------------------------------------
def simbolo(texto):
    """Convierte el texto de <read>/<write> en simbolo; vacio = blanco."""
    if texto is None or texto.strip() == "":
        return BLANCO
    return texto.strip()


def cargar_maquina(nombre_archivo):
    """
    Lee un .jff de tipo 'turing' y devuelve:
      estados  : {id: nombre}
      alfabeto : set de simbolos leidos/escritos (sin el blanco)
      delta    : {(nombre_origen, simbolo_leido): (nombre_destino, simbolo_escrito, movimiento)}
      inicial  : nombre del estado inicial
      finales  : set con los nombres de los estados finales
    """
    raiz = ET.parse(nombre_archivo).getroot()
    automata = raiz.find("automaton")

    # Los .jff de maquinas de Turing usan <block>
    nodos = automata.findall("block")

    estados = {}
    inicial = None
    finales = set()
    for nodo in nodos:
        id_estado = nodo.get("id")
        nombre = nodo.get("name") or "q" + id_estado
        estados[id_estado] = nombre
        if nodo.find("initial") is not None:
            inicial = nombre
        if nodo.find("final") is not None:
            finales.add(nombre)

    delta = {}
    alfabeto = set()
    for t in automata.findall("transition"):
        origen = estados[t.find("from").text.strip()]
        destino = estados[t.find("to").text.strip()]
        leido = simbolo(t.find("read").text)
        escrito = simbolo(t.find("write").text)
        mov = (t.find("move").text or "S").strip().upper()
        delta[(origen, leido)] = (destino, escrito, mov)
        for s in (leido, escrito):
            if s != BLANCO:
                alfabeto.add(s)

    if inicial is None:
        raise ValueError("El automata no tiene estado inicial.")
    return estados, alfabeto, delta, inicial, finales


# ---------------------------------------------------------------------------
# Simulacion
# ---------------------------------------------------------------------------
def mostrar_cinta(cinta, cabezal):
    """Devuelve la cinta como texto, marcando la celda del cabezal entre [ ]."""
    if not cinta:
        return "[" + BLANCO + "]"
    desde = min(min(cinta), cabezal)
    hasta = max(max(cinta), cabezal)
    partes = []
    for i in range(desde, hasta + 1):
        s = cinta.get(i, BLANCO)
        partes.append(f"[{s}]" if i == cabezal else f" {s} ")
    return "".join(partes)


def simular(cadena, delta, inicial, finales, verbose=True):
    """
    Simula la maquina. Se detiene cuando:
      - alcanza un estado final            -> ACEPTA
      - no existe transicion aplicable     -> RECHAZA
      - supera MAX_PASOS                   -> RECHAZA (posible bucle infinito)
    Devuelve (aceptada, motivo, cinta_final).
    """
    cinta = {i: c for i, c in enumerate(cadena)}
    cabezal = 0
    estado = inicial
    paso = 0

    if verbose:
        print(f"\n{'Paso':<5}{'Estado':<8}Cinta")
        print(f"{paso:<5}{estado:<8}{mostrar_cinta(cinta, cabezal)}")

    while True:
        if estado in finales:
            return True, f"se alcanzo el estado final {estado}", cinta

        if paso >= MAX_PASOS:
            return False, "se supero el maximo de pasos (posible bucle infinito)", cinta

        leido = cinta.get(cabezal, BLANCO)
        clave = (estado, leido)
        if clave not in delta:
            nombre = "blanco" if leido == BLANCO else leido
            return False, f"no hay transicion para ({estado}, {nombre})", cinta

        destino, escrito, mov = delta[clave]

        # escribir (si se escribe blanco, se borra la celda)
        if escrito == BLANCO:
            cinta.pop(cabezal, None)
        else:
            cinta[cabezal] = escrito

        # mover
        if mov == "R":
            cabezal += 1
        elif mov == "L":
            cabezal -= 1

        paso += 1
        if verbose:
            print(f"{paso:<5}{destino:<8}{mostrar_cinta(cinta, cabezal)}"
                  f"   ({estado}, {leido} -> {escrito}, {mov})")
        estado = destino


def contenido_cinta(cinta):
    """Contenido de la cinta sin blancos de los extremos."""
    if not cinta:
        return ""
    return "".join(cinta.get(i, BLANCO) for i in range(min(cinta), max(cinta) + 1))


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def pedir_archivo():
    while True:
        nombre = input("Nombre del automata (ej: Ej4 o Ej4.jff): ").strip()
        if not nombre:
            continue
        if not nombre.lower().endswith(".jff"):
            nombre += ".jff"
        ruta = os.path.join(CARPETA_RECURSOS, nombre)
        if os.path.isfile(ruta):
            return ruta
        print(f"  No se encontro '{nombre}' en {CARPETA_RECURSOS}. Intente de nuevo.")


def main():
    archivo = pedir_archivo()
    try:
        estados, alfabeto, delta, inicial, finales = cargar_maquina(archivo)
    except (ET.ParseError, ValueError, AttributeError, KeyError) as e:
        print(f"Error al leer el archivo: {e}")
        return

    print("\n=== Maquina cargada ===")
    print("Estados   :", ", ".join(estados[k] for k in sorted(estados, key=int)))
    print("Alfabeto  :", ", ".join(sorted(alfabeto)) or "(vacio)")
    print("Inicial   :", inicial)
    print("Finales   :", ", ".join(sorted(finales)) or "(ninguno)")
    print("Transiciones (estado, leido) -> (destino, escrito, mov):")
    for (o, l), (d, e, m) in delta.items():
        print(f"  ({o}, {l}) -> ({d}, {e}, {m})")
    print(f"  (el simbolo '{BLANCO}' representa la celda en blanco)")

    seguir = "s"
    while seguir == "s":
        cadena = input("\nIngrese la cadena a analizar (vacio = cadena vacia): ").strip()
        aceptada, motivo, cinta = simular(cadena, delta, inicial, finales)

        print(f"\nCinta final: {contenido_cinta(cinta)!r}")
        if aceptada:
            print(f"Resultado: ACEPTADA ({motivo})")
        else:
            print(f"Resultado: RECHAZADA ({motivo})")

        seguir = input("\n¿Analizar otra cadena con esta maquina? (s/n): ").strip().lower()


if __name__ == "__main__":
    main()
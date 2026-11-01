"""
Analizador de cadenas para Automatas Finitos disenados en JFLAP (.jff).
Funciona con AFD, AFND y AFND con transiciones lambda.

Flujo:
  1. El usuario ingresa el nombre del automata (.jff).
  2. Se leen estados, alfabeto, transiciones, estado inicial y estados finales.
  3. El usuario ingresa una cadena.
  4. Se simula el automata y se informa si la cadena es ACEPTADA o RECHAZADA.

Convenciones de JFLAP que se respetan:
  - <read/> vacio -> transicion lambda (no consume simbolo).

Metodo de simulacion: se mantiene el CONJUNTO de estados en los que puede
estar el automata (construccion de subconjuntos "al vuelo"). Si el automata
es determinista, el conjunto siempre tiene un solo estado.

Criterio de aceptacion: la cadena se acepta si, al terminar de leerla, al
menos uno de los estados alcanzados es final.
"""
import os
import xml.etree.ElementTree as ET

CARPETA_RECURSOS = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "recursos")
)
LAMBDA = "λ"   # solo para mostrar; en el .jff es una etiqueta vacia


# ---------------------------------------------------------------------------
# Lectura del .jff
# ---------------------------------------------------------------------------
def texto(nodo):
    """Texto de un nodo XML sin espacios; vacio si no existe o esta vacio."""
    if nodo is None or nodo.text is None:
        return ""
    return nodo.text.strip()


def cargar_automata(nombre_archivo):
    """
    Lee un .jff de tipo 'fa' y devuelve:
      estados  : {id: nombre}
      alfabeto : set de simbolos de entrada (sin lambda)
      delta    : {(nombre_origen, simbolo): set(nombres_destino)}
                 ('' representa lambda)
      inicial  : nombre del estado inicial
      finales  : set con los nombres de los estados finales
    """
    raiz = ET.parse(nombre_archivo).getroot()

    tipo = texto(raiz.find("type"))
    if tipo != "fa":
        raise ValueError(f"el archivo es de tipo '{tipo}', se esperaba 'fa'.")

    automata = raiz.find("automaton")

    estados = {}
    inicial = None
    finales = set()
    for nodo in automata.findall("state"):
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
        origen = estados[texto(t.find("from"))]
        destino = estados[texto(t.find("to"))]
        simbolo = texto(t.find("read"))
        delta.setdefault((origen, simbolo), set()).add(destino)
        if simbolo:
            alfabeto.add(simbolo)

    if inicial is None:
        raise ValueError("El automata no tiene estado inicial.")
    return estados, alfabeto, delta, inicial, finales


def es_determinista(delta):
    """AFD: sin transiciones lambda y un unico destino por (estado, simbolo)."""
    return all(s != "" and len(d) == 1 for (_, s), d in delta.items())


# ---------------------------------------------------------------------------
# Simulacion
# ---------------------------------------------------------------------------
def clausura_lambda(conjunto, delta):
    """Estados alcanzables desde 'conjunto' usando solo transiciones lambda."""
    resultado = set(conjunto)
    pendientes = list(conjunto)
    while pendientes:
        estado = pendientes.pop()
        for destino in delta.get((estado, ""), ()):
            if destino not in resultado:
                resultado.add(destino)
                pendientes.append(destino)
    return resultado


def mostrar_conjunto(conjunto):
    """Conjunto de estados como texto ordenado: {q0, q2}."""
    if not conjunto:
        return "{}"
    return "{" + ", ".join(sorted(conjunto, key=clave_natural)) + "}"


def clave_natural(nombre):
    """Orden natural para nombres tipo q2 < q10."""
    digitos = "".join(c for c in nombre if c.isdigit())
    return (nombre.rstrip("0123456789"), int(digitos) if digitos else -1, nombre)


def simular(cadena, delta, inicial, finales, verbose=True):
    """
    Simula el automata sobre la cadena.
    Devuelve (aceptada, motivo).
    Se detiene antes de tiempo (RECHAZA) si el conjunto de estados queda vacio.
    """
    actuales = clausura_lambda({inicial}, delta)

    if verbose:
        print(f"\n{'Paso':<5}{'Simbolo':<9}Estados actuales")
        print(f"{0:<5}{'-':<9}{mostrar_conjunto(actuales)}")

    for paso, simbolo in enumerate(cadena, start=1):
        siguientes = set()
        for estado in actuales:
            siguientes |= delta.get((estado, simbolo), set())
        siguientes = clausura_lambda(siguientes, delta)

        if verbose:
            print(f"{paso:<5}{simbolo:<9}{mostrar_conjunto(siguientes)}")

        if not siguientes:
            return False, (f"no hay transicion para el simbolo '{simbolo}' "
                           f"desde {mostrar_conjunto(actuales)}")
        actuales = siguientes

    alcanzados = actuales & finales
    if alcanzados:
        return True, f"se termino la cadena en el estado final {mostrar_conjunto(alcanzados)}"
    return False, (f"se termino la cadena en {mostrar_conjunto(actuales)}, "
                   "que no contiene estados finales")


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def pedir_archivo():
    while True:
        nombre = input("Nombre del automata (ej: Ej1a o Ej1a.jff): ").strip()
        if not nombre:
            continue
        if not nombre.lower().endswith(".jff"):
            nombre += ".jff"
        if os.path.isfile(nombre):          # ruta indicada directamente
            return nombre
        ruta = os.path.join(CARPETA_RECURSOS, nombre)
        if os.path.isfile(ruta):
            return ruta
        print(f"  No se encontro '{nombre}' en {CARPETA_RECURSOS}. Intente de nuevo.")


def main():
    archivo = pedir_archivo()
    try:
        estados, alfabeto, delta, inicial, finales = cargar_automata(archivo)
    except (ET.ParseError, ValueError, AttributeError, KeyError) as e:
        print(f"Error al leer el archivo: {e}")
        return

    tipo = "AFD" if es_determinista(delta) else "AFND"
    if any(s == "" for (_, s) in delta):
        tipo += " con transiciones lambda"

    print(f"\n=== Automata finito cargado ({tipo}) ===")
    print("Estados   :", ", ".join(estados[k] for k in sorted(estados, key=int)))
    print("Alfabeto  :", ", ".join(sorted(alfabeto)) or "(vacio)")
    print("Inicial   :", inicial)
    print("Finales   :", ", ".join(sorted(finales, key=clave_natural)) or "(ninguno)")
    print("Transiciones (estado, simbolo) -> destinos:")
    for (o, s), destinos in sorted(delta.items(),
                                   key=lambda kv: (clave_natural(kv[0][0]), kv[0][1])):
        print(f"  ({o}, {s or LAMBDA}) -> {mostrar_conjunto(destinos)}")
    print(f"  (el simbolo '{LAMBDA}' representa una transicion sin consumir entrada)")

    seguir = "s"
    while seguir == "s":
        cadena = input("\nIngrese la cadena a analizar (vacio = cadena vacia): ").strip()

        fuera = sorted(set(cadena) - alfabeto)
        if fuera:
            print(f"Aviso: simbolos fuera del alfabeto del automata: {', '.join(fuera)}")

        aceptada, motivo = simular(cadena, delta, inicial, finales)

        if aceptada:
            print(f"\nResultado: ACEPTADA ({motivo})")
        else:
            print(f"\nResultado: RECHAZADA ({motivo})")

        seguir = input("\n¿Analizar otra cadena con este automata? (s/n): ").strip().lower()


if __name__ == "__main__":
    main()
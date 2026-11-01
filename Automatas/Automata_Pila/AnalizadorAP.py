"""
Analizador de cadenas para Automatas de Pila disenados en JFLAP (.jff).

Flujo:
  1. El usuario ingresa el nombre del automata (.jff).
  2. Se leen estados, transiciones, estado inicial y estados finales.
  3. El usuario ingresa una cadena.
  4. Se simula el automata (explorando todas las ramas posibles, por lo que
     tambien funciona con automatas NO deterministas) y se informa si la
     cadena es ACEPTADA o RECHAZADA.

Convenciones de JFLAP que se respetan:
  - <read/> vacio  -> la transicion no consume simbolo de la entrada (lambda).
  - <pop/>  vacio  -> la transicion no desapila ni exige nada en el tope.
  - <push/> vacio  -> la transicion no apila nada.
  - <push>0Z</push> -> el primer caracter ('0') queda en el TOPE de la pila.
  - La pila comienza con el simbolo inicial Z.

Criterio de aceptacion (definicion de la teoria): una cadena es aceptada si,
al terminar de consumirla, la pila quedo vacia. Los estados finales marcados
en el .jff no se tienen en cuenta.
"""
import os
import xml.etree.ElementTree as ET
from collections import deque

CARPETA_RECURSOS = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "recursos")
)
LAMBDA = "λ"          # solo para mostrar; en el .jff es una etiqueta vacia
PILA_INICIAL = "Z"    # simbolo inicial de la pila
MAX_CONFIGS = 200000  # proteccion contra automatas con infinitas configuraciones
MAX_PILA = 200        # proteccion contra pilas que crecen sin limite


# ---------------------------------------------------------------------------
# Lectura del .jff
# ---------------------------------------------------------------------------
def texto(nodo):
    """Texto de un nodo XML sin espacios; vacio si no existe o esta vacio."""
    if nodo is None or nodo.text is None:
        return ""
    return nodo.text.strip()


def mostrar(simbolos):
    """Cadena para imprimir: lambda si esta vacia."""
    return simbolos if simbolos else LAMBDA


def cargar_automata(nombre_archivo):
    """
    Lee un .jff de tipo 'pda' y devuelve:
      estados       : {id: nombre}
      alfabeto      : set de simbolos de entrada (sin lambda)
      alfabeto_pila : set de simbolos de pila
      delta         : {(origen, leido, pop): [(destino, push), ...]}
                      ('' representa lambda en leido, pop y push)
      inicial       : nombre del estado inicial
      finales       : set con los nombres de los estados finales
    """
    raiz = ET.parse(nombre_archivo).getroot()

    tipo = texto(raiz.find("type"))
    if tipo != "pda":
        raise ValueError(f"el archivo es de tipo '{tipo}', se esperaba 'pda'.")

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
    alfabeto_pila = {PILA_INICIAL}
    for t in automata.findall("transition"):
        origen = estados[texto(t.find("from"))]
        destino = estados[texto(t.find("to"))]
        leido = texto(t.find("read"))
        pop = texto(t.find("pop"))
        push = texto(t.find("push"))
        delta.setdefault((origen, leido, pop), []).append((destino, push))
        alfabeto.update(leido)
        alfabeto_pila.update(pop)
        alfabeto_pila.update(push)

    if inicial is None:
        raise ValueError("El automata no tiene estado inicial.")
    return estados, alfabeto, alfabeto_pila, delta, inicial, finales


# ---------------------------------------------------------------------------
# Simulacion
# ---------------------------------------------------------------------------
def es_aceptacion(config, longitud):
    """Una configuracion acepta si se consumio toda la cadena y la pila quedo vacia."""
    estado, pos, pila = config
    return pos == longitud and pila == ""


def reconstruir_camino(padre, config):
    """Recorre los padres y devuelve [(transicion, configuracion), ...] desde el inicio."""
    camino = []
    while padre[config] is not None:
        anterior, trans = padre[config]
        camino.append((trans, config))
        config = anterior
    camino.reverse()
    return camino


def simular(cadena, delta, inicial):
    """
    Simula el automata por busqueda en anchura sobre configuraciones
    (estado, posicion en la entrada, pila). La pila se guarda como texto con
    el tope a la IZQUIERDA.

    Devuelve (aceptada, motivo, camino, configuraciones_exploradas).
    Si la cadena se acepta, 'camino' es la secuencia mas corta de movimientos.
    """
    # indice para recorrer rapido las transiciones de cada estado
    por_origen = {}
    for (origen, leido, pop), destinos in delta.items():
        for destino, push in destinos:
            por_origen.setdefault(origen, []).append((leido, pop, destino, push))

    inicio = (inicial, 0, PILA_INICIAL)
    padre = {inicio: None}
    cola = deque([inicio])
    truncado = False

    while cola:
        config = cola.popleft()
        estado, pos, pila = config

        if es_aceptacion(config, len(cadena)):
            motivo = "se consumio la cadena y la pila quedo vacia"
            return True, motivo, reconstruir_camino(padre, config), len(padre)

        for leido, pop, destino, push in por_origen.get(estado, []):
            # 1) simbolo de entrada
            if leido:
                if pos >= len(cadena) or cadena[pos] != leido:
                    continue
                nueva_pos = pos + 1
            else:
                nueva_pos = pos

            # 2) tope de la pila (pop vacio = sin condicion)
            if not pila.startswith(pop):
                continue

            # 3) apilar (el primer simbolo de push queda en el tope)
            nueva_pila = push + pila[len(pop):]
            if len(nueva_pila) > MAX_PILA:
                truncado = True
                continue

            nueva = (destino, nueva_pos, nueva_pila)
            if nueva in padre:
                continue
            if len(padre) >= MAX_CONFIGS:
                truncado = True
                continue
            padre[nueva] = (config, (estado, leido, pop, destino, push))
            cola.append(nueva)

    if truncado:
        motivo = ("se supero el limite de exploracion sin encontrar una "
                  "configuracion de aceptacion (posible bucle infinito)")
    else:
        motivo = "ninguna secuencia de movimientos consume la cadena y deja la pila vacia"
    return False, motivo, [], len(padre)


def mostrar_camino(cadena, inicial, camino):
    """Imprime el recorrido paso a paso."""
    print(f"\n{'Paso':<5}{'Estado':<8}{'Entrada restante':<20}{'Pila (tope a la izq.)':<24}Transicion")
    print(f"{0:<5}{inicial:<8}{mostrar(cadena):<20}{PILA_INICIAL:<24}")
    for paso, (trans, (estado, pos, pila)) in enumerate(camino, start=1):
        origen, leido, pop, destino, push = trans
        restante = mostrar(cadena[pos:])
        pila_txt = pila if pila else "(vacia)"
        detalle = f"({origen}, {mostrar(leido)}, {mostrar(pop)}) -> ({destino}, {mostrar(push)})"
        print(f"{paso:<5}{estado:<8}{restante:<20}{pila_txt:<24}{detalle}")


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
        estados, alfabeto, alfabeto_pila, delta, inicial, finales = cargar_automata(archivo)
    except (ET.ParseError, ValueError, AttributeError, KeyError) as e:
        print(f"Error al leer el archivo: {e}")
        return

    print("\n=== Automata de pila cargado ===")
    print("Estados          :", ", ".join(estados[k] for k in sorted(estados, key=int)))
    print("Alfabeto entrada :", ", ".join(sorted(alfabeto)) or "(vacio)")
    print("Alfabeto de pila :", ", ".join(sorted(alfabeto_pila)))
    print("Simbolo inicial  :", PILA_INICIAL)
    print("Inicial          :", inicial)
    print("Transiciones (estado, leido, tope) -> (destino, apilar):")
    for (o, l, p), destinos in delta.items():
        for d, push in destinos:
            print(f"  ({o}, {mostrar(l)}, {mostrar(p)}) -> ({d}, {mostrar(push)})")
    print(f"  (el simbolo '{LAMBDA}' representa vacio: no leer / no desapilar / no apilar)")

    print("Criterio de aceptacion: pila vacia (definicion de la teoria)")

    seguir = "s"
    while seguir == "s":
        cadena = input("\nIngrese la cadena a analizar (vacio = cadena vacia): ").strip()

        fuera = sorted(set(cadena) - alfabeto)
        if fuera:
            print(f"Aviso: simbolos fuera del alfabeto del automata: {', '.join(fuera)}")

        aceptada, motivo, camino, n = simular(cadena, delta, inicial)

        if aceptada:
            mostrar_camino(cadena, inicial, camino)
            print(f"\nResultado: ACEPTADA ({motivo})")
        else:
            print(f"\nConfiguraciones exploradas: {n}")
            print(f"Resultado: RECHAZADA ({motivo})")

        seguir = input("\n¿Analizar otra cadena con este automata? (s/n): ").strip().lower()


if __name__ == "__main__":
    main()
"""
Automatas de pila (<type>pda</type>), deterministas o no deterministas.

Convenciones de JFLAP que se respetan:
  - <read/> vacio  -> la transicion no consume simbolo de la entrada (lambda).
  - <pop/>  vacio  -> la transicion no desapila ni exige nada en el tope.
  - <push/> vacio  -> la transicion no apila nada.
  - <push>0Z</push> -> el primer caracter ('0') queda en el TOPE de la pila.
  - La pila comienza con el simbolo inicial Z.
  El vacio se guarda internamente como "" y se muestra como lambda.

Criterio de aceptacion: el .jff no lo guarda (JFLAP lo elige al simular), asi
que se infiere de lo que tiene el archivo:
  - si hay al menos un estado final -> ESTADO FINAL: se acepta al consumir
    toda la cadena estando en un estado final (la pila no importa);
  - si no hay estados finales       -> PILA VACIA: se acepta al consumir toda
    la cadena con la pila vacia.

Metodo de simulacion: busqueda en anchura sobre configuraciones
(estado, posicion en la entrada, pila), explorando todas las ramas, por lo
que tambien funciona con automatas NO deterministas.

Contrato del modulo (ver registro.py): TIPO, NOMBRE, ETIQUETA_ESTADO,
construir_delta(), simular(), mostrar_resumen() y mostrar_traza().
"""
from collections import deque

from nucleo.comun import VACIO, LAMBDA, mostrar, clave_natural
from nucleo.modelo import Resultado

TIPO = "pda"
NOMBRE = "Automata de pila"
ETIQUETA_ESTADO = "state"

PILA_INICIAL = "Z"    # simbolo inicial de la pila
MAX_CONFIGS = 200000  # proteccion contra automatas con infinitas configuraciones
MAX_PILA = 200        # proteccion contra pilas que crecen sin limite

CRITERIO_FINAL = "estado final"
CRITERIO_PILA = "pila vacia"


# ---------------------------------------------------------------------------
# Construccion de delta
# ---------------------------------------------------------------------------
def construir_delta(transiciones):
    """
    A partir de las transiciones en crudo devuelve (delta, alfabeto, extra):
      delta    : {(origen, leido, pop): [(destino, push), ...]}
                 ('' representa lambda en leido, pop y push)
      alfabeto : simbolos de entrada, sin lambda
      extra    : {"alfabeto_pila": simbolos de pila, incluido Z}
    """
    delta = {}
    alfabeto = set()
    alfabeto_pila = {PILA_INICIAL}
    for t in transiciones:
        leido = t.get("read", VACIO)
        pop = t.get("pop", VACIO)
        push = t.get("push", VACIO)
        delta.setdefault((t["from"], leido, pop), []).append((t["to"], push))
        alfabeto.update(leido)
        alfabeto_pila.update(pop)
        alfabeto_pila.update(push)
    return delta, alfabeto, {"alfabeto_pila": alfabeto_pila}


def criterio(automata):
    """Criterio de aceptacion que corresponde segun lo leido del .jff."""
    return CRITERIO_FINAL if automata.finales else CRITERIO_PILA


# ---------------------------------------------------------------------------
# Simulacion
# ---------------------------------------------------------------------------
def es_aceptacion(config, longitud, crit, finales):
    """Una configuracion acepta si se consumio toda la cadena y se cumple el criterio."""
    estado, pos, pila = config
    if pos != longitud:
        return False
    if crit == CRITERIO_FINAL:
        return estado in finales
    return pila == ""


def reconstruir_camino(padre, config):
    """Recorre los padres y devuelve [(transicion, configuracion), ...] desde el inicio."""
    camino = []
    while padre[config] is not None:
        anterior, trans = padre[config]
        camino.append((trans, config))
        config = anterior
    camino.reverse()
    return camino


def simular(cadena, automata):
    """
    Simula el automata y devuelve un Resultado.

    La pila se guarda como texto con el tope a la IZQUIERDA. Si la cadena se
    acepta, la traza es la secuencia MAS CORTA de movimientos:
      [((origen, leido, pop, destino, push), (estado, pos, pila)), ...]
    datos: {"explorados": configuraciones visitadas, "criterio": criterio
            aplicado, "inicial": estado inicial, "cadena": entrada}.
    """
    crit = criterio(automata)
    finales = automata.finales

    # indice para recorrer rapido las transiciones de cada estado
    por_origen = {}
    for (origen, leido, pop), destinos in automata.delta.items():
        for destino, push in destinos:
            por_origen.setdefault(origen, []).append((leido, pop, destino, push))

    inicio = (automata.inicial, 0, PILA_INICIAL)
    padre = {inicio: None}
    cola = deque([inicio])
    truncado = False

    def resultado(aceptada, motivo, camino):
        datos = {"explorados": len(padre), "criterio": crit,
                 "inicial": automata.inicial, "cadena": cadena}
        return Resultado(aceptada, motivo, camino, datos)

    while cola:
        config = cola.popleft()
        estado, pos, pila = config

        if es_aceptacion(config, len(cadena), crit, finales):
            if crit == CRITERIO_FINAL:
                motivo = f"se consumio la cadena y se llego al estado final {estado}"
            else:
                motivo = "se consumio la cadena y la pila quedo vacia"
            return resultado(True, motivo, reconstruir_camino(padre, config))

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
    elif crit == CRITERIO_FINAL:
        motivo = ("ninguna secuencia de movimientos consume la cadena y "
                  "termina en un estado final")
    else:
        motivo = ("ninguna secuencia de movimientos consume la cadena y "
                  "deja la pila vacia")
    return resultado(False, motivo, [])


# ---------------------------------------------------------------------------
# Salida por pantalla
# ---------------------------------------------------------------------------
def mostrar_resumen(automata):
    """Imprime el automata cargado."""
    print(f"\n=== {NOMBRE} cargado ===")
    print("Estados          :", ", ".join(automata.estados[k]
                                          for k in sorted(automata.estados, key=int)))
    print("Alfabeto entrada :", ", ".join(sorted(automata.alfabeto)) or "(vacio)")
    print("Alfabeto de pila :", ", ".join(sorted(automata.extra["alfabeto_pila"])))
    print("Simbolo inicial  :", PILA_INICIAL)
    print("Inicial          :", automata.inicial)
    print("Finales          :", ", ".join(sorted(automata.finales, key=clave_natural))
          or "(ninguno)")
    print("Transiciones (estado, leido, tope) -> (destino, apilar):")
    ordenadas = sorted(
        ((o, l, p, d, push)
         for (o, l, p), destinos in automata.delta.items()
         for d, push in destinos),
        key=lambda x: (clave_natural(x[0]), x[1], x[2], clave_natural(x[3]), x[4]))
    for o, l, p, d, push in ordenadas:
        print(f"  ({o}, {mostrar(l)}, {mostrar(p)}) -> ({d}, {mostrar(push)})")
    print(f"  (el simbolo '{LAMBDA}' representa vacio: no leer / no desapilar / no apilar)")

    if criterio(automata) == CRITERIO_FINAL:
        print("Criterio de aceptacion: estado final (el automata tiene estados finales)")
    else:
        print("Criterio de aceptacion: pila vacia (el automata no tiene estados finales)")


def mostrar_traza(cadena, resultado):
    """Imprime el recorrido paso a paso si se acepto; si no, cuantas configuraciones se exploraron."""
    if not resultado.aceptada:
        print(f"\nConfiguraciones exploradas: {resultado.datos['explorados']}")
        return

    inicial = resultado.datos["inicial"]
    print(f"\n{'Paso':<5}{'Estado':<8}{'Entrada restante':<20}"
          f"{'Pila (tope a la izq.)':<24}Transicion")
    print(f"{0:<5}{inicial:<8}{mostrar(cadena):<20}{PILA_INICIAL:<24}")
    for paso, (trans, (estado, pos, pila)) in enumerate(resultado.traza, start=1):
        origen, leido, pop, destino, push = trans
        restante = mostrar(cadena[pos:])
        pila_txt = pila if pila else "(vacia)"
        detalle = (f"({origen}, {mostrar(leido)}, {mostrar(pop)}) -> "
                   f"({destino}, {mostrar(push)})")
        print(f"{paso:<5}{estado:<8}{restante:<20}{pila_txt:<24}{detalle}")
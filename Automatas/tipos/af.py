"""
Automatas finitos (<type>fa</type>): AFD, AFND y AFND con transiciones lambda.

Convenciones de JFLAP que se respetan:
  - <read/> vacio -> transicion lambda (no consume simbolo); se guarda como "".

Metodo de simulacion: se mantiene el CONJUNTO de estados en los que puede
estar el automata (construccion de subconjuntos "al vuelo"). Si el automata
es determinista, el conjunto siempre tiene un solo estado.

Criterio de aceptacion: la cadena se acepta si, al terminar de leerla, al
menos uno de los estados alcanzados es final.

Contrato del modulo (ver registro.py): TIPO, NOMBRE, ETIQUETA_ESTADO,
construir_delta(), simular(), mostrar_resumen() y mostrar_traza().
"""
from nucleo.comun import VACIO, LAMBDA, clave_natural
from nucleo.modelo import Resultado

TIPO = "fa"
NOMBRE = "Automata finito"
ETIQUETA_ESTADO = "state"


# ---------------------------------------------------------------------------
# Construccion de delta
# ---------------------------------------------------------------------------
def construir_delta(transiciones):
    """
    A partir de las transiciones en crudo devuelve (delta, alfabeto, extra):
      delta    : {(origen, simbolo): set(destinos)}  ('' = lambda)
      alfabeto : simbolos de entrada, sin lambda
      extra    : {} (el AF no necesita datos adicionales)
    """
    delta = {}
    alfabeto = set()
    for t in transiciones:
        simbolo = t.get("read", VACIO)
        delta.setdefault((t["from"], simbolo), set()).add(t["to"])
        if simbolo != VACIO:
            alfabeto.add(simbolo)
    return delta, alfabeto, {}


def es_determinista(delta):
    """AFD: sin transiciones lambda y un unico destino por (estado, simbolo)."""
    return all(s != VACIO and len(d) == 1 for (_, s), d in delta.items())


def tiene_lambda(delta):
    return any(s == VACIO for (_, s) in delta)


# ---------------------------------------------------------------------------
# Simulacion
# ---------------------------------------------------------------------------
def clausura_lambda(conjunto, delta):
    """Estados alcanzables desde 'conjunto' usando solo transiciones lambda."""
    resultado = set(conjunto)
    pendientes = list(conjunto)
    while pendientes:
        estado = pendientes.pop()
        for destino in delta.get((estado, VACIO), ()):
            if destino not in resultado:
                resultado.add(destino)
                pendientes.append(destino)
    return resultado


def mostrar_conjunto(conjunto):
    """Conjunto de estados como texto ordenado: {q0, q2}."""
    if not conjunto:
        return "{}"
    return "{" + ", ".join(sorted(conjunto, key=clave_natural)) + "}"


def simular(cadena, automata):
    """
    Simula el automata sobre la cadena y devuelve un Resultado.

    traza: lista de (paso, simbolo, estados_actuales); el paso 0 tiene
    simbolo None. Se detiene antes de tiempo (RECHAZA) si el conjunto de
    estados queda vacio.
    """
    delta, finales = automata.delta, automata.finales

    actuales = clausura_lambda({automata.inicial}, delta)
    traza = [(0, None, frozenset(actuales))]

    for paso, simbolo in enumerate(cadena, start=1):
        siguientes = set()
        for estado in actuales:
            siguientes |= delta.get((estado, simbolo), set())
        siguientes = clausura_lambda(siguientes, delta)
        traza.append((paso, simbolo, frozenset(siguientes)))

        if not siguientes:
            motivo = (f"no hay transicion para el simbolo '{simbolo}' "
                      f"desde {mostrar_conjunto(actuales)}")
            return Resultado(False, motivo, traza)
        actuales = siguientes

    alcanzados = actuales & finales
    if alcanzados:
        motivo = f"se termino la cadena en el estado final {mostrar_conjunto(alcanzados)}"
        return Resultado(True, motivo, traza)
    motivo = (f"se termino la cadena en {mostrar_conjunto(actuales)}, "
              "que no contiene estados finales")
    return Resultado(False, motivo, traza)


# ---------------------------------------------------------------------------
# Salida por pantalla
# ---------------------------------------------------------------------------
def mostrar_resumen(automata):
    """Imprime el automata cargado."""
    clase = "AFD" if es_determinista(automata.delta) else "AFND"
    if tiene_lambda(automata.delta):
        clase += " con transiciones lambda"

    print(f"\n=== {NOMBRE} cargado ({clase}) ===")
    print("Estados   :", ", ".join(automata.estados[k]
                                   for k in sorted(automata.estados, key=int)))
    print("Alfabeto  :", ", ".join(sorted(automata.alfabeto)) or "(vacio)")
    print("Inicial   :", automata.inicial)
    print("Finales   :", ", ".join(sorted(automata.finales, key=clave_natural))
          or "(ninguno)")
    print("Transiciones (estado, simbolo) -> destinos:")
    ordenadas = sorted(automata.delta.items(),
                       key=lambda kv: (clave_natural(kv[0][0]), kv[0][1]))
    for (origen, simbolo), destinos in ordenadas:
        print(f"  ({origen}, {simbolo or LAMBDA}) -> {mostrar_conjunto(destinos)}")
    if tiene_lambda(automata.delta):
        print(f"  (el simbolo '{LAMBDA}' representa una transicion sin consumir entrada)")
    print("Criterio de aceptacion: terminar la cadena en un estado final")


def mostrar_traza(cadena, resultado):
    """Imprime el conjunto de estados alcanzado despues de cada simbolo."""
    print(f"\n{'Paso':<5}{'Simbolo':<9}Estados actuales")
    for paso, simbolo, estados in resultado.traza:
        print(f"{paso:<5}{simbolo if simbolo is not None else '-':<9}"
              f"{mostrar_conjunto(estados)}")
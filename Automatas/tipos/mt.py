"""
Maquinas de Turing (<type>turing</type>) disenadas en JFLAP.

Convenciones de JFLAP que se respetan:
  - Los estados son nodos <block> (nunca <state>).
  - <read/> vacio  -> la transicion se aplica sobre una celda en blanco.
  - <write/> vacio -> la transicion escribe un blanco (borra la celda).
  - <move> es L (izquierda), R (derecha) o S (se queda).
  - La cadena se coloca desde la celda 0 y el cabezal empieza en ella.

El blanco se guarda internamente como "" (ver comun.VACIO) y se muestra
como lambda.

Criterio de aceptacion: la cadena se acepta apenas la maquina alcanza un
estado final. Se rechaza si no existe transicion aplicable o si se supera
MAX_PASOS (posible bucle infinito).

La maquina es determinista: si el .jff tiene dos transiciones desde el
mismo estado leyendo el mismo simbolo, se rechaza el archivo (un duplicado
haria que una pise a la otra sin aviso).

Contrato del modulo (ver registro.py): TIPO, NOMBRE, ETIQUETA_ESTADO,
construir_delta(), simular(), mostrar_resumen() y mostrar_traza().
"""
from nucleo.comun import VACIO, LAMBDA, mostrar, clave_natural
from nucleo.modelo import ErrorAutomata, Resultado

TIPO = "turing"
NOMBRE = "Maquina de Turing"
ETIQUETA_ESTADO = "block"

MOVIMIENTOS = ("L", "R", "S")
MAX_PASOS = 100000    # proteccion contra maquinas que nunca se detienen
TRAZA_EXTREMOS = 25   # pasos que se muestran al principio y al final de la traza
VENTANA = 30          # celdas a cada lado del cabezal que se muestran de la cinta


# ---------------------------------------------------------------------------
# Construccion de delta
# ---------------------------------------------------------------------------
def construir_delta(transiciones):
    """
    A partir de las transiciones en crudo devuelve (delta, alfabeto, extra):
      delta    : {(origen, leido): (destino, escrito, movimiento)}  ('' = blanco)
      alfabeto : simbolos leidos o escritos, sin el blanco
      extra    : {}

    Lanza ErrorAutomata si hay dos transiciones con la misma clave
    (no determinismo) o si un movimiento no es L, R ni S.
    """
    delta = {}
    alfabeto = set()
    for t in transiciones:
        origen = t["from"]
        leido = t.get("read", VACIO)
        escrito = t.get("write", VACIO)
        mov = t.get("move", "S").upper() or "S"

        if mov not in MOVIMIENTOS:
            raise ErrorAutomata(
                f"movimiento '{mov}' invalido en la transicion desde {origen} "
                f"leyendo {mostrar(leido)} (se esperaba L, R o S).")
        if (origen, leido) in delta:
            raise ErrorAutomata(
                f"dos transiciones desde {origen} leyendo {mostrar(leido)}: "
                "la maquina debe ser determinista.")

        delta[(origen, leido)] = (t["to"], escrito, mov)
        alfabeto.update(s for s in (leido, escrito) if s != VACIO)
    return delta, alfabeto, {}


# ---------------------------------------------------------------------------
# Simulacion
# ---------------------------------------------------------------------------
def aplicar(cinta, cabezal, escrito, mov):
    """Escribe en la celda del cabezal, lo mueve y devuelve la nueva posicion.
    Escribir blanco borra la celda."""
    if escrito == VACIO:
        cinta.pop(cabezal, None)
    else:
        cinta[cabezal] = escrito
    if mov == "R":
        return cabezal + 1
    if mov == "L":
        return cabezal - 1
    return cabezal


def simular(cadena, automata):
    """
    Simula la maquina y devuelve un Resultado.

    traza: un registro por paso, (paso, origen, destino, leido, escrito, mov,
           posicion_del_cabezal_antes_de_mover). Es liviano a proposito:
           la cinta de cada paso se reconstruye al imprimir.
    datos: {"cinta": contenido final, "inicial": estado inicial,
            "cadena": cadena de entrada}.
    """
    delta, finales = automata.delta, automata.finales
    cinta = {i: c for i, c in enumerate(cadena)}
    cabezal = 0
    estado = automata.inicial
    traza = []

    def resultado(aceptada, motivo):
        datos = {"cinta": contenido_cinta(cinta), "inicial": automata.inicial,
                 "cadena": cadena}
        return Resultado(aceptada, motivo, traza, datos)

    while True:
        if estado in finales:
            return resultado(True, f"se alcanzo el estado final {estado}")

        if len(traza) >= MAX_PASOS:
            return resultado(False, "se supero el maximo de pasos "
                                    "(posible bucle infinito)")

        leido = cinta.get(cabezal, VACIO)
        if (estado, leido) not in delta:
            return resultado(False, f"no hay transicion para "
                                    f"({estado}, {mostrar(leido)})")

        destino, escrito, mov = delta[(estado, leido)]
        traza.append((len(traza) + 1, estado, destino, leido, escrito, mov, cabezal))
        cabezal = aplicar(cinta, cabezal, escrito, mov)
        estado = destino


def contenido_cinta(cinta):
    """Contenido de la cinta sin blancos en los extremos (los interiores se ven como lambda)."""
    if not cinta:
        return ""
    return "".join(cinta.get(i, VACIO) or LAMBDA
                   for i in range(min(cinta), max(cinta) + 1))


# ---------------------------------------------------------------------------
# Salida por pantalla
# ---------------------------------------------------------------------------
def texto_cinta(cinta, cabezal):
    """
    Cinta como texto, marcando la celda del cabezal entre [ ].
    Si la cinta es muy larga, muestra solo VENTANA celdas a cada lado del
    cabezal y marca con '...' lo recortado.
    """
    desde = min(min(cinta, default=cabezal), cabezal)
    hasta = max(max(cinta, default=cabezal), cabezal)
    recorta_izq = desde < cabezal - VENTANA
    recorta_der = hasta > cabezal + VENTANA
    if recorta_izq:
        desde = cabezal - VENTANA
    if recorta_der:
        hasta = cabezal + VENTANA

    partes = ["..." if recorta_izq else ""]
    for i in range(desde, hasta + 1):
        s = cinta.get(i, VACIO) or LAMBDA
        partes.append(f"[{s}]" if i == cabezal else f" {s} ")
    partes.append("..." if recorta_der else "")
    return "".join(partes)


def mostrar_resumen(automata):
    """Imprime la maquina cargada."""
    print(f"\n=== {NOMBRE} cargada ===")
    print("Estados   :", ", ".join(automata.estados[k]
                                   for k in sorted(automata.estados, key=int)))
    print("Alfabeto  :", ", ".join(sorted(automata.alfabeto)) or "(vacio)")
    print("Inicial   :", automata.inicial)
    print("Finales   :", ", ".join(sorted(automata.finales, key=clave_natural))
          or "(ninguno)")
    print("Transiciones (estado, leido) -> (destino, escrito, mov):")
    ordenadas = sorted(automata.delta.items(),
                       key=lambda kv: (clave_natural(kv[0][0]), kv[0][1]))
    for (origen, leido), (destino, escrito, mov) in ordenadas:
        print(f"  ({origen}, {mostrar(leido)}) -> ({destino}, {mostrar(escrito)}, {mov})")
    print(f"  (el simbolo '{LAMBDA}' representa la celda en blanco)")
    print("Criterio de aceptacion: alcanzar un estado final")


def mostrar_traza(cadena, resultado):
    """
    Imprime el recorrido paso a paso con la cinta y el cabezal. Si hay mas de
    2 * TRAZA_EXTREMOS pasos, muestra solo los primeros y los ultimos.
    """
    traza = resultado.traza
    print(f"\n{'Paso':<7}{'Estado':<8}Cinta")

    cinta = {i: c for i, c in enumerate(cadena)}
    cabezal = 0
    print(f"{0:<7}{resultado.datos['inicial']:<8}{texto_cinta(cinta, cabezal)}")

    total = len(traza)
    limite = 2 * TRAZA_EXTREMOS
    for paso, origen, destino, leido, escrito, mov, _ in traza:
        cabezal = aplicar(cinta, cabezal, escrito, mov)
        if total > limite and TRAZA_EXTREMOS < paso <= total - TRAZA_EXTREMOS:
            if paso == TRAZA_EXTREMOS + 1:
                print(f"  ... ({total - limite} pasos omitidos) ...")
            continue
        print(f"{paso:<7}{destino:<8}{texto_cinta(cinta, cabezal)}"
              f"   ({origen}, {mostrar(leido)} -> {mostrar(escrito)}, {mov})")

    print(f"\nCinta final: {resultado.datos['cinta']!r}")
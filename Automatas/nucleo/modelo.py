"""
Estructuras comunes a todos los tipos de automata.

Contrato entre las piezas del programa:
  - lector_jff.py construye un Automata.
  - tipos/<tipo>.py recibe ese Automata y devuelve siempre un Resultado.
  - interfaz.py solo conoce estas estructuras, nunca el tipo concreto.
"""
from dataclasses import dataclass, field


class ErrorAutomata(Exception):
    """Error al leer, validar o simular un automata.

    Se usa para todo lo que el usuario puede corregir en JFLAP (tipo no
    soportado, falta el estado inicial, transiciones duplicadas, etc.).
    La interfaz lo captura y muestra el mensaje tal cual.
    """


@dataclass
class Automata:
    """Automata ya leido desde un .jff, listo para simular.

    tipo      : valor de <type> en el .jff ("fa", "pda" o "turing").
    estados   : {id: nombre}, por ejemplo {"0": "q0", "1": "q1"}.
    alfabeto  : simbolos de entrada (sin el vacio).
    delta     : funcion de transicion; su forma depende del tipo:
                  fa     -> {(origen, simbolo): {destinos}}
                  pda    -> {(origen, leido, pop): [(destino, push), ...]}
                  turing -> {(origen, leido): (destino, escrito, movimiento)}
                El vacio se guarda siempre como "" (ver comun.VACIO).
    inicial   : nombre del estado inicial.
    finales   : nombres de los estados finales.
    extra     : datos propios de cada tipo (por ejemplo, el alfabeto de
                pila en AP).
    """
    tipo: str
    estados: dict
    alfabeto: set
    delta: dict
    inicial: str
    finales: set
    extra: dict = field(default_factory=dict)


@dataclass
class Resultado:
    """Resultado de simular una cadena; es igual para todos los tipos.

    aceptada : True si la cadena es aceptada.
    motivo   : explicacion corta del veredicto.
    traza    : recorrido paso a paso. Cada tipo decide que guarda y lo
               imprime con su propia mostrar_traza().
    datos    : informacion adicional del tipo (por ejemplo, la cinta
               final en MT o las configuraciones exploradas en AP).
    """
    aceptada: bool
    motivo: str
    traza: list = field(default_factory=list)
    datos: dict = field(default_factory=dict)
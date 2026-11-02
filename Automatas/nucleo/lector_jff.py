"""
Lectura de archivos .jff (JFLAP) independiente del tipo de automata.

Este modulo solo sabe de XML: lee <type>, los estados y las transiciones
"en crudo". No sabe armar delta ni simular; eso lo hace cada modulo de
tipos/. Lo unico que necesita de ellos es que le digan que etiqueta XML
representa un estado (<state> en AF y AP, <block> en MT), y lo recibe como
parametro para no depender de tipos/ ni de registro.py.

Cada <transition> se entrega como un diccionario generico:
    {"from": "q0", "to": "q1", "read": "a", "write": "", "move": "R", ...}
con origen y destino ya traducidos a nombre de estado, y el texto de cada
etiqueta hija (vacio = ""). Cada tipo toma solo los campos que necesita.
"""
import xml.etree.ElementTree as ET
from typing import NamedTuple

from nucleo.comun import texto
from nucleo.modelo import ErrorAutomata


class LecturaJFF(NamedTuple):
    """Contenido del .jff sin interpretar los campos propios de cada tipo."""
    tipo: str            # valor de <type>
    estados: dict        # {id: nombre}
    inicial: str         # nombre del estado inicial
    finales: set         # nombres de los estados finales
    transiciones: list   # [{"from": nombre, "to": nombre, "read": ..., ...}]


def leer_tipo(raiz):
    """Valor de <type>, o ErrorAutomata si el archivo no lo tiene."""
    tipo = texto(raiz.find("type"))
    if not tipo:
        raise ErrorAutomata("el archivo no tiene la etiqueta <type>.")
    return tipo


def leer_jff(nombre_archivo, etiquetas_estado):
    """
    Lee un .jff y devuelve una LecturaJFF.

    etiquetas_estado: {tipo: etiqueta_xml_de_estado}, por ejemplo
        {"fa": "state", "pda": "state", "turing": "block"}.
        Sus claves son los tipos soportados.

    Lanza ErrorAutomata si el archivo no se puede abrir, no es XML valido,
    el tipo no esta soportado, no hay estados, no hay exactamente un estado
    inicial, o hay ids/nombres repetidos o transiciones que apuntan a un
    estado inexistente.
    """
    try:
        raiz = ET.parse(nombre_archivo).getroot()
    except ET.ParseError as e:
        raise ErrorAutomata(f"el archivo no es un XML valido ({e}).")
    except OSError as e:
        raise ErrorAutomata(f"no se pudo abrir el archivo ({e.strerror or e}).")

    tipo = leer_tipo(raiz)
    if tipo not in etiquetas_estado:
        disponibles = ", ".join(sorted(etiquetas_estado))
        raise ErrorAutomata(
            f"tipo '{tipo}' no soportado; disponibles: {disponibles}.")

    automata = raiz.find("automaton")
    if automata is None:
        raise ErrorAutomata("el archivo no tiene la etiqueta <automaton>.")

    estados, inicial, finales = _leer_estados(automata, etiquetas_estado[tipo])
    transiciones = _leer_transiciones(automata, estados)
    return LecturaJFF(tipo, estados, inicial, finales, transiciones)


def _leer_estados(automata, etiqueta):
    """Devuelve ({id: nombre}, inicial, finales) leyendo los nodos 'etiqueta'."""
    estados = {}
    iniciales = []
    finales = set()

    for nodo in automata.findall(etiqueta):
        id_estado = nodo.get("id")
        if id_estado is None:
            raise ErrorAutomata(f"hay un <{etiqueta}> sin atributo id.")
        if id_estado in estados:
            raise ErrorAutomata(f"el id {id_estado} esta repetido.")

        nombre = nodo.get("name") or "q" + id_estado
        if nombre in estados.values():
            raise ErrorAutomata(f"el nombre de estado '{nombre}' esta repetido.")

        estados[id_estado] = nombre
        if nodo.find("initial") is not None:
            iniciales.append(nombre)
        if nodo.find("final") is not None:
            finales.add(nombre)

    if not estados:
        raise ErrorAutomata(f"el automata no tiene estados (<{etiqueta}>).")
    if not iniciales:
        raise ErrorAutomata("el automata no tiene estado inicial.")
    if len(iniciales) > 1:
        raise ErrorAutomata(
            "el automata tiene mas de un estado inicial: "
            + ", ".join(iniciales) + ".")
    return estados, iniciales[0], finales


def _leer_transiciones(automata, estados):
    """Lee cada <transition> como diccionario generico, con origen/destino por nombre."""
    transiciones = []
    for t in automata.findall("transition"):
        datos = {hijo.tag: texto(hijo) for hijo in t}
        for lado in ("from", "to"):
            id_estado = datos.get(lado, "")
            if id_estado not in estados:
                raise ErrorAutomata(
                    f"una transicion usa el estado inexistente "
                    f"'{id_estado}' en <{lado}>.")
            datos[lado] = estados[id_estado]
        transiciones.append(datos)
    return transiciones
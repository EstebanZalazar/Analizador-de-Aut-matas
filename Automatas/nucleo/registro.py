"""
Registro de tipos de automata: tabla de despacho {valor de <type>: modulo}.

Es el unico lugar que conoce que tipos existen. Para agregar un tipo nuevo
alcanza con crear su modulo en tipos/ e incluirlo en MODULOS.

Cada modulo debe cumplir el contrato:
    TIPO, NOMBRE, ETIQUETA_ESTADO,
    construir_delta(transiciones) -> (delta, alfabeto, extra),
    simular(cadena, automata)     -> Resultado,
    mostrar_resumen(automata),
    mostrar_traza(cadena, resultado)
"""
from nucleo.lector_jff import leer_jff
from nucleo.modelo import Automata, ErrorAutomata
from tipos import af, ap, mt

MODULOS = {m.TIPO: m for m in (af, ap, mt)}


def tipos_soportados():
    """Valores de <type> que se pueden analizar, ordenados."""
    return sorted(MODULOS)


def modulo_de(tipo):
    """Modulo que implementa el tipo dado, o ErrorAutomata si no existe."""
    if tipo not in MODULOS:
        raise ErrorAutomata(
            f"tipo '{tipo}' no soportado; disponibles: "
            + ", ".join(tipos_soportados()) + ".")
    return MODULOS[tipo]


def cargar_automata(nombre_archivo):
    """
    Lee un .jff, deduce su tipo por <type> y devuelve un Automata completo.
    Lanza ErrorAutomata ante cualquier problema del archivo.
    """
    etiquetas = {tipo: m.ETIQUETA_ESTADO for tipo, m in MODULOS.items()}
    lectura = leer_jff(nombre_archivo, etiquetas)

    modulo = modulo_de(lectura.tipo)
    delta, alfabeto, extra = modulo.construir_delta(lectura.transiciones)
    return Automata(lectura.tipo, lectura.estados, alfabeto, delta,
                    lectura.inicial, lectura.finales, extra)
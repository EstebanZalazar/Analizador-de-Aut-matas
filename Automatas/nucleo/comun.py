"""
Utilidades comunes a todos los analizadores de automatas.

Este modulo no importa nada del resto del proyecto: todo lo demas
(modelo, lector, tipos, interfaz) puede importarlo sin riesgo de
dependencias circulares.
"""
import os

CARPETA_RECURSOS = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "recursos")
)

# Simbolo vacio: internamente se guarda como "" y solo se muestra como lambda.
VACIO = ""
LAMBDA = "λ"


def texto(nodo):
    """Texto de un nodo XML sin espacios; vacio si no existe o esta vacio."""
    if nodo is None or nodo.text is None:
        return VACIO
    return nodo.text.strip()


def mostrar(simbolos):
    """Cadena para imprimir: lambda si esta vacia."""
    return simbolos if simbolos else LAMBDA


def clave_natural(nombre):
    """Orden natural para nombres tipo q2 < q10."""
    digitos = "".join(c for c in nombre if c.isdigit())
    return (nombre.rstrip("0123456789"), int(digitos) if digitos else -1, nombre)
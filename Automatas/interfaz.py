"""
Interfaz de consola del analizador universal.

No conoce ningun tipo de automata: pide el archivo, lo carga con el
registro y delega en el modulo del tipo la simulacion y la salida.

Flujo:
  1. El usuario ingresa el nombre del automata (.jff).
  2. Se deduce el tipo por <type> y se muestra el automata cargado.
  3. El usuario ingresa cadenas; se informa si son ACEPTADAS o RECHAZADAS.
  4. Al terminar, se puede cargar otro automata.
"""
import os

from nucleo import registro
from nucleo.comun import CARPETA_RECURSOS
from nucleo.modelo import ErrorAutomata


def pedir_archivo():
    """Pide un nombre (con o sin .jff) y devuelve la ruta existente."""
    while True:
        nombre = input("Nombre del automata (ej: Ej1 o Ej1.jff): ").strip()
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


def cargar():
    """Pide archivos hasta lograr cargar un automata valido."""
    while True:
        archivo = pedir_archivo()
        try:
            return registro.cargar_automata(archivo)
        except ErrorAutomata as e:
            print(f"Error al leer el archivo: {e}\n")


def analizar_cadenas(automata, modulo):
    """Bucle 'cadena -> simular -> resultado' para un automata ya cargado."""
    seguir = "s"
    while seguir == "s":
        cadena = input("\nIngrese la cadena a analizar (vacio = cadena vacia): ").strip()

        fuera = sorted(set(cadena) - automata.alfabeto)
        if fuera:
            print(f"Aviso: simbolos fuera del alfabeto del automata: {', '.join(fuera)}")

        try:
            resultado = modulo.simular(cadena, automata)
        except ErrorAutomata as e:
            print(f"Error al simular: {e}")
        else:
            modulo.mostrar_traza(cadena, resultado)
            veredicto = "ACEPTADA" if resultado.aceptada else "RECHAZADA"
            print(f"\nResultado: {veredicto} ({resultado.motivo})")

        seguir = input("\n¿Analizar otra cadena con este automata? (s/n): ").strip().lower()


def ejecutar():
    """Programa principal."""
    print("=== Analizador de automatas (JFLAP) ===")
    print("Tipos soportados:", ", ".join(registro.tipos_soportados()))
    otro = "s"
    while otro == "s":
        automata = cargar()
        modulo = registro.modulo_de(automata.tipo)
        modulo.mostrar_resumen(automata)
        analizar_cadenas(automata, modulo)
        otro = input("\n¿Cargar otro automata? (s/n): ").strip().lower()
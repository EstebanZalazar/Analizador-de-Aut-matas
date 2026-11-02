"""Punto de entrada: ejecutar desde la carpeta Automatas/ con `python main.py`."""
from interfaz import ejecutar

if __name__ == "__main__":
    try:
        ejecutar()
    except (KeyboardInterrupt, EOFError):
        print("\nPrograma finalizado.")
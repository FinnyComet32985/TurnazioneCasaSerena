import os
import sys

def resource_path(relative_path):
    """ Ottiene il percorso assoluto della risorsa, funzionante sia in dev che in PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
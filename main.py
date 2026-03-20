import sys
import os
from PyQt6.QtWidgets import QApplication
from db.initDB import init_db
from interfacciaDirigente import InterfacciaDirigente
from sistemaCaricamento import load_dipendenti, load_turni
from sistemaDipendenti.sistemaDipendenti import SistemaDipendenti
from sistemaTurnazione.turnazione import Turnazione

from interfacciaGrafica.main_window import MainWindow

def main():
    db_exist = os.path.isfile('./db/turnazione.db')

    if db_exist:
        sistema_dipendenti = load_dipendenti()
        turnazione = load_turni(sistema_dipendenti)
    else:
        init_db()
        sistema_dipendenti = SistemaDipendenti()
        turnazione = Turnazione()
    
    # Manteniamo l'istanza dell'interfaccia (o degli strati logici) pronta per quando 
    # la passeremo alla MainWindow per farla comunicare coi dati.
    interfaccia = InterfacciaDirigente(sistema_dipendenti, turnazione)

    # --- Avvio dell'Applicazione Desktop PyQt6 ---
    app = QApplication(sys.argv)
    window = MainWindow(interfaccia)
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
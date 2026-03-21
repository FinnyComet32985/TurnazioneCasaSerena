import sys
import os
import calendar
from datetime import date, datetime
from PyQt6.QtWidgets import QApplication
from db.initDB import init_db
from interfacciaDirigente import InterfacciaDirigente
from sistemaCaricamento import load_dipendenti, load_turni, load_last_update
from sistemaDipendenti.sistemaDipendenti import SistemaDipendenti
from sistemaTurnazione.turnazione import Turnazione

import sistemaSalvataggio
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
    
    # Caricamento configurazione (eseguito una sola volta all'avvio)
    turnazione.load_configuration()

    # Manteniamo l'istanza dell'interfaccia (o degli strati logici) pronta per quando 
    # la passeremo alla MainWindow per farla comunicare coi dati.
    interfaccia = InterfacciaDirigente(sistema_dipendenti, turnazione)

    check_update_assenze(sistema_dipendenti)

    # --- Avvio dell'Applicazione Desktop PyQt6 ---
    app = QApplication(sys.argv)
    window = MainWindow(interfaccia)
    window.show()
    sys.exit(app.exec())


def check_update_assenze(sistema_dipendenti: SistemaDipendenti):
    last_update = load_last_update()
    oggi = date.today()

    if last_update is None:
        # Se non esiste una data, impostiamo oggi come punto di partenza senza aggiornare
        sistemaSalvataggio.save_last_update(oggi.strftime("%Y-%m-%d"))
        return

    # Convertiamo la stringa DB in oggetto date
    data_ultimo_agg = datetime.strptime(last_update, "%Y-%m-%d").date()

    # Calcoliamo la fine del mese relativo all'ultimo aggiornamento
    giorni_nel_mese = calendar.monthrange(data_ultimo_agg.year, data_ultimo_agg.month)[1]
    fine_mese_last = date(data_ultimo_agg.year, data_ultimo_agg.month, giorni_nel_mese)

    # Logica per determinare il prossimo traguardo (Target) da raggiungere
    target_date = None
    
    if data_ultimo_agg < fine_mese_last:
        # Se l'ultimo aggiornamento non era un fine mese (es. prima installazione a metà mese),
        # il primo target è la fine di QUEL mese corrente.
        target_date = fine_mese_last
    else:
        # Se l'ultimo aggiornamento era già a fine mese, il target è la fine del mese successivo.
        target_date = get_next_month_end(data_ultimo_agg)

    # Ciclo di aggiornamento (recupera tutti i mesi persi fino ad oggi)
    while target_date <= oggi:
        print(f"Aggiornamento mensile rilevato per la data: {target_date}")
        sistema_dipendenti.matura_ratei_mensili()
        
        # Salviamo questo step come completato
        sistemaSalvataggio.save_last_update(target_date.strftime("%Y-%m-%d"))
        
        # Calcoliamo il prossimo target
        target_date = get_next_month_end(target_date)

def get_next_month_end(d: date) -> date:
    # Calcola il primo giorno del mese successivo
    if d.month == 12:
        next_month_first = date(d.year + 1, 1, 1)
    else:
        next_month_first = date(d.year, d.month + 1, 1)
    
    # Ottieni l'ultimo giorno di quel nuovo mese
    giorni_nel_mese = calendar.monthrange(next_month_first.year, next_month_first.month)[1]
    return date(next_month_first.year, next_month_first.month, giorni_nel_mese)


if __name__ == '__main__':
    main()
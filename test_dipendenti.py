import os
from db.initDB import init_db
from interfacciaDirigente import InterfacciaDirigente
from sistemaCaricamento import load_dipendenti, load_turni
from sistemaDipendenti.sistemaDipendenti import SistemaDipendenti
from sistemaTurnazione.turnazione import Turnazione

def main():
    # 1. Inizializziamo il sistema come succede già in main.py
    db_exist = os.path.isfile('./db/turnazione.db')

    if db_exist:
        sistema_dipendenti = load_dipendenti()
        turnazione = load_turni(sistema_dipendenti)
    else:
        init_db()
        sistema_dipendenti = SistemaDipendenti()
        turnazione = Turnazione()

    # 2. Istanziamo interfaccia dirigente
    interfaccia = InterfacciaDirigente(sistema_dipendenti, turnazione)

    print("=== TEST ELENCO DIPENDENTI ===")
    
    # 3. Metodo base: usare print_dipendenti() della classe InterfacciaDirigente (che stampa a terminale)
    # interfaccia.print_dipendenti()
    
    # 4. In alternativa (ed è quello che farai per la GUI UI):
    # Preleviamo direttamente l'array dei dipendenti e ne usiamo i dati nativamente:
    lista_dipendenti = sistema_dipendenti.get_lista_dipendenti()
    
    for dipendente in lista_dipendenti:
        # Nota: Stiamo chiamando direttamente la proprietà .val del Enum StatoDipendente se necessario, 
        # o semplicemente stampiamo l'oggetto enumeratore.
        print(f"ID: {dipendente.id_dipendente} | Nome: {dipendente.nome} | Cognome: {dipendente.cognome} | Stato: {dipendente.stato.name}")

if __name__ == '__main__':
    main()

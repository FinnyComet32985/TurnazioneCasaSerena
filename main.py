from db.initDB import init_db
from interfacciaDirigente import InterfacciaDirigente
from sistemaSalvataggio import load_dipendenti
from sistemaDipendenti.sistemaDipendenti import SistemaDipendenti
import os



def main():
    db_exist = os.path.isfile('./db/turnazione.db')

    if db_exist:
        lista_dipendenti = load_dipendenti()
        sistema_dipendenti = SistemaDipendenti(lista_dipendenti)
    else:
        init_db()
        sistema_dipendenti = SistemaDipendenti()
    
    # Istanziamo l'interfaccia passando il sistema (Dependency Injection)
    interfaccia = InterfacciaDirigente(sistema_dipendenti)
    #interfaccia.aggiungi_dipendente()
    #interfaccia.print_dipendenti()
    #interfaccia.rimuovi_dipendente()
    interfaccia.print_dipendenti()

    #interfaccia.aggiungi_assenza()
    interfaccia.print_assenze_dipendente()

if __name__ == '__main__':
    main()
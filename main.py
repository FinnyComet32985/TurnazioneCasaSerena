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

    action = -1

    while action != 0:
        print("\n\nScegli l'azione da eseguire:\n0.Esci\n1.Visualizza dipendenti\n2.Aggiungi dipendente\n3.Rimuovi dipendente\n4.Modifica dipendente\n5.Aggiungi assenza\n")
        action = int(input())
        print("\n")
        if action == 1:
            interfaccia.print_dipendenti()
        elif action == 2:
            interfaccia.aggiungi_dipendente()
        elif action == 3:
            interfaccia.rimuovi_dipendente()
        elif action == 4:
            interfaccia.modifica_dipendente()
        elif action == 5:
            interfaccia.aggiungi_assenza()

if __name__ == '__main__':
    main()
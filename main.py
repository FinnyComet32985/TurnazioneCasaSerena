from db.initDB import init_db
from interfacciaDirigente import InterfacciaDirigente
from sistemaCaricamento import load_dipendenti, load_turni
from sistemaDipendenti.sistemaDipendenti import SistemaDipendenti
from sistemaTurnazione.turnazione import Turnazione
import os




def main():
    db_exist = os.path.isfile('./db/turnazione.db')

    if db_exist:
        sistema_dipendenti = load_dipendenti()
        turnazione = load_turni(sistema_dipendenti)
    else:
        init_db()
        sistema_dipendenti = SistemaDipendenti()
        turnazione = Turnazione()
    
    # Istanziamo l'interfaccia passando le dipendenze di cui ha bisogno
    interfaccia = InterfacciaDirigente(sistema_dipendenti, turnazione)

    action = -1

    while action != 0:
        print("\n\nScegli l'azione da eseguire:\n0.Esci\n1.Visualizza dipendenti\n2.Aggiungi dipendente\n3.Rimuovi dipendente\n4.Modifica dipendente\n5.Visualizza assenze\n6.Aggiungi assenza\n7.Visualizza turnazione\n8.Aggiungi turno e assegnazione\n")
        action = int(input())
        print("\n")
        if action == 1:
            interfaccia.print_dipendenti()
        elif action == 2:
            interfaccia.assumi_dipendente()
        elif action == 3:
            interfaccia.rimuovi_dipendente()
        elif action == 4:
            interfaccia.modifica_dipendente()
        elif action == 5:
            interfaccia.print_assenze_dipendente()
        elif action == 6:
            interfaccia.aggiungi_assenza()
        elif action == 7:
            interfaccia.print_turni()
        elif action == 8:
            interfaccia.aggiungi_turno()

if __name__ == '__main__':
    main()
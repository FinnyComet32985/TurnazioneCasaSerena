from operator import truediv

from sistemaDipendenti.sistemaDipendenti import SistemaDipendenti

class InterfacciaDirigente:
    sistema_dipendenti: SistemaDipendenti


    def __init__(self, sistema_dipendenti: SistemaDipendenti):
        self.sistema_dipendenti = sistema_dipendenti


    def print_dipendenti(self):
        dipendenti = self.sistema_dipendenti.get_lista_dipendenti()
        for dipendente in dipendenti:
            print(dipendente.id_dipendente, dipendente.nome, dipendente.cognome)

    def aggiungi_dipendente(self):
        nome = input("Nome: ")
        cognome = input("Cognome: ")
        self.sistema_dipendenti.aggiungi_dipendente(nome, cognome)

    def rimuovi_dipendente(self):
        id_input = input("id del dipendente da rimuovere: ")
        
        if not id_input.isdigit():
            print("Errore: L'ID deve essere un numero intero.")
            return

        result = self.sistema_dipendenti.rimuovi_dipendente(int(id_input))

        if result is True:
            print("Dipendente rimosso con successo")
        else:
            print("Errore durante la rimozione")


    def modifica_dipendente(self):
        pass

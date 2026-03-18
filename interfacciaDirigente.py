from datetime import datetime
from sistemaDipendenti import sistemaDipendenti
from sistemaDipendenti.assenzaProgrammata import TipoAssenza
from sistemaDipendenti.dipendente import StatoDipendente
from sistemaDipendenti.sistemaDipendenti import SistemaDipendenti

class InterfacciaDirigente:
    sistema_dipendenti: SistemaDipendenti


    def __init__(self, sistema_dipendenti: SistemaDipendenti):
        self.sistema_dipendenti = sistema_dipendenti


    def print_dipendenti(self):
        dipendenti = self.sistema_dipendenti.get_lista_dipendenti()

        print("Dipendenti attivi:")
        for dipendente in dipendenti:
            if dipendente.stato is StatoDipendente.ASSUNTO:
                print(dipendente.id_dipendente, dipendente.nome, dipendente.cognome, dipendente.stato)

        print("\nDipendenti licenziati:")        
        for dipendente in dipendenti:
            if dipendente.stato is StatoDipendente.LICENZIATO:
                print(dipendente.id_dipendente, dipendente.nome, dipendente.cognome, dipendente.stato)

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


    
    def aggiungi_assenza(self):
        id_dipendente = input("su quale dipendente devi aggiungere l'assenza?")

        if not id_dipendente.isdigit():
            print("Errore: L'ID deve essere un numero intero.")
            return
        
        tipo_ass_input = input("scegli il tipo di assenza:\n1.FERIE\n2.ROL\n3.CERTIFICATO\n\n")

        if tipo_ass_input == "1":
            tipo_ass = TipoAssenza.FERIE
        elif tipo_ass_input == "2":
            tipo_ass = TipoAssenza.ROL
        elif tipo_ass_input == "3":
            tipo_ass = TipoAssenza.CERTIFICATO
        
        data_inizio_input = input("data inizio assenza (GG/MM/AAAA HH:MM): ")
        data_fine_input = input("data fine assenza (GG/MM/AAAA HH:MM): ")

        try:
            # Convertiamo da GG/MM/AAAA HH:MM a oggetto datetime
            dt_inizio = datetime.strptime(data_inizio_input, "%d/%m/%Y %H:%M")
            dt_fine = datetime.strptime(data_fine_input, "%d/%m/%Y %H:%M")
            
            # Convertiamo in stringa ISO per il DB (AAAA-MM-GG HH:MM:SS)
            str_inizio = dt_inizio.strftime("%Y-%m-%d %H:%M:%S")
            str_fine = dt_fine.strftime("%Y-%m-%d %H:%M:%S")
            
            # Passiamo le stringhe formattate e l'ID convertito in intero
            result = self.sistema_dipendenti.aggiungi_assenza(int(id_dipendente), tipo_ass, str_inizio, str_fine)

        except ValueError:
            print("Errore: Formato data non valido. Usa GG/MM/AAAA HH:MM")
            return

        if result is True:
            print("Assenza aggiunta con successo")
        else:
            print("Errore durante l'aggiunta dell'assenza")

    def print_assenze_dipendente(self):
        id_dipendente = input("su quale dipendente vuoi vedere le assenze?")

        if not id_dipendente.isdigit():
            print("Errore: L'ID deve essere un numero intero.")
            return

        assenze = self.sistema_dipendenti.get_assenze_dipendente(int(id_dipendente))

        for assenza in assenze:
            print(assenza.tipo, assenza.data_inizio, assenza.data_fine)
    
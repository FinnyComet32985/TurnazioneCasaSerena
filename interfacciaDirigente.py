from datetime import datetime
from sistemaDipendenti import sistemaDipendenti
from sistemaDipendenti.assenzaProgrammata import TipoAssenza
from sistemaDipendenti.dipendente import StatoDipendente
from sistemaDipendenti.sistemaDipendenti import SistemaDipendenti
from sistemaTurnazione import assegnazioneTurno
from sistemaTurnazione import turnazione
from sistemaTurnazione.fasciaOraria import TipoFascia
from sistemaTurnazione.turnazione import Turnazione
from sistemaTurnazione.sistemaGenerazione import SistemaGenerazione


class InterfacciaDirigente:
    sistema_dipendenti: SistemaDipendenti
    turnazione: Turnazione



    def __init__(self, sistema_dipendenti: SistemaDipendenti, turnazione: Turnazione):
        self.sistema_dipendenti = sistema_dipendenti
        self.turnazione = turnazione


    def print_dipendenti(self):
        dipendenti = self.sistema_dipendenti.get_lista_dipendenti()

        print("Dipendenti attivi:")
        for dipendente in dipendenti:
            if dipendente.stato is StatoDipendente.ASSUNTO:
                print(dipendente.id_dipendente, dipendente.nome, dipendente.cognome)

        print("\nDipendenti licenziati:")        
        for dipendente in dipendenti:
            if dipendente.stato is StatoDipendente.LICENZIATO:
                print(dipendente.id_dipendente, dipendente.nome, dipendente.cognome)

    def assumi_dipendente(self):
        nome = input("Nome: ")
        cognome = input("Cognome: ")
        self.sistema_dipendenti.assumi_dipendente(nome, cognome)

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
    
    def approva_turnazione_settimana(self):
        """
        Approva l'intera settimana, calcola i saldi e aggiorna le banche ore.
        """
        input_str = input("Inserisci la settimana da APPROVARE (anno settimana, es: 2025 2): ")
        try:
            parti = input_str.split()
            if len(parti) != 2: raise ValueError
            settimana_key = (int(parti[0]), int(parti[1]))
            
            confirm = input(f"Sei sicuro di voler approvare la settimana {settimana_key}? Questo aggiornerà la banca ore di tutti i dipendenti. (s/n): ")
            if confirm.lower() == 's':
                if self.turnazione.approva_settimana(self.sistema_dipendenti, settimana_key):
                    print("Settimana approvata con successo.")
        except ValueError:
            print("Formato non valido.")

    def riapri_turnazione_settimana(self):
        """
        Rollback: Riapre la settimana e stenta le ore dalla banca ore.
        """
        input_str = input("Inserisci la settimana da RIAPRIRE/MODIFICARE (anno settimana, es: 2025 2): ")
        try:
            parti = input_str.split()
            if len(parti) != 2: raise ValueError
            settimana_key = (int(parti[0]), int(parti[1]))
            
            confirm = input(f"ATTENZIONE: Stai per riaprire la settimana {settimana_key}. Le ore aggiunte alla banca ore verranno RIMOSSE. Procedere? (s/n): ")
            if confirm.lower() == 's':
                if self.turnazione.riapri_settimana(self.sistema_dipendenti, settimana_key):
                    print("Settimana riaperta. Ora puoi modificarla.")
        except ValueError:
            print("Formato non valido.")

    def genera_turnazione(self):
        """
        Comando per generare automaticamente la turnazione.
        """
        input_str = input("Inserisci la settimana da GENERARE (anno settimana, es: 2025 2): ")
        try:
            parti = input_str.split()
            if len(parti) != 2: raise ValueError
            anno, settimana = int(parti[0]), int(parti[1])

            generatore = SistemaGenerazione(self.turnazione, self.sistema_dipendenti)
            generatore.genera_turnazione_automatica(anno, settimana)
        except ValueError:
            print("Formato non valido.")

    def print_turni(self):
        input_str = input("inserisci la settimana di cui vuoi vedere i turni (anno settimana, es: 2025 2): ")
        
        try:
            parti = input_str.split()
            if len(parti) != 2:
                raise ValueError
            anno = int(parti[0])
            settimana = int(parti[1])
            settimana_key = (anno, settimana)
        except ValueError:
            print("Formato non valido. Inserire 'Anno Settimana' (es. 2025 5)")
            return

        settimana_dict = self.turnazione.get_turnazione_settimana(settimana_key)

        for data_turno, fasce in settimana_dict.items():
            print(f"\nDATA: {data_turno}")
            for tipo, fascia in fasce.items():
                status_flag = f"[{fascia.stato.name}]" if fascia.stato else ""
                dipendenti_assegnati = ", ".join([f"{a.dipendente.nome} {a.dipendente.cognome}" for a in fascia.assegnazioni])
                print(f"  - {tipo.value} {status_flag}: {dipendenti_assegnati if dipendenti_assegnati else 'Vuoto'}")




    def aggiungi_turno(self):
        data_turno = input("inserisci la data del turno da inserire (GG/MM/AAAA):")

        try:
            # Conversione stringa -> oggetto date
            dt_turno = datetime.strptime(data_turno, "%d/%m/%Y").date()
        except ValueError:
            print("Formato data non valido.")
            return

        tipo_fascia_input = input("scegli il tipo di fascia:\n1.MATTINA\n2.POMERIGGIO\n3.NOTTE\n4.RIPOSO\n\n")

        if tipo_fascia_input == "1":
            tipo_fascia = TipoFascia.MATTINA
        elif tipo_fascia_input == "2":
            tipo_fascia = TipoFascia.POMERIGGIO
        elif tipo_fascia_input == "3":
            tipo_fascia = TipoFascia.NOTTE
        elif tipo_fascia_input == "4":
            tipo_fascia = TipoFascia.RIPOSO
        else:
            print("Scelta non valida")
            return

        # Creazione del contenitore turno (FasciaOraria)
        self.turnazione.add_turno(dt_turno, tipo_fascia)
    
        # Assegnazione del dipendente
        id_dipendente = input("a quale dipendente vuoi assegnare il turno?")
        if not id_dipendente.isdigit():
            print("ID non valido")
            return

        # Per semplicità ora passiamo piano 0 e booleani False, in futuro si possono chiedere con input
        self.turnazione.assegna_turno(self.sistema_dipendenti, int(id_dipendente), dt_turno, tipo_fascia, piano=0, jolly=False, turno_breve=False)
    
    def rimuovi_turno(self):
        data_turno = input("inserisci la data del turno da rimuovere (GG/MM/AAAA):")

        try:
            dt_turno = datetime.strptime(data_turno, "%d/%m/%Y").date()
        except ValueError:
            print("Formato data non valido.")
            return

        tipo_fascia_input = input("scegli il tipo di fascia:\n1.MATTINA\n2.POMERIGGIO\n3.NOTTE\n4.RIPOSO\n\n")

        if tipo_fascia_input == "1":
            tipo_fascia = TipoFascia.MATTINA
        elif tipo_fascia_input == "2":
            tipo_fascia = TipoFascia.POMERIGGIO
        elif tipo_fascia_input == "3":
            tipo_fascia = TipoFascia.NOTTE
        else:
            print("Scelta non valida")
            return

        id_dipendente = input("ID del dipendente da rimuovere dal turno: ")
        if not id_dipendente.isdigit():
            print("ID non valido")
            return
            
        if self.turnazione.rimuovi_assegnazione(int(id_dipendente), dt_turno, tipo_fascia):
            print("Assegnazione rimossa con successo.")
        else:
            print("Errore durante la rimozione (Verifica che il turno esista e non sia approvato).")

    def print_turni_dip(self):
        input_str = input("inserisci la settimana di cui vuoi vedere i turni del dipendente (anno settimana, es: 2025 2): ")
        
        try:
            parti = input_str.split()
            if len(parti) != 2:
                raise ValueError
            anno = int(parti[0])
            settimana = int(parti[1])
            settimana_key = (anno, settimana)
        except ValueError:
            print("Formato non valido. Inserire 'Anno Settimana' (es. 2025 5)")
            return
        

        id_dipendente = input("su quale dipendente vuoi vedere i turni?")

        if not id_dipendente.isdigit():
            print("Errore: L'ID deve essere un numero intero.")
            return

        turn = self.turnazione.get_assegnazioni_dipendente(settimana_key, int(id_dipendente))

        for t in turn:
            print(t[0].data_turno, t[0].tipo, t[1].dipendente.nome, t[1].dipendente.cognome, t[1].piano, t[1].jolly, t[1].turnoBreve)
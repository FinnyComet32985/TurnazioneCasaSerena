from datetime import datetime

from sistemaDipendenti.assenzaProgrammata import AssenzaProgrammata, TipoAssenza
from sistemaDipendenti.dipendente import Dipendente, StatoDipendente
from sistemaSalvataggio import save_dipendente
import sistemaSalvataggio

class SistemaDipendenti:
    dipendenti : list[Dipendente]

    def __init__(self, lista_dipendenti: list[Dipendente] | None = None):
        if lista_dipendenti is not None:
            self.dipendenti = lista_dipendenti
        else:
            self.dipendenti = []


    def ripristina_dipendente(self, id_dipendente: int, nome: str, cognome: str, ferie_rimanenti: float, rol_rimanenti: float, banca_ore: float, stato_str: str):
        """Crea un'istanza di dipendente da dati grezzi (DB) e la aggiunge alla lista senza salvare su DB."""
        stato = StatoDipendente(stato_str) if stato_str else StatoDipendente.ASSUNTO
        
        dipendente = Dipendente(nome, cognome, stato, ferie_rimanenti, rol_rimanenti, banca_ore, [], id_dipendente)
        self.dipendenti.append(dipendente)


    def assumi_dipendente(self, nome: str, cognome: str, stato: StatoDipendente = StatoDipendente.ASSUNTO, ferie_rimanenti: float = 0, rol_rimanenti : float = 0, banca_ore: float = 0):
        # Salva nel DB e ottieni l'ID generato
        id_dip = save_dipendente(nome, cognome, stato.value, ferie_rimanenti, rol_rimanenti, banca_ore)

        dipendente = Dipendente(nome, cognome, stato, ferie_rimanenti, rol_rimanenti, banca_ore, [], id_dip)

        self.dipendenti.append(dipendente)

    def rimuovi_dipendente(self, id_dipendente: int):
        result = sistemaSalvataggio.remove_dipendente(id_dipendente)
        if result is True:
            # Cerchiamo l'oggetto dipendente nella lista controllando l'attributo id_dipendente
            for dipendente in self.dipendenti:
                if dipendente.id_dipendente == id_dipendente:
                    dipendente.stato = StatoDipendente.LICENZIATO
                    break
            return True
        else:
            return False

    def get_lista_dipendenti(self):
        return self.dipendenti

    def get_dipendente(self, id_dipendente: int):
        for dipendente in self.dipendenti:
            if dipendente.id_dipendente == id_dipendente:
                return dipendente
        return None

    def ripristina_assenza(self, id_dipendente: int, id_assenza: int, tipo_assenza_str: str, data_inizio: str, data_fine: str):
        """Ripristina un'assenza da dati grezzi e la associa al dipendente corretto."""
        for dipendente in self.dipendenti:
            if dipendente.id_dipendente == id_dipendente:
                # Creiamo l'oggetto assenza
                assenza = AssenzaProgrammata(
                    id_assenza=id_assenza,
                    data_inizio=data_inizio,
                    data_fine=data_fine,
                    tipo=tipo_assenza_str
                )
                dipendente.assenze_programmate.append(assenza)
                return True
        return False

    def aggiungi_assenza(self, id_dipendente:int, tipo_assenza: TipoAssenza, data_inizio: str, data_fine: str):

        eseguito = False

        # Cerchiamo l'oggetto dipendente nella lista
        for dipendente in self.dipendenti:
            if dipendente.id_dipendente == id_dipendente:
                # Salviamo nel DB
                id_db = sistemaSalvataggio.save_assenza(id_dipendente, tipo_assenza.value, data_inizio, data_fine)
                
                # Creiamo l'oggetto in memoria (passando il valore stringa dell'Enum)
                nuova_assenza = AssenzaProgrammata(data_inizio, data_fine, tipo_assenza.value, id_assenza=id_db)
                dipendente.assenze_programmate.append(nuova_assenza)
                
                # --- CALCOLO CONSUMO FERIE / ROL ---
                # Convertiamo le stringhe in datetime per calcolare la differenza
                fmt = "%Y-%m-%d %H:%M:%S"
                dt_inizio = datetime.strptime(data_inizio, fmt)
                dt_fine = datetime.strptime(data_fine, fmt)
                delta = dt_fine - dt_inizio
                
                if tipo_assenza == TipoAssenza.FERIE:
                    # Ferie calcolate in giorni. Se la differenza è < 24h ma copre un turno, conta come 1?
                    # Semplificazione: usiamo i giorni arrotondati + frazioni
                    giorni = delta.total_seconds() / 86400  # 86400 secondi in un giorno
                    # Arrotondiamo a 0.5 o intero per pulizia, o lasciamo float puro
                    dipendente.ferie_rimanenti = round(dipendente.ferie_rimanenti - giorni, 2)
                    
                elif tipo_assenza == TipoAssenza.ROL:
                    # ROL calcolati in ore
                    ore = delta.total_seconds() / 3600
                    dipendente.rol_rimanenti = round(dipendente.rol_rimanenti - ore, 2)
                
                # Aggiorniamo il saldo nel DB
                self.modifica_dipendente(dipendente.id_dipendente, dipendente.nome, dipendente.cognome, dipendente.ferie_rimanenti, dipendente.rol_rimanenti, dipendente.banca_ore)
                
                eseguito = True
                break
        
        return eseguito
        
    def get_assenze_dipendente(self, id_dipendente: int):
        for dipendente in self.dipendenti:
            if dipendente.id_dipendente == id_dipendente:
                return dipendente.get_assenze_programmate()
        return []

    def modifica_dipendente(self, id_dipendente: int, nome: str, cognome: str, ferie: float, rol: float, banca_ore: float = None):
        # Se banca_ore non è passato, recuperiamo quello attuale (per compatibilità chiamate vecchie)
        dip = self.get_dipendente(id_dipendente)
        if banca_ore is None and dip:
            banca_ore = dip.banca_ore
            
        result = sistemaSalvataggio.update_dipendente(id_dipendente, nome, cognome, ferie, rol, banca_ore)
        if result:
            if dip:
                dip.nome = nome
                dip.cognome = cognome
                dip.ferie_rimanenti = ferie
                dip.rol_rimanenti = rol
                dip.banca_ore = banca_ore
            return True
        return False
        
    def rimuovi_assenza(self, id_dipendente: int, id_assenza: int):
        result = sistemaSalvataggio.delete_assenza(id_assenza)
        if result:
            dip = self.get_dipendente(id_dipendente)
            if dip:
                dip.assenze_programmate = [a for a in dip.assenze_programmate if getattr(a, 'id_assenza', None) != id_assenza]
            return True
        return False

    def matura_ratei_mensili(self):
        """Aggiunge i ratei mensili (ferie e rol) a tutti i dipendenti attivi."""
        print("--- Esecuzione maturazione automatica ratei mensili ---")
        for dip in self.dipendenti:
            if dip.stato == StatoDipendente.ASSUNTO:
                # CCNL Cooperative Sociali (Calcolo esatto arrotondato)
                # FERIE: 26 giorni annui / 12 mesi
                dip.ferie_rimanenti = round(dip.ferie_rimanenti + (26 / 12), 2)
                # ROL: 32 ore annue / 12 mesi
                dip.rol_rimanenti = round(dip.rol_rimanenti + (32 / 12), 2)
                
                # Salvataggio su DB
                self.modifica_dipendente(
                    dip.id_dipendente, 
                    dip.nome, 
                    dip.cognome, 
                    dip.ferie_rimanenti, 
                    dip.rol_rimanenti,
                    dip.banca_ore
                )

    def aggiorna_banca_ore(self, id_dipendente: int, delta_ore: float):
        """
        Aggiorna la banca ore di un dipendente aggiungendo (o sottraendo) un delta.
        Salva immediatamente la modifica sul database.
        """
        dip = self.get_dipendente(id_dipendente)
        if dip:
            dip.banca_ore += delta_ore
            # Arrotondiamo per evitare problemi di floating point
            dip.banca_ore = round(dip.banca_ore, 2)
            
            # Salviamo la modifica completa del dipendente
            self.modifica_dipendente(
                dip.id_dipendente,
                dip.nome,
                dip.cognome,
                dip.ferie_rimanenti,
                dip.rol_rimanenti,
                dip.banca_ore
            )
            return True
        return False
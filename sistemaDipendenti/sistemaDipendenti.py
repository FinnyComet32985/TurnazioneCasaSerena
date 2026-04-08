from datetime import datetime, date

from sistemaDipendenti.assenzaProgrammata import AssenzaProgrammata, TipoAssenza
from sistemaDipendenti.dipendente import Dipendente, StatoDipendente
from sistemaDipendenti.variazioneBancaOre import VariazioneBancaOre
from sistemaSalvataggio import save_dipendente
import sistemaSalvataggio

class SistemaDipendenti:
    dipendenti : list[Dipendente]

    def __init__(self, lista_dipendenti: list[Dipendente] | None = None):
        if lista_dipendenti is not None:
            self.dipendenti = lista_dipendenti
        else:
            self.dipendenti = []


    def ripristina_dipendente(self, id_dipendente: int, nome: str, cognome: str, ferie_rimanenti: float, rol_rimanenti: float, banca_ore: float, stato_str: str, variazioni: list = None):
        """Crea un'istanza di dipendente da dati grezzi (DB) e la aggiunge alla lista senza salvare su DB."""
        stato = StatoDipendente(stato_str) if stato_str else StatoDipendente.ASSUNTO
        
        dipendente = Dipendente(nome, cognome, stato, ferie_rimanenti, rol_rimanenti, banca_ore, [], id_dipendente)
        if variazioni:
            dipendente.variazioni_banca_ore = variazioni
        self.dipendenti.append(dipendente)


    def assumi_dipendente(self, nome: str, cognome: str, stato: StatoDipendente = StatoDipendente.ASSUNTO, ferie_rimanenti: float = 0, rol_rimanenti : float = 0):
        # Salva nel DB e ottieni l'ID generato
        id_dip = save_dipendente(nome, cognome, stato.value, ferie_rimanenti, rol_rimanenti)

        dipendente = Dipendente(nome, cognome, stato, ferie_rimanenti, rol_rimanenti, 0, [], id_dip)

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

    def riassumi_dipendente(self, id_dipendente: int):
        result = sistemaSalvataggio.riassumi_dipendente(id_dipendente)
        if result is True:
            # Cerchiamo l'oggetto dipendente nella lista controllando l'attributo id_dipendente
            for dipendente in self.dipendenti:
                if dipendente.id_dipendente == id_dipendente:
                    dipendente.stato = StatoDipendente.ASSUNTO
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
                # --- CONTROLLO SOVRAPPOSIZIONI ---
                fmt = "%Y-%m-%d %H:%M:%S"
                new_start = datetime.strptime(data_inizio, fmt)
                new_end = datetime.strptime(data_fine, fmt)

                for ass in dipendente.assenze_programmate:
                    ex_start = datetime.strptime(ass.data_inizio, fmt)
                    ex_end = datetime.strptime(ass.data_fine, fmt)
                    if (new_start <= ex_end) and (new_end >= ex_start):
                        return "SOVRAPPOSIZIONE"

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
                    # Calcolo giorni inclusivi: se inizio e fine sono lo stesso giorno, è 1 giorno di ferie.
                    giorni = (dt_fine.date() - dt_inizio.date()).days + 1
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
        dip = self.get_dipendente(id_dipendente)
            
        result = sistemaSalvataggio.update_dipendente(id_dipendente, nome, cognome, ferie, rol)
        if result:
            if dip:
                dip.nome = nome
                dip.cognome = cognome
                dip.ferie_rimanenti = ferie
                dip.rol_rimanenti = rol
                # Il saldo banca_ore non viene più aggiornato direttamente qui
            return True
        return False
        
    def rimuovi_assenza(self, id_dipendente: int, id_assenza: int):
        result = sistemaSalvataggio.delete_assenza(id_assenza)
        if result:
            dip = self.get_dipendente(id_dipendente)
            if dip:
                # Trova l'assenza da rimuovere per riaccreditare le ore/giorni
                absence_to_remove = None
                for ass in dip.assenze_programmate:
                    if getattr(ass, 'id_assenza', None) == id_assenza:
                        absence_to_remove = ass
                        break

                if absence_to_remove:
                    fmt = "%Y-%m-%d %H:%M:%S"
                    dt_inizio = datetime.strptime(absence_to_remove.data_inizio, fmt)
                    dt_fine = datetime.strptime(absence_to_remove.data_fine, fmt)
                    
                    if absence_to_remove.tipo == TipoAssenza.FERIE.value:
                        giorni = (dt_fine.date() - dt_inizio.date()).days + 1
                        dip.ferie_rimanenti = round(dip.ferie_rimanenti + giorni, 2)
                    elif absence_to_remove.tipo == TipoAssenza.ROL.value:
                        ore = (dt_fine - dt_inizio).total_seconds() / 3600
                        dip.rol_rimanenti = round(dip.rol_rimanenti + ore, 2)
                    
                    # Aggiorna il saldo del dipendente nel database
                    sistemaSalvataggio.update_dipendente(dip.id_dipendente, dip.nome, dip.cognome, dip.ferie_rimanenti, dip.rol_rimanenti)
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

    def verifica_assenza(self, id_dipendente: int, data_check: date) -> bool:
        """Restituisce True se il dipendente è in assenza (Ferie, Malattia, ecc.) nella data specificata."""
        dip = self.get_dipendente(id_dipendente)
        if not dip:
            return False
        
        fmt = "%Y-%m-%d %H:%M:%S"
        for assenza in dip.assenze_programmate:
            # Conversione date stringa -> datetime -> date
            dt_inizio = datetime.strptime(assenza.data_inizio, fmt).date()
            dt_fine = datetime.strptime(assenza.data_fine, fmt).date()
            if dt_inizio <= data_check <= dt_fine:
                return True
        return False

    def get_statistiche_oggi(self) -> tuple[int, int, int]:
        """Restituisce una tupla: (Totale Dipendenti, In Ferie Oggi, In Certificato Oggi)"""
        totale = 0
        ferie = 0
        certificato = 0
        
        oggi = date.today()
        fmt = "%Y-%m-%d %H:%M:%S"

        for dip in self.dipendenti:
            if dip.stato == StatoDipendente.ASSUNTO:
                totale += 1
                
                # Controlliamo se è in assenza OGGI
                for ass in dip.assenze_programmate:
                    dt_inizio = datetime.strptime(ass.data_inizio, fmt).date()
                    dt_fine = datetime.strptime(ass.data_fine, fmt).date()
                    
                    if dt_inizio <= oggi <= dt_fine:
                        if ass.tipo == TipoAssenza.FERIE.value:
                            ferie += 1
                        elif ass.tipo == TipoAssenza.CERTIFICATO.value:
                            certificato += 1
        
        return totale, ferie, certificato
    
    def aggiungi_variazione_banca_ore(self, id_dipendente: int, delta_ore: float, key: str, descrizione: str = ""):
        """ aggiunge la variazione e chiama la funzione per salvarla nel db """
        dip = self.get_dipendente(id_dipendente)
        if not dip:
            return False

        # Se la variazione è 0, è inutile salvarla nel DB o tenerla nello storico in memoria.
        # Se esisteva già un record per questa settimana, lo rimuoviamo del tutto per pulizia.
        if delta_ore == 0:
            return self.elimina_variazione_banca_ore(id_dipendente, key)
        
        if sistemaSalvataggio.save_variazione_banca_ore(id_dipendente, key, delta_ore, descrizione):
            # Aggiornamento in memoria
            esiste = False
            for var in dip.variazioni_banca_ore:
                if var.key == key:
                    old_val = var.valore
                    var.valore = delta_ore
                    var.descrizione = descrizione
                    dip.banca_ore = round(dip.banca_ore - old_val + delta_ore, 2)
                    esiste = True
                    break
            
            if not esiste:
                nuova_var = VariazioneBancaOre(key, delta_ore, descrizione)
                dip.variazioni_banca_ore.append(nuova_var)
                dip.banca_ore = round(dip.banca_ore + delta_ore, 2)
            return True
        return False

    def elimina_variazione_banca_ore(self, id_dipendente: int, key: str):
        """ rimuove la variazione dal db e aggiorna lo stato in memoria """
        dip = self.get_dipendente(id_dipendente)
        if not dip:
            return False
        
        if sistemaSalvataggio.delete_variazione_banca_ore(id_dipendente, key):
            for i, var in enumerate(dip.variazioni_banca_ore):
                if var.key == key:
                    dip.banca_ore = round(dip.banca_ore - var.valore, 2)
                    dip.variazioni_banca_ore.pop(i)
                    break
            return True
        return False

    def get_movimenti_banca_ore(self, id_dipendente: int):
        """ recupera i movimenti dal database e restituisce oggetti VariazioneBancaOre """
        rows = sistemaSalvataggio.get_variazioni_banca_ore(id_dipendente)
        movimenti = []
        for row in rows:
            # row[0] = key, row[1] = valore, row[2] = descrizione
            movimenti.append(VariazioneBancaOre(row[0], row[1], row[2]))
        
        # Ordiniamo per inserimento decrescente (le più recenti in alto)
        movimenti.reverse()
        return movimenti
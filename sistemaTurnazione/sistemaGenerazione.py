import random
from datetime import date, timedelta, datetime
from typing import List

import sistemaSalvataggio
from sistemaDipendenti.dipendente import Dipendente, StatoDipendente
from sistemaDipendenti.sistemaDipendenti import SistemaDipendenti
from sistemaTurnazione.fasciaOraria import TipoFascia, StatoFascia
from sistemaTurnazione.turnazione import Turnazione

class SistemaGenerazione:
    
    def __init__(self, turnazione: Turnazione, sistema_dipendenti: SistemaDipendenti):
        self.turnazione = turnazione
        self.sistema_dipendenti = sistema_dipendenti

    def _sort_candidati_per_rotazione(self, candidati: List[Dipendente], tipo_fascia: TipoFascia, anno: int, settimana: int) -> List[Dipendente]:
        """
        Ordina i candidati con un sistema a punteggio multiplo (Gerarchico):
        1. Recency: Chi non svolge questo turno da più tempo (data minore) ha la priorità.
        2. Carico Settimanale: Chi ha lavorato meno ore nella settimana corrente ha la priorità.
        3. Banca Ore: Chi ha la banca ore più bassa (o negativa) ha la priorità per recuperare.
        """
        candidati_con_punteggio = []
        
        for dip in candidati:
            last_date_str = sistemaSalvataggio.get_data_ultimo_turno(dip.id_dipendente, tipo_fascia.value)
            
            if last_date_str:
                # Ha già fatto questo turno in passato -> data effettiva
                last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
            else:
                # Mai fatto questo turno -> data molto vecchia (priorità massima)
                last_date = date.min 

            # Calcoliamo le ore già lavorate questa settimana per evitare di caricare tutto su uno a inizio settimana
            ore_settimana = self.turnazione._get_ore_lavorate_settimana(dip.id_dipendente, (anno, settimana))

            # La tupla rappresenta il punteggio. Python ordina le tuple elemento per elemento.
            # (Data Vecchia < Data Recente) -> Vince Data Vecchia
            # (Ore Basse < Ore Alte) -> Vince Ore Basse
            # (Banca Ore Bassa < Banca Ore Alta) -> Vince Banca Ore Bassa
            candidati_con_punteggio.append((dip, last_date, ore_settimana, dip.banca_ore))
        
        # Mischiamo prima di ordinare per gestire i pareggi (es. due persone con date.min o stessa data) in modo non deterministico
        random.shuffle(candidati_con_punteggio)
        
        # Ordiniamo usando la chiave composta
        # x[1] = last_date
        # x[2] = ore_settimana
        # x[3] = banca_ore
        candidati_con_punteggio.sort(key=lambda x: (x[1], x[2], x[3]))
        
        return [item[0] for item in candidati_con_punteggio]

    def _applica_turni_brevi(self, anno: int, settimana: int):
        """
        Post-processing: Assegna 1 turno breve (6h) per ogni Mattina.
        Criteri:
        1. Solo chi NON fa notti nella settimana corrente.
        2. Priorità a chi ha più ore settimanali (per ridurle).
        3. Priorità a chi ha più banca ore.
        """
        print("--- Applicazione Turni Brevi (MATTINA) ---")
        primo_giorno = date.fromisocalendar(anno, settimana, 1)
        giorni_settimana = [primo_giorno + timedelta(days=i) for i in range(7)]
        
        for giorno in giorni_settimana:
            fascia = self.turnazione.turnazioneSettimanale.get((anno, settimana), {}).get(giorno, {}).get(TipoFascia.MATTINA)
            if not fascia or not fascia.assegnazioni:
                continue

            # Se c'è già un turno breve assegnato (es. manualmente), saltiamo questo giorno
            if any(a.turnoBreve for a in fascia.assegnazioni):
                continue
                
            candidati = []
            for assegnazione in fascia.assegnazioni:
                dip = assegnazione.dipendente
                
                # 1. Filtro: Chi non fa notte questa settimana
                assegnazioni_settimana = self.turnazione.get_assegnazioni_dipendente((anno, settimana), dip.id_dipendente)
                fa_notte = any(item[0].tipo == TipoFascia.NOTTE for item in assegnazioni_settimana)
                if fa_notte:
                    continue
                    
                # 2. Metriche: Ore settimana e Banca Ore
                ore_sett = self.turnazione._get_ore_lavorate_settimana(dip.id_dipendente, (anno, settimana))
                candidati.append((assegnazione, ore_sett, dip.banca_ore))
            
            if candidati:
                # Ordiniamo: Chi ha più ore settimanali e più banca ore viene per primo
                candidati.sort(key=lambda x: (x[1], x[2]), reverse=True)
                best_ass = candidati[0][0]
                
                # Applichiamo la modifica
                best_ass.turnoBreve = True
                if sistemaSalvataggio.set_turno_breve(fascia.id_turno, best_ass.dipendente.id_dipendente, True):
                    print(f"  -> Assegnato turno breve a {best_ass.dipendente.nome} {best_ass.dipendente.cognome} il {giorno}")
                else:
                    best_ass.turnoBreve = False # Rollback in memoria

    def genera_turnazione_automatica(self, anno: int, settimana: int) -> bool:
        """
        Genera automaticamente i turni per la settimana specificata.
        Priorità: 1. Notti, 2. Turni Diurni (Mattina/Pomeriggio).
        Criterio: Rotazione (data ultimo turno).
        """
        print(f"--- Inizio Generazione Automatica Settimana {anno}-{settimana} ---")
        
        # 1. Inizializza la griglia vuota (se non esiste)
        if not self.turnazione.inizializza_settimana(anno, settimana):
            return False

        primo_giorno = date.fromisocalendar(anno, settimana, 1)
        giorni_settimana = [primo_giorno + timedelta(days=i) for i in range(7)]

        # Definizione dell'ordine di riempimento: PRIMA LE NOTTI (Vincolo forte per il riposo del giorno dopo)
        # POI i turni diurni.
        fasi_generazione = [
            [TipoFascia.NOTTE],
            [TipoFascia.MATTINA, TipoFascia.POMERIGGIO]
        ]

        for fase in fasi_generazione:
            for giorno in giorni_settimana:
                for tipo_fascia in fase:
                    
                    target_operatori = self.turnazione.limiti_fascia[tipo_fascia]
                    
                    # Controlliamo quanti ne abbiamo già (nel caso di rigenerazione parziale)
                    fascia = self.turnazione.turnazioneSettimanale.get((anno, settimana), {}).get(giorno, {}).get(tipo_fascia)
                    count_attuale = len(fascia.assegnazioni) if fascia else 0

                    while count_attuale < target_operatori:
                        candidati = self.turnazione.get_candidati_disponibili(self.sistema_dipendenti, giorno, tipo_fascia)
                        candidati_ordinati = self._sort_candidati_per_rotazione(candidati, tipo_fascia, anno, settimana)
                        
                        assigned = False
                        for cand in candidati_ordinati:
                            try:
                                self.turnazione.assegna_turno(self.sistema_dipendenti, cand.id_dipendente, giorno, tipo_fascia, stato=StatoFascia.GENERATA)
                                count_attuale += 1
                                assigned = True
                                break # Passa al prossimo slot vuoto
                            except ValueError:
                                continue # Se l'assegnazione fallisce (es. trigger DB), prova il prossimo candidato
                        
                        if not assigned:
                            print(f"WARNING: Impossibile trovare candidati validi per {tipo_fascia.value} del {giorno}. (Slot {count_attuale+1}/{target_operatori})")
                            break # Esce dal while per evitare loop infinito su questo slot, passa al prossimo turno
        
        self._assegna_riposi_mancanti(anno, settimana)

        # Post-Processing: Turni Brevi
        self._applica_turni_brevi(anno, settimana)
        
        print("--- Generazione Completata ---")
        return True

    def _assegna_riposi_mancanti(self, anno: int, settimana: int):
        """
        Post-processing: Delega al metodo centralizzato di riempimento riposi.
        """
        print("--- Assegnazione Riposi Mancanti ---")
        self.turnazione.riempi_riposi_settimana(self.sistema_dipendenti, (anno, settimana))
import random
from datetime import date, timedelta, datetime
from typing import List

import sistemaSalvataggio
from sistemaDipendenti.dipendente import Dipendente
from sistemaDipendenti.sistemaDipendenti import SistemaDipendenti
from sistemaTurnazione.fasciaOraria import TipoFascia
from sistemaTurnazione.turnazione import Turnazione

class SistemaGenerazione:
    
    def __init__(self, turnazione: Turnazione, sistema_dipendenti: SistemaDipendenti):
        self.turnazione = turnazione
        self.sistema_dipendenti = sistema_dipendenti

    def _sort_candidati_per_rotazione(self, candidati: List[Dipendente], tipo_fascia: TipoFascia) -> List[Dipendente]:
        """
        Ordina i candidati in base alla 'Recency':
        Chi non svolge questo tipo di turno da più tempo (data minore) ha la priorità (punteggio migliore).
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

            candidati_con_punteggio.append((dip, last_date))
        
        # Mischiamo prima di ordinare per gestire i pareggi (es. due persone con date.min o stessa data) in modo non deterministico
        random.shuffle(candidati_con_punteggio)
        
        # Ordiniamo per data crescente (il più vecchio vince)
        candidati_con_punteggio.sort(key=lambda x: x[1])
        
        return [item[0] for item in candidati_con_punteggio]

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
                    
                    target_operatori = self.turnazione.LIMITI_FASCIA[tipo_fascia]
                    
                    # Controlliamo quanti ne abbiamo già (nel caso di rigenerazione parziale)
                    fascia = self.turnazione.turnazioneSettimanale.get((anno, settimana), {}).get(giorno, {}).get(tipo_fascia)
                    count_attuale = len(fascia.assegnazioni) if fascia else 0

                    while count_attuale < target_operatori:
                        candidati = self.turnazione.get_candidati_disponibili(self.sistema_dipendenti, giorno, tipo_fascia)
                        candidati_ordinati = self._sort_candidati_per_rotazione(candidati, tipo_fascia)
                        
                        assigned = False
                        for cand in candidati_ordinati:
                            try:
                                self.turnazione.assegna_turno(self.sistema_dipendenti, cand.id_dipendente, giorno, tipo_fascia)
                                count_attuale += 1
                                assigned = True
                                break # Passa al prossimo slot vuoto
                            except ValueError:
                                continue # Se l'assegnazione fallisce (es. trigger DB), prova il prossimo candidato
                        
                        if not assigned:
                            print(f"WARNING: Impossibile trovare candidati validi per {tipo_fascia.value} del {giorno}. (Slot {count_attuale+1}/{target_operatori})")
                            break # Esce dal while per evitare loop infinito su questo slot, passa al prossimo turno
        
        print("--- Generazione Completata ---")
        return True
import random
from datetime import date, timedelta, datetime
from typing import List

import sistemaSalvataggio
from sistemaDipendenti.dipendente import Dipendente, StatoDipendente
from sistemaDipendenti.sistemaDipendenti import SistemaDipendenti
from sistemaTurnazione.fasciaOraria import TipoFascia, StatoFascia
from sistemaTurnazione.turnazione import Turnazione
from sistemaTurnazione.festivita_util import get_festivita_italiane, get_vigilie, calcola_pasqua

class SistemaGenerazione:
    
    def __init__(self, turnazione: Turnazione, sistema_dipendenti: SistemaDipendenti):
        self.turnazione = turnazione
        self.sistema_dipendenti = sistema_dipendenti

    def _is_festivo(self, d: date) -> bool:
        """Riconosce le festività fisse e le vigilie per la rotazione."""
        return d in get_festivita_italiane(d.year) or d in get_vigilie(d.year)

    def _get_date_collegate(self, d: date) -> List[date]:
        """Ritorna le date 'opposte' per la rotazione delle feste (es: 25 e 26 dic)."""
        coppie = [
            ((12, 24), (12, 25)),
            ((12, 25), (12, 26)),
            ((12, 31), (1, 1))
        ]
        
        pasqua = calcola_pasqua(d.year)
        if d == pasqua: return [pasqua + timedelta(days=1)]
        if d == pasqua + timedelta(days=1): return [pasqua]

        m, g = d.month, d.day
        for c1, c2 in coppie:
            if (m, g) == c1: return [d + timedelta(days=1)]
            if (m, g) == c2: return [d - timedelta(days=1)]
        return []

    def _sort_candidati_per_rotazione(self, candidati: List[Dipendente], tipo_fascia: TipoFascia, anno: int, settimana: int, giorno_data: date) -> List[Dipendente]:
        """
        Ordina i candidati con un sistema a punteggio multiplo (Gerarchico):
        1. Recency: Chi non svolge questo turno da più tempo (data minore) ha la priorità.
        2. Sequenza/Varietà: Evitiamo sequenze lunghe e favoriamo rotazioni intelligenti (es. Pomeriggio -> Notte).
        3. Carico Settimanale: Chi ha lavorato meno ore nella settimana corrente ha la priorità.
        4. Banca Ore: Chi ha la banca ore più bassa (o negativa) ha la priorità per recuperare.
        """
        candidati_con_punteggio = []

        is_holiday = self._is_festivo(giorno_data)
        linked_dates = self._get_date_collegate(giorno_data)
        
        for dip in candidati:
            # 1. Recency specifica per questo tipo di fascia
            last_date_raw = sistemaSalvataggio.get_data_ultimo_turno(dip.id_dipendente, tipo_fascia.value)
            if isinstance(last_date_raw, str):
                last_date = datetime.strptime(last_date_raw, "%Y-%m-%d").date()
            elif last_date_raw:
                # Se è già un oggetto date (comportamento standard di psycopg2)
                last_date = last_date_raw
            else:
                last_date = date.min

            # 2. Analisi sequenza recente (Cosa ha fatto ieri/l'altro ieri?)
            consecutive_count = 0
            last_type = None
            
            # Recuperiamo le assegnazioni già fatte in questa settimana per il dipendente
            ass_sett = self.turnazione.get_assegnazioni_dipendente((anno, settimana), dip.id_dipendente)
            ass_sett.sort(key=lambda x: x[0].data_turno, reverse=True) # Dalla più recente
            
            if ass_sett:
                for fascia, _ in ass_sett:
                    if last_type is None:
                        last_type = fascia.tipo
                        consecutive_count = 1
                    elif fascia.tipo == last_type:
                        consecutive_count += 1
                    else:
                        break

            # Calcolo Punteggio Varietà (Minore è meglio)
            varieta_score = 0
            
            # PENALITÀ: Se sta facendo lo stesso turno, penalizziamo pesantemente dopo il 2° giorno
            if last_type == tipo_fascia:
                varieta_score += (consecutive_count * 20)
            
            # BONUS "ESCAPE": Se ha fatto Pomeriggi, diamogli la Notte con priorità per sbloccarlo
            if tipo_fascia == TipoFascia.NOTTE and last_type == TipoFascia.POMERIGGIO:
                varieta_score -= 30 # Altissima priorità per rompere il ciclo dei pomeriggi
            
            # BONUS ROTAZIONE: Se ha fatto Mattina, può passare a Pomeriggio
            if tipo_fascia == TipoFascia.POMERIGGIO and last_type == TipoFascia.MATTINA:
                varieta_score -= 10

            # 3. Carico Ore
            ore_settimana = self.turnazione._get_ore_lavorate_settimana(dip.id_dipendente, (anno, settimana))

            # 4. Logica Festività (Rotazione Coppie)
            holiday_penalty = 0
            if is_holiday:
                # Se è una festa, penalizziamo chi ha lavorato nella data collegata (es. Natale vs S.Stefano)
                for d_link in linked_dates:
                    a_l, s_l, _ = d_link.isocalendar()
                    ass_link = self.turnazione.get_assegnazioni_dipendente((a_l, s_l), dip.id_dipendente)
                    if any(f.data_turno == d_link and f.tipo != TipoFascia.RIPOSO for f, ass in ass_link):
                        holiday_penalty += 50 # Penalità alta per favorire la rotazione

            # Ordinamento Gerarchico:
            # 1. holiday_penalty (Rispetto delle feste a rotazione)
            # 2. varieta_score (Priorità assoluta alla rotazione richiesta)
            # 3. last_date (Chi non fa questo turno da più tempo)
            # 4. ore_settimana (Meno ore lavorate)
            # 5. banca_ore (Banca ore più bassa)
            candidati_con_punteggio.append((
                dip, 
                holiday_penalty,
                varieta_score, 
                last_date, 
                ore_settimana, 
                dip.banca_ore
            ))
        
        random.shuffle(candidati_con_punteggio)
        candidati_con_punteggio.sort(key=lambda x: (x[1], x[2], x[3], x[4], x[5]))
        
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

    def genera_turnazione_automatica(self, anno: int, settimana: int, genera_piani: bool = True, date_notti_extra: List[date] = None) -> bool:
        """
        Genera automaticamente i turni per la settimana specificata.
        Priorità: 1. Notti, 2. Turni Diurni (Mattina/Pomeriggio).
        Criterio: Rotazione (data ultimo turno).
        """
        if date_notti_extra is None:
            date_notti_extra = []
            
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
                    # Costruiamo gli "slot" basandoci sui limiti per piano/fascia configurati
                    config_fascia = self.turnazione.limiti_piani_fascia.get(tipo_fascia, {})
                    slots_obiettivi = [] # Lista di (piano, is_jolly)
                    
                    for p in [0, 1, 2]:
                        for _ in range(config_fascia.get(p, 0)):
                            slots_obiettivi.append((p, False))
                    
                    for _ in range(config_fascia.get('jolly', 0)):
                        slots_obiettivi.append((1, True)) # Jolly default su P1

                    target_operatori = len(slots_obiettivi)
                    if target_operatori == 0 and tipo_fascia == TipoFascia.NOTTE:
                        target_operatori = 1
                        slots_obiettivi = [(0, False)]
                        
                    if tipo_fascia == TipoFascia.NOTTE and giorno in date_notti_extra:
                        target_operatori += 1
                        slots_obiettivi.append((0, False))

                    # Controlliamo quanti ne abbiamo già (nel caso di rigenerazione parziale)
                    fascia_obj = self.turnazione.turnazioneSettimanale.get((anno, settimana), {}).get(giorno, {}).get(tipo_fascia)
                    count_attuale = len(fascia_obj.assegnazioni) if fascia_obj else 0
                    
                    while count_attuale < target_operatori:
                        candidati = self.turnazione.get_candidati_disponibili(self.sistema_dipendenti, giorno, tipo_fascia)
                        candidati_ordinati = self._sort_candidati_per_rotazione(candidati, tipo_fascia, anno, settimana, giorno)
                        
                        assigned = False
                        # Recuperiamo la configurazione dello slot corrente
                        piano_slot, is_jolly_slot = slots_obiettivi[count_attuale]

                        for cand in candidati_ordinati:
                            try:
                                self.turnazione.assegna_turno(
                                    self.sistema_dipendenti, 
                                    cand.id_dipendente, 
                                    giorno, 
                                    tipo_fascia, 
                                    piano=piano_slot if genera_piani else 0, 
                                    jolly=is_jolly_slot if genera_piani else False,
                                    stato=StatoFascia.GENERATA,
                                    commit=False # In memoria durante la generazione
                                )
                                count_attuale += 1
                                assigned = True
                                break # Passa al prossimo slot vuoto
                            except ValueError:
                                continue # Se l'assegnazione fallisce (es. trigger DB), prova il prossimo candidato
                        
                        if not assigned:
                            print(f"WARNING: Impossibile trovare candidati validi per {tipo_fascia.value} del {giorno}. (Slot {count_attuale+1}/{target_operatori})")
                            break # Esce dal while per evitare loop infinito su questo slot, passa al prossimo turno
        
        self._assegna_riposi_mancanti(anno, settimana, commit=False)

        # Post-Processing: Turni Brevi
        self._applica_turni_brevi(anno, settimana)
        
        # --- COMMIT FINALE BATCH ---
        print("--- Salvataggio massivo su Database ---")
        pending_assignments = []
        settimana_dict = self.turnazione.turnazioneSettimanale.get((anno, settimana), {})
        for giorno_dict in settimana_dict.values():
            for fascia in giorno_dict.values():
                for ass in fascia.assegnazioni:
                    # Esportiamo solo l'essenziale per il DB
                    pending_assignments.append((
                        ass.dipendente.id_dipendente,
                        fascia.id_turno,
                        ass.piano,
                        ass.jolly,
                        ass.turnoBreve
                    ))
        
        if not sistemaSalvataggio.save_assegnazioni_batch(pending_assignments):
            print("ERRORE CRITICO: Il salvataggio batch è fallito. I vincoli del database sono stati violati.")
            return False

        print("--- Generazione Completata ---")
        return True

    def _assegna_riposi_mancanti(self, anno: int, settimana: int, commit: bool = True):
        """
        Post-processing: Delega al metodo centralizzato di riempimento riposi.
        """
        print("--- Assegnazione Riposi Mancanti ---")
        self.turnazione.riempi_riposi_settimana(self.sistema_dipendenti, (anno, settimana), commit=commit)
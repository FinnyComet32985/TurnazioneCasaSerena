import random
from datetime import date, timedelta, datetime
from typing import List

import sistemaSalvataggio
from sistemaDipendenti.dipendente import Dipendente
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

        # Ordinamento Gerarchico:
            # 1. holiday_penalty (Rispetto delle feste a rotazione)
            # 2. varieta_score (Priorità assoluta alla rotazione richiesta)
            # 3. last_date (Chi non fa questo turno da più tempo)
            # 4. banca_ore (Banca ore più bassa)
            # 5. ore_settimana (Meno ore lavorate)
        """
        candidati_con_punteggio = []

        is_holiday = self._is_festivo(giorno_data)
        linked_dates = self._get_date_collegate(giorno_data)
        
        for dip in candidati:
            # 1. Recency specifica per questo tipo di fascia
            last_date_str = sistemaSalvataggio.get_data_ultimo_turno(dip.id_dipendente, tipo_fascia.value)
            if last_date_str:
                last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
            else:
                last_date = date.min 

            # 2. Analisi sequenza immediata (Cosa ha fatto nei giorni precedenti?)
            consecutive_count = 0
            tipo_ieri = None

            # Guardiamo indietro i giorni precedenti a prescindere dalla settimana
            for i in range(1, 5):
                d_prec = giorno_data - timedelta(days=i)
                a_p, s_p, _ = d_prec.isocalendar()
                ass_prec = self.turnazione.get_assegnazioni_dipendente((a_p, s_p), dip.id_dipendente)
                
                # Cerchiamo il turno di quel giorno specifico
                turno_giorno = next((f.tipo for f, ass in ass_prec if f.data_turno == d_prec and f.tipo != TipoFascia.RIPOSO), None)
                
                if i == 1:
                    tipo_ieri = turno_giorno
                
                if turno_giorno == tipo_fascia:
                    consecutive_count += 1
                else:
                    break # Sequenza interrotta

            # Calcolo Punteggio Varietà (Minore è meglio)
            varieta_score = 0
            
            # PENALITÀ SEQUENZA: Evitiamo che lo stesso turno si ripeta troppo
            if consecutive_count == 1:
                varieta_score += 15 # Leggera preferenza a cambiare tipo di turno
            elif consecutive_count >= 2:
                # Se ne ha già fatti 2 consecutivi, applichiamo una penalità drastica per evitare il 3°
                varieta_score += 150
                if tipo_fascia == TipoFascia.POMERIGGIO:
                    varieta_score += 100 # I pomeriggi pesano ancora di più per la stanchezza
            
            # BONUS "ESCAPE": Se ha fatto Pomeriggi, favoriamo la Notte per spezzare il ciclo
            if tipo_fascia == TipoFascia.NOTTE and tipo_ieri == TipoFascia.POMERIGGIO:
                varieta_score -= 40 # Alta priorità per "sbloccarlo" dai pomeriggi
            
            # BONUS ROTAZIONE STANDARD
            if tipo_fascia == TipoFascia.POMERIGGIO and tipo_ieri == TipoFascia.MATTINA:
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

            candidati_con_punteggio.append((
                dip, 
                holiday_penalty,
                varieta_score, 
                last_date, 
                ore_settimana, 
                dip.banca_ore
            ))
        
        random.shuffle(candidati_con_punteggio)
        candidati_con_punteggio.sort(key=lambda x: (x[1], x[2], x[3], x[5], x[4]))
        
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
                    
                # 2. Metriche: Ore settimana, Banca Ore e Piano attuale
                ore_sett = self.turnazione._get_ore_lavorate_settimana(dip.id_dipendente, (anno, settimana))
                # Priorità a chi è già al Piano 1 per mantenere l'equilibrio della generazione
                is_already_p1 = 1 if assegnazione.piano == 1 else 0
                candidati.append((assegnazione, ore_sett, dip.banca_ore, is_already_p1))
            
            if candidati:
                # Ordiniamo: Preferenza Piano 1, poi chi ha più ore settimanali e più banca ore
                candidati.sort(key=lambda x: (x[3], x[1], x[2]), reverse=True)
                best_ass = candidati[0][0]
                
                # Applichiamo la modifica: il turno breve deve essere svolto al Piano 1
                best_ass.turnoBreve = True
                best_ass.piano = 1
                if sistemaSalvataggio.set_turno_breve(fascia.id_turno, best_ass.dipendente.id_dipendente, True):
                    print(f"  -> Assegnato turno breve a {best_ass.dipendente.nome} {best_ass.dipendente.cognome} il {giorno}")
                else:
                    best_ass.turnoBreve = False # Rollback in memoria

    def genera_turnazione_automatica(self, anno: int, settimana: int, genera_piani: bool = True) -> bool:
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
                    # Costruiamo gli "slot" basandoci sui limiti per piano/fascia configurati
                    config_fascia = self.turnazione.limiti_piani_fascia.get(tipo_fascia, {})
                    slots_obiettivi = [] # Lista di (piano, is_jolly)
                    
                    for p in [0, 1, 2]:
                        for _ in range(config_fascia.get(p, 0)):
                            slots_obiettivi.append((p, False))
                    
                    for _ in range(config_fascia.get('jolly', 0)):
                        slots_obiettivi.append((1, True)) # Jolly default su P1

                    target_operatori = len(slots_obiettivi)

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
                                    stato=StatoFascia.GENERATA
                                )
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
        #self._applica_turni_brevi(anno, settimana)
        
        print("--- Generazione Completata ---")
        return True

    def _assegna_riposi_mancanti(self, anno: int, settimana: int):
        """
        Post-processing: Delega al metodo centralizzato di riempimento riposi.
        """
        print("--- Assegnazione Riposi Mancanti ---")
        self.turnazione.riempi_riposi_settimana(self.sistema_dipendenti, (anno, settimana))
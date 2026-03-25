from copy import deepcopy
from datetime import date, datetime, timedelta, time
from typing import List
from sistemaDipendenti.sistemaDipendenti import SistemaDipendenti
from sistemaDipendenti.dipendente import Dipendente
from sistemaTurnazione.assegnazioneTurno import AssegnazioneTurno
from sistemaTurnazione.fasciaOraria import FasciaOraria, TipoFascia, StatoFascia
import sistemaSalvataggio

class Turnazione:
    # Struttura:
    # Livello 1 Key: (Anno, SettimanaISO) es. (2026, 2)
    # Livello 2 Key: Data specifica es. 2026-01-08
    # Livello 3 Key: TipoFascia (MATTINA, POMERIGGIO...)
    # Value Finale: Oggetto FasciaOraria
    turnazioneSettimanale: dict[tuple[int, int], dict[date, dict[TipoFascia, FasciaOraria]]]

    MAX_ORE : int = 38
    MAX_ORE_MEDIA_MENSILE: int = 48
    ORE_TURNI: dict = {
        "MATTINA": 7,
        "MATTINA CORTA": 6,
        "POMERIGGIO": 7,
        "NOTTE": 10,
        "RIPOSO": 0
    }
    ORARIO_TURNI: dict = {
        "MATTINA": [7, 14],
        "MATTINA CORTA": [7, 13],
        "POMERIGGIO": [14, 21],
        "NOTTE": [21, 7]
    }

    PAUSA_TRA_TURNI: int = 11
    RIPOSO_SETTIMANALE_MIN: int = 24 # Ore consecutive
    
    # Variabili Configurazione (Inizializzate nel costruttore)
    max_jolly_per_turno: int
    max_dipendenti_per_piano: int
    limiti_fascia: dict

    def __init__(self, turnazioneSettimanale: dict[tuple[int, int], dict[date, dict[TipoFascia, FasciaOraria]]] | None = None):
        if turnazioneSettimanale is not None:
            self.turnazioneSettimanale = turnazioneSettimanale
        else:
            self.turnazioneSettimanale = {}
        
        # Configurazione Default (inizializzata in memoria per evitare query DB in loop)
        self.max_jolly_per_turno = 1
        self.max_dipendenti_per_piano = 3
        self.limiti_fascia = {
            TipoFascia.MATTINA: 7,
            TipoFascia.POMERIGGIO: 6,
            TipoFascia.NOTTE: 1
        }

    def load_configuration(self):
        """Carica i parametri di configurazione dal DB o imposta i default."""
        # Jolly
        val = sistemaSalvataggio.get_config('max_jolly')
        self.max_jolly_per_turno = int(val) if val else 1
        
        # Piano
        val = sistemaSalvataggio.get_config('max_piano')
        self.max_dipendenti_per_piano = int(val) if val else 3

        # Limiti Fascia
        self.limiti_fascia = {}
        # Default values
        defaults = {
            TipoFascia.MATTINA: 7,
            TipoFascia.POMERIGGIO: 6,
            TipoFascia.NOTTE: 1
        }
        
        for tf in [TipoFascia.MATTINA, TipoFascia.POMERIGGIO, TipoFascia.NOTTE]:
            val = sistemaSalvataggio.get_config(f'limit_{tf.value}')
            if val:
                self.limiti_fascia[tf] = int(val)
            else:
                self.limiti_fascia[tf] = defaults.get(tf, 0)
    
    # loading dei turni del DB
    def ripristina_fascia(self, id_turno: int, data_str: str, tipo_fascia_str: str, stato_str: str):
        """Ricostruisce l'oggetto FasciaOraria e lo inserisce nella struttura dati corretta."""
        
        # Conversione dati
        # Assumiamo che la data arrivi come stringa "YYYY-MM-DD" dal DB
        if isinstance(data_str, str):
            data_turno = datetime.strptime(data_str, "%Y-%m-%d").date()
        else:
            data_turno = data_str # Caso in cui sia già oggetto date
            
        tipo_fascia = TipoFascia(tipo_fascia_str)
        stato = StatoFascia(stato_str)

        # Creazione oggetto
        fascia = FasciaOraria(data_turno, tipo_fascia, assegnazioni=[], stato=stato, id_turno=id_turno)

        # Calcolo chiavi per il dizionario (Anno, Settimana)
        anno, settimana, _ = data_turno.isocalendar()
        settimana_key = (anno, settimana)

        # Inserimento nella struttura
        self.turnazioneSettimanale.setdefault(settimana_key, {}).setdefault(data_turno, {})[tipo_fascia] = fascia

    def ripristina_assegnazione(self, id_turno: int, dipendente: Dipendente, piano: int, jolly: bool, turno_breve: bool):
        """Cerca la fascia oraria corretta tramite ID e aggiunge l'assegnazione."""
        
        # Poiché la struttura è organizzata per Data e non per ID, dobbiamo cercare la fascia.
        # Nota: Questo potrebbe essere lento se ci sono molti dati, ma avviene solo all'avvio.
        for settimana_dict in self.turnazioneSettimanale.values():
            for giorno_dict in settimana_dict.values():
                for fascia in giorno_dict.values():
                    if getattr(fascia, 'id_turno', None) == id_turno:
                        assegnazione = AssegnazioneTurno(dipendente, turnoBreve=turno_breve, piano=piano, jolly=jolly)
                        fascia.ripristina_assegnazione(assegnazione)
                        return True
        return False

    def get_turnazione_settimana(self, settimana_key: tuple[int, int]) -> dict[date, dict[TipoFascia, FasciaOraria]]:
        return self.turnazioneSettimanale.get(settimana_key, {})

    def inizializza_settimana(self, anno: int, settimana: int) -> bool:
        """
        Crea i turni vuoti (MATTINA, POMERIGGIO, NOTTE) per tutti i giorni della settimana specificata.
        """
        try:
            # Calcola il primo giorno (Lunedì) della settimana ISO
            primo_giorno = date.fromisocalendar(anno, settimana, 1)
            
            for i in range(7):
                giorno_corrente = primo_giorno + timedelta(days=i)
                # Creiamo le 3 fasce principali (il RIPOSO è un concetto assegnato al dipendente, non un turno lavorativo generato)
                self.add_turno(giorno_corrente, TipoFascia.MATTINA, StatoFascia.GENERATA)
                self.add_turno(giorno_corrente, TipoFascia.POMERIGGIO, StatoFascia.GENERATA)
                self.add_turno(giorno_corrente, TipoFascia.NOTTE, StatoFascia.GENERATA)
            return True
        except Exception as e:
            print(f"Errore inizializzazione settimana: {e}")
            return False

    def add_turno(self, data_turno: date, tipo_fascia: TipoFascia, stato: StatoFascia = StatoFascia.VUOTA) :
        """
        Aggiunge una nuova fascia oraria alla turnazione, salvandola prima nel database.
        """
        anno, settimana_iso, _ = data_turno.isocalendar()
        settimana_key = (anno, settimana_iso)

        # Controllo anticipato: se la fascia esiste già in memoria, non la ricreiamo nel DB.
        if tipo_fascia in self.turnazioneSettimanale.get(settimana_key, {}).get(data_turno, {}):
            return settimana_key

        # 1. Salva il turno nel database e ottieni l'ID
        id_turno_db = sistemaSalvataggio.save_turno(data_turno, tipo_fascia.value, stato.value)

        if id_turno_db is None:
            print(f"Errore: Impossibile salvare il turno per {data_turno} {tipo_fascia.value} nel database.")
            return False

        # 2. Crea l'oggetto FasciaOraria con l'ID ottenuto
        fascia_oraria = FasciaOraria(
            data_turno=data_turno,
            tipo=tipo_fascia,
            stato=stato,
            id_turno=id_turno_db
        )

        # 3. Aggiungi la FasciaOraria alla struttura dati in memoria
        # Se la fascia esiste già in memoria, non sovrascriverla per non perdere le assegnazioni caricate/aggiunte
        settimana_dict = self.turnazioneSettimanale.setdefault(settimana_key, {})
        giorno_dict = settimana_dict.setdefault(data_turno, {})
        
        if tipo_fascia not in giorno_dict:
            giorno_dict[tipo_fascia] = fascia_oraria
        
        return settimana_key

    def _check_max_ore_settimanali(self, id_dipendente: int, settimana_key: tuple[int, int], tipo_fascia: TipoFascia, turno_breve: bool) -> list[bool, bool | None]:
        """
        Verifica se il dipendente ha superato il monte ore massimo settimanale.
        """
        asseg_dip = self.get_assegnazioni_dipendente(settimana_key, id_dipendente)
        ore_settimanali = 0

        # calcoliamo le ore già programmate
        for asseg in asseg_dip:
            fascia_obj: FasciaOraria = asseg[0]
            if fascia_obj.tipo == TipoFascia.MATTINA and asseg[1].turnoBreve:
                ore_settimanali += self.ORE_TURNI["MATTINA CORTA"]
            else:
                ore_settimanali += self.ORE_TURNI[fascia_obj.tipo.value]

        if ore_settimanali > self.MAX_ORE:
            return [False, False] # il secondo bool "False" indica che la violazione non è provocata dal nuovo turno (esiste già prima dell'inserimento del nuovo turno)

        # aggiungiamo le ore del nuovo turno da aggiungere
        if tipo_fascia == TipoFascia.MATTINA and turno_breve:
            ore_settimanali += self.ORE_TURNI["MATTINA CORTA"]
        else:
            ore_settimanali += self.ORE_TURNI[tipo_fascia.value]

        if ore_settimanali > self.MAX_ORE:
            return [False, True] # il secondo bool "True" indica che la violazione è provocata direttamente dall'inserimento del nuovo turno 

        return [True, None]

    def _get_ore_lavorate_settimana(self, id_dipendente: int, settimana_key: tuple[int, int]) -> float:
        """Helper function to calculate total hours worked by an employee in a week."""
        assegnazioni = self.get_assegnazioni_dipendente(settimana_key, id_dipendente)
        ore_lavorate = 0
        for fascia, assegnazione in assegnazioni:
            if fascia.tipo == TipoFascia.RIPOSO:
                continue
            
            if fascia.tipo == TipoFascia.MATTINA and assegnazione.turnoBreve:
                ore_lavorate += self.ORE_TURNI["MATTINA CORTA"]
            else:
                ore_lavorate += self.ORE_TURNI.get(fascia.tipo.value, 0)
        return ore_lavorate

    def calcola_saldo_ore_settimanale(self, id_dipendente: int, settimana_key: tuple[int, int]) -> float:
        """
        Calcola il saldo ore di un dipendente per una data settimana (ore lavorate - 38).
        Un risultato positivo indica ore da aggiungere alla banca ore.
        Un risultato negativo indica ore da recuperare (sottrarre dalla banca ore).
        """
        ore_lavorate = self._get_ore_lavorate_settimana(id_dipendente, settimana_key)
        return ore_lavorate - self.MAX_ORE # MAX_ORE is 38

    def _check_media_ore_4_mesi(self, id_dipendente: int, data_riferimento: date, nome_dipendente: str = "") -> bool:
        """
        Controlla la media delle ore lavorative nelle ultime 16 settimane (circa 4 mesi)
        per verificare il rispetto del limite di 48 ore settimanali medie.
        """
        NUM_SETTIMANE_MEDIA = 16
        ore_totali_periodo = 0
        
        settimane_controllate = set() # Per evitare di calcolare due volte la stessa settimana

        # Itera all'indietro per un numero sufficiente di giorni per coprire 16 settimane
        for i in range(NUM_SETTIMANE_MEDIA * 7 + 7): 
            data_target = data_riferimento - timedelta(days=i)
            anno, settimana, _ = data_target.isocalendar()
            settimana_key_target = (anno, settimana)

            if settimana_key_target not in settimane_controllate:
                ore_lavorate_settimana = self._get_ore_lavorate_settimana(id_dipendente, settimana_key_target)
                ore_totali_periodo += ore_lavorate_settimana
                settimane_controllate.add(settimana_key_target)
            
            if len(settimane_controllate) >= NUM_SETTIMANE_MEDIA:
                break
                
        media_settimanale = ore_totali_periodo / NUM_SETTIMANE_MEDIA
        
        if media_settimanale > self.MAX_ORE_MEDIA_MENSILE:
            nome_str = f"dal dipendente {nome_dipendente} (ID {id_dipendente})" if nome_dipendente else f"dal dipendente ID {id_dipendente}"
            print(f"ATTENZIONE LEGALE: La media di ore lavorate {nome_str} nelle ultime {NUM_SETTIMANE_MEDIA} settimane è {media_settimanale:.2f}, superando il limite di {self.MAX_ORE_MEDIA_MENSILE}h.")
            return False
            
        return True

    def _check_riposo_settimanale(self, settimana_key: tuple[int, int], id_dipendente: int, data_nuovo_turno: date, tipo_nuovo_turno: TipoFascia, turno_breve: bool) -> bool:
        """
        Verifica se esiste almeno un periodo di riposo di 24h consecutive associato alla settimana di lavoro,
        controllando anche i turni a cavallo con la settimana precedente e successiva.
        """
        # --- 1. Costruisce la lista dei segmenti di lavoro per la settimana corrente, incluso il nuovo turno ---
        assegnazioni = self.get_assegnazioni_dipendente(settimana_key, id_dipendente)
        
        # Costruiamo la lista di tutti i segmenti lavorativi (inizio, fine)
        segmenti_lavoro = []
        
        # Aggiungiamo i turni esistenti
        for item in assegnazioni:
            fascia: FasciaOraria = item[0]
            assegnazione: AssegnazioneTurno = item[1]
            if fascia.tipo == TipoFascia.RIPOSO: 
                continue
            
            orari_key = fascia.tipo.value
            if fascia.tipo == TipoFascia.MATTINA and assegnazione.turnoBreve:
                orari = self.ORARIO_TURNI["MATTINA CORTA"]
            else:
                orari = self.ORARIO_TURNI[orari_key]

            start = datetime.combine(fascia.data_turno, time(hour=orari[0]))
            end = datetime.combine(fascia.data_turno, time(hour=orari[1]))
            if orari[1] < orari[0]: 
                end += timedelta(days=1) # Notte
            
            segmenti_lavoro.append((start, end))
            
        # Aggiungiamo il turno ipotetico
        if tipo_nuovo_turno != TipoFascia.RIPOSO:
            if tipo_nuovo_turno == TipoFascia.MATTINA and turno_breve:
                orari_new = self.ORARIO_TURNI["MATTINA CORTA"]
            else:
                orari_new = self.ORARIO_TURNI[tipo_nuovo_turno.value]

            start_new = datetime.combine(data_nuovo_turno, time(hour=orari_new[0]))
            end_new = datetime.combine(data_nuovo_turno, time(hour=orari_new[1]))
            if orari_new[1] < orari_new[0]: 
                end_new += timedelta(days=1)
            segmenti_lavoro.append((start_new, end_new))
            
        if not segmenti_lavoro:
            return True # Se non ci sono turni di lavoro nella settimana, il riposo è garantito.
            
        segmenti_lavoro.sort(key=lambda x: x[0])
        
        # --- 2. Controllo dei gap interni alla settimana ---
        for i in range(len(segmenti_lavoro) - 1):
            fine_precedente = segmenti_lavoro[i][1]
            inizio_successivo = segmenti_lavoro[i+1][0]
            delta_ore = (inizio_successivo - fine_precedente).total_seconds() / 3600
            
            if delta_ore >= self.RIPOSO_SETTIMANALE_MIN:
                return True # Trovato un riposo valido all'interno della settimana.

        # --- 3. Se non ci sono gap interni, controlliamo i confini con le altre settimane ---
        
        # Controlla il confine INIZIALE (tra settimana precedente e corrente)
        anno, settimana = settimana_key
        primo_giorno_settimana = date.fromisocalendar(anno, settimana, 1)
        data_settimana_prec = primo_giorno_settimana - timedelta(days=1)
        settimana_key_prec = (data_settimana_prec.year, data_settimana_prec.isocalendar()[1])
        
        turni_prec = self.get_assegnazioni_dipendente(settimana_key_prec, id_dipendente)
        if not turni_prec:
            return True # Se la settimana prima non ha lavorato, ha avuto riposo.
        
        # Trova l'orario di fine dell'ultimo turno della settimana precedente, gestendo correttamente le notti.
        fine_ultimo_turno_prec = None
        for item in turni_prec:
            fascia_prec: FasciaOraria = item[0]
            if fascia_prec.tipo == TipoFascia.RIPOSO:
                continue
            orari = self.ORARIO_TURNI[fascia_prec.tipo.value]
            end_time_prec = datetime.combine(fascia_prec.data_turno, time(hour=orari[1]))
            if orari[1] < orari[0]: # Gestisce la notte
                end_time_prec += timedelta(days=1)
            
            if fine_ultimo_turno_prec is None or end_time_prec > fine_ultimo_turno_prec:
                fine_ultimo_turno_prec = end_time_prec

        # Se non c'è un ultimo turno (solo riposi) o se il gap è sufficiente
        if not fine_ultimo_turno_prec or (segmenti_lavoro[0][0] - fine_ultimo_turno_prec).total_seconds() / 3600 >= self.RIPOSO_SETTIMANALE_MIN:
            return True

        # Controlla il confine FINALE (tra settimana corrente e successiva)
        data_settimana_succ = primo_giorno_settimana + timedelta(days=7)
        settimana_key_succ = (data_settimana_succ.year, data_settimana_succ.isocalendar()[1])
        turni_succ = self.get_assegnazioni_dipendente(settimana_key_succ, id_dipendente)
        if not turni_succ:
            return True # Se la settimana dopo non lavora, inizierà un periodo di riposo.

        # Altrimenti, calcoliamo il gap tra la fine dell'ultimo turno corrente e l'inizio del primo successivo
        inizio_primo_turno_succ = None
        for item in turni_succ:
            fascia_succ: FasciaOraria = item[0]
            if fascia_succ.tipo == TipoFascia.RIPOSO:
                continue
            orari = self.ORARIO_TURNI[fascia_succ.tipo.value]
            start_time_succ = datetime.combine(fascia_succ.data_turno, time(hour=orari[0]))
            if inizio_primo_turno_succ is None or start_time_succ < inizio_primo_turno_succ:
                inizio_primo_turno_succ = start_time_succ
        
        fine_ultimo_turno_corrente = segmenti_lavoro[-1][1]
        if inizio_primo_turno_succ and (inizio_primo_turno_succ - fine_ultimo_turno_corrente).total_seconds() / 3600 >= self.RIPOSO_SETTIMANALE_MIN:
            return True

        # Se nessun controllo ha dato esito positivo, non c'è un riposo di 24h garantito.
        return False

    def _check_riposo_tra_turni(self, settimana_key: tuple[int, int], data_turno: date, tipo_fascia: TipoFascia, dipendente_obj: Dipendente, turno_breve: bool, piano: int, jolly: bool) -> bool:
        """
        Simula l'assegnazione e verifica che venga rispettato il vincolo delle 11 ore di riposo tra i turni,
        controllando anche i turni a cavallo con le settimane adiacenti.
        """
        # 1. Creiamo un'istanza TEMPORANEA di Turnazione
        turnazione_simulata = Turnazione()
        # Ottimizzazione: Copiamo la configurazione dall'istanza attuale
        turnazione_simulata.max_jolly_per_turno = self.max_jolly_per_turno
        turnazione_simulata.max_dipendenti_per_piano = self.max_dipendenti_per_piano
        turnazione_simulata.limiti_fascia = self.limiti_fascia.copy()
        
        # 2. Iniettiamo in questa istanza una COPIA della settimana corrente
        turnazione_simulata.turnazioneSettimanale[settimana_key] = deepcopy(self.turnazioneSettimanale.get(settimana_key, {}))
        
        # 3. Aggiungiamo la NUOVA assegnazione alla turnazione simulata
        fascia_simulata = turnazione_simulata.turnazioneSettimanale[settimana_key].get(data_turno, {}).get(tipo_fascia)
        if fascia_simulata:
            fascia_simulata.ripristina_assegnazione(AssegnazioneTurno(dipendente_obj, turnoBreve=turno_breve, piano=piano, jolly=jolly))
        
        # 4. Recuperiamo TUTTI i turni dalla simulazione per la settimana corrente
        assegnazioni_dip = turnazione_simulata.get_assegnazioni_dipendente(settimana_key, dipendente_obj.id_dipendente)
        lista_intervalli = []

        for item in assegnazioni_dip:
            fascia_obj: FasciaOraria = item[0]
            if fascia_obj.tipo == TipoFascia.RIPOSO:
                continue

            orari = self.ORARIO_TURNI[fascia_obj.tipo.value]
            start_h, end_h = orari[0], orari[1]
            dt_start = datetime.combine(fascia_obj.data_turno, time(hour=start_h))
            dt_end = datetime.combine(fascia_obj.data_turno, time(hour=end_h))
            if end_h < start_h:
                dt_end += timedelta(days=1)
            
            lista_intervalli.append((dt_start, dt_end, fascia_obj.tipo.value))

        # --- Aggiungiamo i turni di confine per un controllo completo ---
        anno, settimana = settimana_key
        primo_giorno_settimana = date.fromisocalendar(anno, settimana, 1)

        # A. Turno finale della settimana precedente
        data_settimana_prec = primo_giorno_settimana - timedelta(days=1)
        settimana_key_prec = (data_settimana_prec.year, data_settimana_prec.isocalendar()[1])
        turni_prec = self.get_assegnazioni_dipendente(settimana_key_prec, dipendente_obj.id_dipendente)
        if turni_prec:
            fine_ultimo_turno_prec = None
            ultimo_turno_prec_obj = None
            for item in turni_prec:
                fascia_prec: FasciaOraria = item[0]
                if fascia_prec.tipo == TipoFascia.RIPOSO: continue
                
                orari = self.ORARIO_TURNI[fascia_prec.tipo.value]
                end_time_prec = datetime.combine(fascia_prec.data_turno, time(hour=orari[1]))
                if orari[1] < orari[0]: end_time_prec += timedelta(days=1)
                
                if fine_ultimo_turno_prec is None or end_time_prec > fine_ultimo_turno_prec:
                    fine_ultimo_turno_prec = end_time_prec
                    start_time_prec = datetime.combine(fascia_prec.data_turno, time(hour=orari[0]))
                    ultimo_turno_prec_obj = (start_time_prec, end_time_prec, fascia_prec.tipo.value)

            if ultimo_turno_prec_obj:
                lista_intervalli.append(ultimo_turno_prec_obj)

        # B. Turno iniziale della settimana successiva
        data_settimana_succ = primo_giorno_settimana + timedelta(days=7)
        settimana_key_succ = (data_settimana_succ.year, data_settimana_succ.isocalendar()[1])
        turni_succ = self.get_assegnazioni_dipendente(settimana_key_succ, dipendente_obj.id_dipendente)
        if turni_succ:
            inizio_primo_turno_succ = None
            primo_turno_succ_obj = None
            for item in turni_succ:
                fascia_succ: FasciaOraria = item[0]
                if fascia_succ.tipo == TipoFascia.RIPOSO: continue

                orari = self.ORARIO_TURNI[fascia_succ.tipo.value]
                start_time_succ = datetime.combine(fascia_succ.data_turno, time(hour=orari[0]))

                if inizio_primo_turno_succ is None or start_time_succ < inizio_primo_turno_succ:
                    inizio_primo_turno_succ = start_time_succ
                    end_time_succ = datetime.combine(fascia_succ.data_turno, time(hour=orari[1]))
                    if orari[1] < orari[0]: end_time_succ += timedelta(days=1)
                    primo_turno_succ_obj = (start_time_succ, end_time_succ, fascia_succ.tipo.value)
            
            if primo_turno_succ_obj:
                lista_intervalli.append(primo_turno_succ_obj)

        # Ordiniamo i turni in base all'orario di inizio (ora include i confini)
        lista_intervalli.sort(key=lambda x: x[0])

        # 5. Controllo sequenziale delle 11 ore
        for i in range(len(lista_intervalli) - 1):
            turno_corrente = lista_intervalli[i]
            turno_successivo = lista_intervalli[i+1]

            # Calcoliamo la differenza tra Fine del Corrente e Inizio del Successivo
            delta = turno_successivo[0] - turno_corrente[1]

            if delta < timedelta(hours=self.PAUSA_TRA_TURNI):
                raise ValueError(f"Violazione riposo min {self.PAUSA_TRA_TURNI}h: Tra {turno_corrente[2]} e {turno_successivo[2]} passano solo {delta}.")

        return True

    def get_candidati_disponibili(self, sistema_dipendenti: SistemaDipendenti, data_turno: date, tipo_fascia: TipoFascia) -> List[Dipendente]:
        """
        Restituisce una lista di dipendenti che POSSONO lavorare in questo specifico turno
        rispettando TUTTI i vincoli (Assenze, Riposo 11h, Riposo 24h, Max Ore).
        """
        candidati = []
        anno, settimana, _ = data_turno.isocalendar()
        settimana_key = (anno, settimana)
        
        tutti_dipendenti = sistema_dipendenti.get_lista_dipendenti()
        
        for dip in tutti_dipendenti:
            # 1. Filtro base: Deve essere ASSUNTO
            if dip.stato.value != "ASSUNTO":
                continue
                
            # 2. Filtro Assenze (Ferie/Malattia)
            if sistema_dipendenti.verifica_assenza(dip.id_dipendente, data_turno):
                continue
                
            assegnazioni_sett = self.get_assegnazioni_dipendente(settimana_key, dip.id_dipendente)
            
            # Filtro: Se ha già un'assegnazione oggi (compreso RIPOSO automatico)
            if any(f.data_turno == data_turno for f, ass in assegnazioni_sett):
                continue
                
            # Filtro: Massimo 1 NOTTE per settimana
            if tipo_fascia == TipoFascia.NOTTE:
                if any(f.tipo == TipoFascia.NOTTE for f, ass in assegnazioni_sett):
                    continue
                
            # 3. Filtro Max Ore Settimanali (Simuliamo inserimento standard, no turno breve per ora)
            # Nota: check_max_ore restituisce [True/False, CausaNuovoTurno]. Ci interessa se passa.
            esito_ore, _ = self._check_max_ore_settimanali(dip.id_dipendente, settimana_key, tipo_fascia, turno_breve=False)
            if not esito_ore:
                continue
                
            # 4. Filtro Riposo 11 ore
            try:
                self._check_riposo_tra_turni(settimana_key, data_turno, tipo_fascia, dip, turno_breve=False, piano=0, jolly=False)
            except ValueError:
                continue # Viola le 11 ore
                
            # 5. Filtro Riposo Settimanale (Warning -> Lo trattiamo come bloccante per l'auto-generazione per essere sicuri)
            if not self._check_riposo_settimanale(settimana_key, dip.id_dipendente, data_turno, tipo_fascia, turno_breve=False):
                # Bloccante per la generazione automatica per garantire il rispetto del vincolo
                continue

            candidati.append(dip)
            
        return candidati

    def assegna_turno(self, sistema_dipendenti: SistemaDipendenti, id_dipendente: int, data_turno: date, tipo_fascia: TipoFascia, piano: int = 0, jolly: bool = False, turno_breve: bool = False) -> bool:
        """Cerca la fascia specifica e aggiunge l'assegnazione (che salva su DB)."""
        anno, settimana, _ = data_turno.isocalendar()
        settimana_key = (anno, settimana)
        
        fascia = self.turnazioneSettimanale.get(settimana_key, {}).get(data_turno, {}).get(tipo_fascia)
        
        if not fascia:
            raise ValueError("La fascia oraria specificata non esiste in giornata.")

        dipendente_obj = sistema_dipendenti.get_dipendente(id_dipendente)
        if dipendente_obj is None:
            raise ValueError("Dipendente non trovato a sistema.")

        # Early return per i turni di RIPOSO per evitare check inutili
        if tipo_fascia == TipoFascia.RIPOSO:
            esito = fascia.add_assegnazione(AssegnazioneTurno(dipendente_obj, turnoBreve=False, piano=None, jolly=False))
            return esito
            
        # Controlli Configurazione Limiti Operatori
        if jolly:
            jolly_count = sum(1 for a in fascia.assegnazioni if getattr(a, 'jolly', False))
            if jolly_count >= self.max_jolly_per_turno:
                raise ValueError(f"Limite massimo di {self.max_jolly_per_turno} Jolly raggiunto per questo turno.")

        if piano is not None:
            piano_count = sum(1 for a in fascia.assegnazioni if getattr(a, 'piano', None) == piano)
            if piano_count >= self.max_dipendenti_per_piano:
                raise ValueError(f"Limite di {self.max_dipendenti_per_piano} dipendenti per il piano {piano} raggiunto.")

        # Controllo vincolo ore massime settimanali
        esito_ore, causa_nuovo = self._check_max_ore_settimanali(id_dipendente, settimana_key, tipo_fascia, turno_breve)
        if not esito_ore:
            if causa_nuovo:
                print("Inserendo il nuovo turno si eccedono le ore settimanali consentite. La rimanente parte verrà considerata come straordinari o finirà in banca ore.")
            else:
                print("Attenzione: Il dipendente ha già superato il monte ore settimanale. Questo turno sarà interamente straordinario.")

        # Verifica vincolo 11 ore di riposo
        self._check_riposo_tra_turni(settimana_key, data_turno, tipo_fascia, dipendente_obj, turno_breve, piano, jolly)
        
        # Verifica vincolo 24 ore riposo settimanale (Warning)
        if not self._check_riposo_settimanale(settimana_key, id_dipendente, data_turno, tipo_fascia, turno_breve):
            print(f"ATTENZIONE: Con questo inserimento, {dipendente_obj.nome} potrebbe non avere 24h consecutive di riposo in questa settimana!")

        # Verifica media 48h/4 mesi (Warning Legale)
        self._check_media_ore_4_mesi(id_dipendente, data_turno, f"{dipendente_obj.nome} {dipendente_obj.cognome}")
            # Non blocchiamo (raise Error) perché magari il riposo è a cavallo della settimana, ma stampiamo warning.

        # Se tutti i controlli passano, procediamo con l'assegnazione reale
        # L'assegnazione chiama database che se bloccata (es per Trigger Assenze) restituirà False
        esito = fascia.add_assegnazione(AssegnazioneTurno(dipendente_obj, turnoBreve=turno_breve, piano=piano, jolly=jolly))
        if not esito:
            raise ValueError("Assegnazione bloccata dal database. Il dipendente potrebbe essere in Ferie/Malattia in questa data.")

        # AUTOMATISMO: Se è un turno di NOTTE, assegna automaticamente 2 giorni di RIPOSO (smontante e riposo)
        if esito and tipo_fascia == TipoFascia.NOTTE:
            data_domani = data_turno + timedelta(days=1)
            data_dopodomani = data_turno + timedelta(days=2)
            
            for giorno_riposo in [data_domani, data_dopodomani]:
                anno_r, sett_r, _ = giorno_riposo.isocalendar()
                
                # Inizializza la settimana se non esiste o è incompleta
                settimana_dict = self.turnazioneSettimanale.get((anno_r, sett_r), {})
                if len(settimana_dict) < 7:
                    self.inizializza_settimana(anno_r, sett_r)
                    
                if self.add_turno(giorno_riposo, TipoFascia.RIPOSO, StatoFascia.CREATO):
                    desc_riposo = "smontante" if giorno_riposo == data_domani else "riposo"
                    print(f"Assegnazione automatica turno RIPOSO ({desc_riposo}) per {dipendente_obj.nome} {dipendente_obj.cognome} il {giorno_riposo}")
                    self.assegna_turno(sistema_dipendenti, id_dipendente, giorno_riposo, TipoFascia.RIPOSO, piano=None)

        return esito

    def rimuovi_assegnazione(self, id_dipendente: int, data_turno: date, tipo_fascia: TipoFascia) -> bool:
        anno, settimana, _ = data_turno.isocalendar()
        settimana_key = (anno, settimana)
        
        fascia = self.turnazioneSettimanale.get(settimana_key, {}).get(data_turno, {}).get(tipo_fascia)
        
        if not fascia:
            print("Fascia oraria non trovata.")
            return False
            
        if fascia.stato == StatoFascia.APPROVATA:
            print("Impossibile rimuovere assegnazione: La settimana è APPROVATA. Esegui prima 'Riapri Settimana'.")
            return False

        return fascia.remove_assegnazione(id_dipendente)

    def svuota_settimana(self, anno: int, settimana: int) -> bool:
        """
        Rimuove tutte le assegnazioni della settimana specificata,
        riportando i turni allo stato 'GENERATA' e svuotando la memoria.
        """
        settimana_key = (anno, settimana)
        settimana_dict = self.turnazioneSettimanale.get(settimana_key, {})
        
        if not settimana_dict:
            print("Nessun turno trovato per questa settimana.")
            return False

        # Verifica blocco approvazione: se approvata, non si tocca.
        for fasce in settimana_dict.values():
            for fascia in fasce.values():
                if fascia.stato == StatoFascia.APPROVATA:
                    print("Impossibile svuotare: La settimana è APPROVATA. Esegui 'Riapri Settimana' prima.")
                    return False
        
        primo_giorno = date.fromisocalendar(anno, settimana, 1)
        ultimo_giorno = primo_giorno + timedelta(days=6)
        
        if sistemaSalvataggio.reset_settimana(primo_giorno.strftime("%Y-%m-%d"), ultimo_giorno.strftime("%Y-%m-%d")):
            print(f"Settimana {settimana_key} svuotata con successo.")
            
            # Aggiornamento Memoria: Logica di pulizia profonda
            for giorno_dict in settimana_dict.values():
                # Rimuovi completamente le fasce RIPOSO dalla memoria (verranno ricreate se necessario)
                fasce_da_rimuovere = [tf for tf, f in giorno_dict.items() if f.tipo == TipoFascia.RIPOSO]
                for tf in fasce_da_rimuovere:
                    del giorno_dict[tf]
                
                # Per le altre fasce (MATTINA, POMERIGGIO, NOTTE), svuota solo le assegnazioni e resetta lo stato
                for fascia in giorno_dict.values():
                    fascia.assegnazioni.clear()
                    fascia.stato = StatoFascia.GENERATA
            return True
        else:
            print("Errore durante lo svuotamento della settimana.")
            return False

    def approva_settimana(self, sistema_dipendenti: SistemaDipendenti, settimana_key: tuple[int, int]) -> bool:
        """
        1. Verifica che la settimana non sia già approvata.
        2. Calcola il saldo ore per ogni dipendente coinvolto nella settimana.
        3. Aggiorna la banca ore dei dipendenti (aggiungendo il saldo).
        4. Imposta lo stato di tutti i turni della settimana su APPROVATA.
        """
        settimana_dict = self.turnazioneSettimanale.get(settimana_key, {})
        if not settimana_dict:
            print("Nessun turno trovato per questa settimana.")
            return False

        # Verifica preliminare: se trovo anche solo un turno già APPROVATO, blocco per sicurezza
        for fasce in settimana_dict.values():
            for fascia in fasce.values():
                if fascia.stato == StatoFascia.APPROVATA:
                    print("Errore: Questa settimana risulta già parzialmente o totalmente approvata. Esegui il 'Riapri Settimana' se vuoi ricalcolarla.")
                    return False

        # Identifichiamo tutti i dipendenti che hanno lavorato questa settimana
        dipendenti_coinvolti = set()
        for fasce in settimana_dict.values():
            for fascia in fasce.values():
                for assegnazione in fascia.assegnazioni:
                    dipendenti_coinvolti.add(assegnazione.dipendente.id_dipendente)

        print(f"Approvazione settimana {settimana_key}... Aggiornamento banca ore per {len(dipendenti_coinvolti)} dipendenti.")

        # 1. Aggiornamento Banca Ore
        for id_dip in dipendenti_coinvolti:
            saldo = self.calcola_saldo_ore_settimanale(id_dip, settimana_key)
            sistema_dipendenti.aggiorna_banca_ore(id_dip, saldo)
            print(f"  -> Dipendente {id_dip}: Saldo {saldo:+.2f} ore applicato.")

        # 2. Aggiornamento Stato Turni (Lock)
        for fasce in settimana_dict.values():
            for fascia in fasce.values():
                fascia.stato = StatoFascia.APPROVATA
                sistemaSalvataggio.update_stato_turno(fascia.id_turno, StatoFascia.APPROVATA.value)
        
        return True

    def riapri_settimana(self, sistema_dipendenti: SistemaDipendenti, settimana_key: tuple[int, int]) -> bool:
        """
        ROLLBACK:
        1. Verifica che la settimana sia effettivamente APPROVATA.
        2. Calcola il saldo ore (basato sui turni attuali) e lo SOTTRAE alla banca ore (annullando l'effetto dell'approvazione).
        3. Riporta lo stato dei turni su MODIFICATA.
        """
        settimana_dict = self.turnazioneSettimanale.get(settimana_key, {})
        
        # Identifichiamo i dipendenti
        dipendenti_coinvolti = set()
        almeno_uno_approvato = False
        
        for fasce in settimana_dict.values():
            for fascia in fasce.values():
                if fascia.stato == StatoFascia.APPROVATA:
                    almeno_uno_approvato = True
                for assegnazione in fascia.assegnazioni:
                    dipendenti_coinvolti.add(assegnazione.dipendente.id_dipendente)
        
        if not almeno_uno_approvato:
            print("Questa settimana non è approvata, non c'è nulla da riaprire.")
            return False

        print(f"ROLLBACK Settimana {settimana_key}... Storno banca ore per {len(dipendenti_coinvolti)} dipendenti.")

        # 1. Storno Banca Ore (Sottraiamo il saldo)
        for id_dip in dipendenti_coinvolti:
            saldo = self.calcola_saldo_ore_settimanale(id_dip, settimana_key)
            # NOTA: Passiamo -saldo per annullare l'operazione precedente
            sistema_dipendenti.aggiorna_banca_ore(id_dip, -saldo) 
            print(f"  -> Dipendente {id_dip}: Storno di {-saldo:+.2f} ore applicato.")

        # 2. Sblocco Turni
        for fasce in settimana_dict.values():
            for fascia in fasce.values():
                fascia.stato = StatoFascia.MODIFICATA
                sistemaSalvataggio.update_stato_turno(fascia.id_turno, StatoFascia.MODIFICATA.value)

        return True

    def get_assegnazioni_dipendente(self, info_settimana: tuple[int, int] | dict, id_dipendente: int) -> List[list]:
        assegnazioni = []

        if isinstance(info_settimana, dict):
            settimana_dict = info_settimana
        else:
            settimana_dict = self.turnazioneSettimanale.get(info_settimana, {})

        for giorno_dict in settimana_dict.values():
            for fascia in giorno_dict.values():
                for assegnazione in fascia.assegnazioni:
                    if assegnazione.dipendente.id_dipendente == id_dipendente:
                        assegnazioni.append([fascia, assegnazione])
        return assegnazioni

    # Metodi di Configurazione
    def set_config_max_jolly(self, valore: int):
        self.max_jolly_per_turno = valore
        sistemaSalvataggio.save_config('max_jolly', str(valore))

    def set_config_max_piano(self, valore: int):
        self.max_dipendenti_per_piano = valore
        sistemaSalvataggio.save_config('max_piano', str(valore))

    def set_config_limite_fascia(self, tipo_fascia: TipoFascia, valore: int):
        self.limiti_fascia[tipo_fascia] = valore
        sistemaSalvataggio.save_config(f'limit_{tipo_fascia.value}', str(valore))
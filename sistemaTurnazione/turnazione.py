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
    
    # Costanti Vincoli Assegnazione
    MAX_JOLLY_PER_TURNO: int = 1
    MAX_DIPENDENTI_PER_PIANO: int = 3


    def __init__(self, turnazioneSettimanale: dict[tuple[int, int], dict[date, dict[TipoFascia, FasciaOraria]]] | None = None):
        if turnazioneSettimanale is not None:
            self.turnazioneSettimanale = turnazioneSettimanale
        else:
            self.turnazioneSettimanale = {}
    
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


    def add_turno(self, data_turno: date, tipo_fascia: TipoFascia, stato: StatoFascia = StatoFascia.VUOTA) :
        """
        Aggiunge una nuova fascia oraria alla turnazione, salvandola prima nel database.
        """
        # 1. Salva il turno nel database e ottieni l'ID
        id_turno_db = sistemaSalvataggio.save_turno(data_turno, tipo_fascia.value, stato.value)

        if id_turno_db is None:
            print(f"Errore: Impossibile salvare il turno per {data_turno} {tipo_fascia.value} nel database.")
            return False

        anno, settimana_iso, _ = data_turno.isocalendar()
        settimana_key = (anno, settimana_iso)

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

    def _check_max_mena_ore_settimanali(self):
        pass

    def _check_riposo_tra_turni(self, settimana_key: tuple[int, int], data_turno: date, tipo_fascia: TipoFascia, dipendente_obj: Dipendente, turno_breve: bool, piano: int, jolly: bool) -> bool:
        """
        Simula l'assegnazione e verifica che venga rispettato il vincolo delle 11 ore di riposo tra i turni.
        Restituisce True se il vincolo è rispettato, False altrimenti.
        """
        # 1. Creiamo un'istanza TEMPORANEA di Turnazione
        turnazione_simulata = Turnazione()
        
        # 2. Iniettiamo in questa istanza una COPIA della settimana corrente
        turnazione_simulata.turnazioneSettimanale[settimana_key] = deepcopy(self.turnazioneSettimanale.get(settimana_key, {}))
        
        # 3. Aggiungiamo la NUOVA assegnazione alla turnazione simulata
        #    Recuperiamo la fascia dalla simulazione
        fascia_simulata = turnazione_simulata.turnazioneSettimanale[settimana_key].get(data_turno, {}).get(tipo_fascia)
        
        if fascia_simulata:
            # Aggiungiamo l'assegnazione usando l'oggetto dipendente reale (ma nella struttura copiata)
            fascia_simulata.ripristina_assegnazione(AssegnazioneTurno(dipendente_obj, turnoBreve=turno_breve, piano=piano, jolly=jolly))
        
        # 4. Recuperiamo TUTTI i turni dalla simulazione
        assegnazioni_dip = turnazione_simulata.get_assegnazioni_dipendente(settimana_key, dipendente_obj.id_dipendente)
        lista_intervalli = []

        for item in assegnazioni_dip:
            fascia_obj: FasciaOraria = item[0]
            # Ignoriamo i turni di RIPOSO per il calcolo delle ore di stacco lavorativo
            if fascia_obj.tipo == TipoFascia.RIPOSO:
                continue

            orari = self.ORARIO_TURNI[fascia_obj.tipo.value] # es. [7, 14]
            start_h, end_h = orari[0], orari[1]

            # Creiamo i datetime completi
            dt_start = datetime.combine(fascia_obj.data_turno, time(hour=start_h))
            dt_end = datetime.combine(fascia_obj.data_turno, time(hour=end_h))

            # Se l'ora di fine è minore dell'inizio (es. NOTTE 21-07), aggiungiamo un giorno alla fine
            if end_h < start_h:
                dt_end += timedelta(days=1)
            
            lista_intervalli.append((dt_start, dt_end, fascia_obj.tipo.value))

        # Ordiniamo i turni in base all'orario di inizio
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
            
        # Controlli Configurazione Limiti Operatori
        if jolly:
            jolly_count = sum(1 for a in fascia.assegnazioni if getattr(a, 'jolly', False))
            if jolly_count >= self.MAX_JOLLY_PER_TURNO:
                raise ValueError(f"Limite massimo di {self.MAX_JOLLY_PER_TURNO} Jolly raggiunto per questo turno.")

        if piano is not None:
            piano_count = sum(1 for a in fascia.assegnazioni if getattr(a, 'piano', None) == piano)
            if piano_count >= self.MAX_DIPENDENTI_PER_PIANO:
                raise ValueError(f"Limite di {self.MAX_DIPENDENTI_PER_PIANO} dipendenti per il piano {piano} raggiunto.")

        # Controllo vincolo ore massime settimanali
        esito_ore, causa_nuovo = self._check_max_ore_settimanali(id_dipendente, settimana_key, tipo_fascia, turno_breve)
        if not esito_ore:
            if causa_nuovo:
                print("Inserendo il nuovo turno si eccedono le ore settimanali consentite. La rimanente parte verrà considerata come straordinari o finirà in banca ore.")
            else:
                print("Attenzione: Il dipendente ha già superato il monte ore settimanale. Questo turno sarà interamente straordinario.")

        # Verifica vincolo 11 ore di riposo
        self._check_riposo_tra_turni(settimana_key, data_turno, tipo_fascia, dipendente_obj, turno_breve, piano, jolly)

        # Se tutti i controlli passano, procediamo con l'assegnazione reale
        # L'assegnazione chiama database che se bloccata (es per Trigger Assenze) restituirà False
        esito = fascia.add_assegnazione(AssegnazioneTurno(dipendente_obj, turnoBreve=turno_breve, piano=piano, jolly=jolly))
        if not esito:
            raise ValueError("Assegnazione bloccata dal database. Il dipendente potrebbe essere in Ferie/Malattia in questa data.")

        # AUTOMATISMO: Se è un turno di NOTTE, assegna automaticamente RIPOSO il giorno dopo
        if esito and tipo_fascia == TipoFascia.NOTTE:
            data_domani = data_turno + timedelta(days=1)
            self.add_turno(data_domani, TipoFascia.RIPOSO, StatoFascia.CREATO)
            print(f"Assegnazione automatica RIPOSO per {dipendente_obj.nome} {dipendente_obj.cognome} il {data_domani}")
            self.assegna_turno(sistema_dipendenti, id_dipendente, data_domani, TipoFascia.RIPOSO, piano=None)

        return esito


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
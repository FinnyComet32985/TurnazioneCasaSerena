from datetime import date, datetime
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

    def assegna_turno(self, sistema_dipendenti: SistemaDipendenti, id_dipendente: int, data_turno: date, tipo_fascia: TipoFascia, piano: int = 0, jolly: bool = False, turno_breve: bool = False) -> bool:
        """Cerca la fascia specifica e aggiunge l'assegnazione (che salva su DB)."""
        anno, settimana, _ = data_turno.isocalendar()
        settimana_key = (anno, settimana)

        try:
            fascia = self.turnazioneSettimanale[settimana_key][data_turno][tipo_fascia]
            
            # Usiamo l'istanza di sistema_dipendenti che ci hai passato per ottenere l'oggetto
            dipendente_obj = sistema_dipendenti.get_dipendente(id_dipendente)
            if dipendente_obj is None:
                print("Dipendente non trovato")
                return False
                
            return fascia.add_assegnazione(AssegnazioneTurno(dipendente_obj, turnoBreve=turno_breve, piano=piano, jolly=jolly))
        except KeyError:
            print("Errore: La fascia oraria specificata non esiste.")
            return False
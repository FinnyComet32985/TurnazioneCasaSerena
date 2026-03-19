from datetime import date
from fasciaOraria import FasciaOraria, TipoFascia, StatoFascia
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
    
    def add_turno(self, anno: int, settimana_iso: int, data_turno: date, tipo_fascia: TipoFascia, stato: StatoFascia = StatoFascia.GENERATA) -> bool:
        """
        Aggiunge una nuova fascia oraria alla turnazione, salvandola prima nel database.
        """
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
        settimana_key = (anno, settimana_iso)
        self.turnazioneSettimanale.setdefault(settimana_key, {}).setdefault(data_turno, {})[tipo_fascia] = fascia_oraria
        
        return True

    def assegna_turno(self, assegnazione_att):
        pass
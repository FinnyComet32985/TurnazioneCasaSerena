import datetime
from enum import Enum
from sqlite3 import Date
import sistemaSalvataggio

from sistemaTurnazione.assegnazioneTurno import AssegnazioneTurno


class TipoFascia(Enum):
    MATTINA = "MATTINA"
    POMERIGGIO = "POMERIGGIO"
    NOTTE = "NOTTE"
    RIPOSO = "RIPOSO"

class StatoFascia(Enum):
    GENERATA = "GENERATA"
    MODIFICATA = "MODIFICATA"
    APPROVATA = "APPROVATA"
    VUOTA = "VUOTA"
    CREATO = "CREATO"

class FasciaOraria:
    id_turno: int
    data_turno: Date
    tipo: TipoFascia
    assegnazioni: list[AssegnazioneTurno]
    stato: StatoFascia

    def __init__(self, data_turno: Date, tipo: TipoFascia, assegnazioni: list[AssegnazioneTurno] | None = None, stato: StatoFascia | None = None, id_turno: int = None):
        self.data_turno = data_turno
        self.tipo = tipo
        if id_turno is not None:
            self.id_turno = id_turno

        if assegnazioni is not None:
            self.assegnazioni = assegnazioni
        else:
            self.assegnazioni = []
        if stato is not None:
            self.stato = stato
    
    def add_assegnazione(self, assegnazione: AssegnazioneTurno):
        # VINCOLO: Il turno breve è applicabile solo alla fascia MATTINA
        if assegnazione.turnoBreve and self.tipo != TipoFascia.MATTINA:
            print(f"Errore: Il turno breve non può essere assegnato alla fascia {self.tipo.value}. È valido solo per MATTINA.")
            return False

        # Verifichiamo che la fascia oraria abbia un ID (sia salvata su DB) prima di salvare l'assegnazione
        if getattr(self, 'id_turno', None) is None:
            return False
            
        result = sistemaSalvataggio.save_assegnazione(self.id_turno, assegnazione)
        if result:
            self.assegnazioni.append(assegnazione)
            return True
        return False

    def ripristina_assegnazione(self, assegnazione: AssegnazioneTurno):
        """Aggiunge un'assegnazione alla lista in memoria senza salvare su DB."""
        self.assegnazioni.append(assegnazione)

    def modify(self):
        pass

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
        # VINCOLO: massimo numero oss per turno
        if self.tipo == TipoFascia.MATTINA and len(self.assegnazioni) >=7:
            print("Errore: nel turno sono già presenti 7 oss")
            return False
        elif self.tipo == TipoFascia.POMERIGGIO and len(self.assegnazioni) >= 6:
            print("Errore: nel turno sono già presenti 6 oss")
            return False
        elif self.tipo == TipoFascia.NOTTE and len(self.assegnazioni) >= 2:
            print("Errore: nel turno sono già presenti 2 oss")
            return False

        # VINCOLO: Il turno breve è applicabile solo alla fascia MATTINA
        if assegnazione.turnoBreve and self.tipo != TipoFascia.MATTINA:
            print(f"Errore: Il turno breve non può essere assegnato alla fascia {self.tipo.value}. È valido solo per MATTINA.")
            return False

        # VINCOLO: È consentito al massimo un turno breve per fascia (già limitato a MATTINA dal check sopra)
        if assegnazione.turnoBreve:
            for a in self.assegnazioni:
                if a.turnoBreve:
                    print(f"Errore: Limite raggiunto. È già presente un turno breve assegnato a {a.dipendente.nome} {a.dipendente.cognome}.")
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

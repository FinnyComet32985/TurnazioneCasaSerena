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
    GENERATA = "GENERATO"
    MODIFICATA = "MODIFICATO"
    APPROVATA = "APPROVATO"
    VUOTA = "VUOTA"
    CREATO = "CREATO"

class FasciaOraria:
    id_turno: int
    data_turno: Date
    tipo: TipoFascia
    assegnazioni: list[AssegnazioneTurno]
    stato: StatoFascia

    def __init__(self, data_turno: Date, tipo: TipoFascia, assegnazioni: list[AssegnazioneTurno] | None = None, stato: StatoFascia | None = None, id_turno: int | None = None):
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
    
    def add_assegnazione(self, assegnazione: AssegnazioneTurno, limiti_fascia: dict | None = None):
        # VINCOLO: massimo numero oss per turno (usare limiti configurati o hardcoded)
        if limiti_fascia is None:
            limiti_fascia = {TipoFascia.MATTINA: 7, TipoFascia.POMERIGGIO: 6, TipoFascia.NOTTE: 5}
        
        max_oss = limiti_fascia.get(self.tipo)
        if max_oss is not None and len(self.assegnazioni) >= max_oss:
            print(f"Errore: nel turno sono già presenti {max_oss} oss")
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
    
    def remove_assegnazione(self, id_dipendente: int) -> bool:
        # Verifica se l'assegnazione esiste
        for i, ass in enumerate(self.assegnazioni):
            if ass.dipendente.id_dipendente == id_dipendente:
                if sistemaSalvataggio.remove_assegnazione_turno(self.id_turno, id_dipendente):
                    self.assegnazioni.pop(i)
                    return True
        return False

    def ripristina_assegnazione(self, assegnazione: AssegnazioneTurno):
        """Aggiunge un'assegnazione alla lista in memoria senza salvare su DB."""
        self.assegnazioni.append(assegnazione)

    def modify(self):
        pass

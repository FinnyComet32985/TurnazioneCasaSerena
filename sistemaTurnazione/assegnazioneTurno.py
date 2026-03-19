
from sistemaDipendenti import sistemaDipendenti
from sistemaDipendenti.dipendente import Dipendente


class AssegnazioneTurno:
    dipendente: Dipendente
    turnoBreve: bool
    piano: int
    jolly: bool

    def __init__(self, dipendente: Dipendente | int, turnoBreve: bool = False, piano: int = None, jolly: bool = False):
        if isinstance(dipendente, Dipendente):
            self.dipendente = dipendente
        elif isinstance(dipendente, int):
            temp = sistemaDipendenti.get_dipendente(dipendente)
            if temp is not None:
                self.dipendente = temp
            else:
                return False
        
        self.turnoBreve = turnoBreve
        self.piano = piano
        self.jolly = jolly
    
    def modify(self):
        pass
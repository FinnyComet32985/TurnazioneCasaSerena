from sistemaDipendenti.dipendente import Dipendente


class AssegnazioneTurno:
    dipendente: Dipendente
    turnoBreve: bool
    piano: int
    jolly: bool

    def __init__(self, dipendente: Dipendente, turnoBreve: bool = False, piano: int = None, jolly: bool = False):
        self.dipendente = dipendente
        
        self.turnoBreve = turnoBreve
        self.piano = piano
        self.jolly = jolly
    
    def modify(self):
        pass
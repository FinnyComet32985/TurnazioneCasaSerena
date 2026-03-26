from enum import Enum
from sistemaDipendenti.assenzaProgrammata import AssenzaProgrammata
from sistemaDipendenti.variazioneBancaOre import VariazioneBancaOre



class StatoDipendente(Enum):
    ASSUNTO = "ASSUNTO"
    LICENZIATO = "LICENZIATO"


class Dipendente:
    id_dipendente: int
    nome: str
    cognome: str
    stato: StatoDipendente
    ferie_rimanenti: float
    rol_rimanenti: float
    variazioni_banca_ore: list[VariazioneBancaOre]
    assenze_programmate: list[AssenzaProgrammata]

    def __init__(self, nome: str, cognome: str, stato: StatoDipendente = None, ferie_rimanenti: float = None, rol_rimanenti: float = None, banca_ore: float = None, assenze_programmate: list[AssenzaProgrammata] = None, id_dipendente: int = None):
        self.nome = nome
        self.cognome = cognome

        if stato is not None:
            self.stato = stato
        else:
            self.stato = StatoDipendente.ASSUNTO
        if ferie_rimanenti is not None:
            self.ferie_rimanenti = ferie_rimanenti
        else:
            self.ferie_rimanenti = 0
        if rol_rimanenti is not None:
            self.rol_rimanenti = rol_rimanenti
        else:
            self.rol_rimanenti = 0
        self.banca_ore = banca_ore if banca_ore is not None else 0
        self.variazioni_banca_ore = []
        if assenze_programmate is not None:
            self.assenze_programmate = assenze_programmate
        else:
            self.assenze_programmate = []
        if id_dipendente is not None:
            self.id_dipendente = id_dipendente

    def get_assenze_programmate(self):
        return self.assenze_programmate
    

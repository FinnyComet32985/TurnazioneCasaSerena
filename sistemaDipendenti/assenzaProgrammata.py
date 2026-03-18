from enum import Enum



class TipoAssenza(Enum):
        FERIE = "FERIE"
        ROL = "ROL"
        CERTIFICATO = "CERTIFICATO"

class AssenzaProgrammata:
    data_inizio: str
    data_fine: str
    tipo: str

    def __init__(self, data_inizio: str, data_fine: str, tipo: str):
        self.data_inizio = data_inizio
        self.data_fine = data_fine
        self.tipo = tipo

    def get_tipo(self):
        return self.tipo
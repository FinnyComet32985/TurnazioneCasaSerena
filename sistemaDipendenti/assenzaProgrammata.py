from enum import Enum



class TipoAssenza(Enum):
        FERIE = "FERIE"
        ROL = "ROL"
        CERTIFICATO = "CERTIFICATO"

class AssenzaProgrammata:
    id_assenza: int
    data_inizio: str
    data_fine: str
    tipo: str

    def __init__(self, data_inizio: str, data_fine: str, tipo: str, id_assenza: int = None):
        self.data_inizio = data_inizio
        self.data_fine = data_fine
        self.tipo = tipo

        if id_assenza is not None:
            self.id_assenza = id_assenza

    def get_tipo(self):
        return self.tipo
class VariazioneBancaOre:
    key: str
    valore: float
    descrizione: str

    def __init__(self, key: str, valore: float, descrizione: str = ""):
        self.key = key
        self.valore = valore
        self.descrizione = descrizione
        

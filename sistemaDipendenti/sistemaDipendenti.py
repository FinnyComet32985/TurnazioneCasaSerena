

from sistemaDipendenti.assenzaProgrammata import AssenzaProgrammata
from sistemaDipendenti.dipendente import Dipendente, StatoDipendente
from sistemaSalvataggio import salva_dipendente
import sistemaSalvataggio

class SistemaDipendenti:
    dipendenti : list[Dipendente]

    def __init__(self, lista_dipendenti: list[Dipendente] | None = None):
        if lista_dipendenti is not None:
            self.dipendenti = lista_dipendenti
        else:
            self.dipendenti = []


    def aggiungi_dipendente(self, nome: str, cognome: str, stato: StatoDipendente | None = None, ferie_rimanenti: float | None = None, rol_rimanenti : float | None = None, assenze_programmate: list[AssenzaProgrammata] | None = None):
        dipendente = Dipendente(nome, cognome, stato, ferie_rimanenti, rol_rimanenti, assenze_programmate)
        
        # Salva nel DB e ottieni l'ID generato
        id_db = salva_dipendente(dipendente)
        dipendente.id_dipendente = id_db

        self.dipendenti.append(dipendente)

    def rimuovi_dipendente(self, id_dipendente: int):
        result = sistemaSalvataggio.rimuovi_dipendente(id_dipendente)
        if result is True:
            # Cerchiamo l'oggetto dipendente nella lista controllando l'attributo id_dipendente
            for dipendente in self.dipendenti:
                if dipendente.id_dipendente == id_dipendente:
                    dipendente.stato = StatoDipendente.LICENZIATO
                    break
            return True
        else:
            return False
            
        

    def get_lista_dipendenti(self):
        return self.dipendenti



    def aggiungi_assenza(self, id_dipendente:int, tipo_assenza: AssenzaProgrammata, data_inizio: str, data_fine: str):

        eseguito = False

        # Cerchiamo l'oggetto dipendente nella lista
        for dipendente in self.dipendenti:
            if dipendente.id_dipendente == id_dipendente:
                # Salviamo nel DB
                id_db = sistemaSalvataggio.save_assenza(id_dipendente, tipo_assenza, data_inizio, data_fine)
                
                # Creiamo l'oggetto in memoria (passando il valore stringa dell'Enum)
                nuova_assenza = AssenzaProgrammata(data_inizio, data_fine, tipo_assenza.value, id_assenza=id_db)
                dipendente.assenze_programmate.append(nuova_assenza)
                eseguito = True
                break
        
        return eseguito
        
    def get_assenze_dipendente(self, id_dipendente: int):
        for dipendente in self.dipendenti:
            if dipendente.id_dipendente == id_dipendente:
                return dipendente.get_assenze_programmate()
        return []
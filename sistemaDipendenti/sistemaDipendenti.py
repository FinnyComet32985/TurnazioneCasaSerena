

from sistemaDipendenti.dipendente import Dipendente, StatoDipendente
from sistemaSalvataggio import salva_dipendente
import sistemaSalvataggio

class SistemaDipendenti:
    dipendenti : list[Dipendente]

    def __init__(self, lista_dipendenti = None):
        if lista_dipendenti is not None:
            self.dipendenti = lista_dipendenti
        else:
            self.dipendenti = []


    def aggiungi_dipendente(self, nome, cognome, stato = None, ferie_rimanenti = None, rol_rimanenti = None, assenze_programmate = None):
        dipendente = Dipendente(nome, cognome, stato, ferie_rimanenti, rol_rimanenti, assenze_programmate)
        
        # Salva nel DB e ottieni l'ID generato
        id_db = salva_dipendente(dipendente)
        dipendente.id_dipendente = id_db

        self.dipendenti.append(dipendente)

    def rimuovi_dipendente(self, id_dipendente):
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

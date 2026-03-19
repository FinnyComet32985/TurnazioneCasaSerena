

from sistemaDipendenti.assenzaProgrammata import AssenzaProgrammata
from sistemaDipendenti.dipendente import Dipendente, StatoDipendente
from sistemaSalvataggio import save_dipendente
import sistemaSalvataggio

class SistemaDipendenti:
    dipendenti : list[Dipendente]

    def __init__(self, lista_dipendenti: list[Dipendente] | None = None):
        if lista_dipendenti is not None:
            self.dipendenti = lista_dipendenti
        else:
            self.dipendenti = []


    def ripristina_dipendente(self, id_dipendente: int, nome: str, cognome: str, ferie_rimanenti: float, rol_rimanenti: float, stato_str: str):
        """Crea un'istanza di dipendente da dati grezzi (DB) e la aggiunge alla lista senza salvare su DB."""
        stato = StatoDipendente(stato_str) if stato_str else StatoDipendente.ASSUNTO
        
        dipendente = Dipendente(nome, cognome, stato, ferie_rimanenti, rol_rimanenti, [], id_dipendente)
        self.dipendenti.append(dipendente)


    def assumi_dipendente(self, nome: str, cognome: str, stato: StatoDipendente | None = None, ferie_rimanenti: float | None = None, rol_rimanenti : float | None = None, assenze_programmate: list[AssenzaProgrammata] | None = None):
        # Salva nel DB e ottieni l'ID generato
        id_dip = save_dipendente(nome, cognome, stato.value, ferie_rimanenti, rol_rimanenti, assenze_programmate)

        dipendente = Dipendente(id_dip, nome, cognome, stato, ferie_rimanenti, rol_rimanenti, assenze_programmate)

        self.dipendenti.append(dipendente)

    def rimuovi_dipendente(self, id_dipendente: int):
        result = sistemaSalvataggio.remove_dipendente(id_dipendente)
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


    def ripristina_assenza(self, id_dipendente: int, id_assenza: int, tipo_assenza_str: str, data_inizio: str, data_fine: str):
        """Ripristina un'assenza da dati grezzi e la associa al dipendente corretto."""
        for dipendente in self.dipendenti:
            if dipendente.id_dipendente == id_dipendente:
                # Creiamo l'oggetto assenza
                assenza = AssenzaProgrammata(
                    id_assenza=id_assenza,
                    data_inizio=data_inizio,
                    data_fine=data_fine,
                    tipo=tipo_assenza_str
                )
                dipendente.assenze_programmate.append(assenza)
                return True
        return False

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
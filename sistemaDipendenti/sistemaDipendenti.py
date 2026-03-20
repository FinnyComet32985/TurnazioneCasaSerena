

from sistemaDipendenti.assenzaProgrammata import AssenzaProgrammata, TipoAssenza
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


    def assumi_dipendente(self, nome: str, cognome: str, stato: StatoDipendente = StatoDipendente.ASSUNTO, ferie_rimanenti: float = 0, rol_rimanenti : float = 0):
        # Salva nel DB e ottieni l'ID generato
        id_dip = save_dipendente(nome, cognome, stato.value, ferie_rimanenti, rol_rimanenti)

        dipendente = Dipendente(nome, cognome, stato, ferie_rimanenti, rol_rimanenti, [], id_dip)

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

    def get_dipendente(self, id_dipendente: int):
        for dipendente in self.dipendenti:
            if dipendente.id_dipendente == id_dipendente:
                return dipendente
        return None

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

    def aggiungi_assenza(self, id_dipendente:int, tipo_assenza: TipoAssenza, data_inizio: str, data_fine: str):

        eseguito = False

        # Cerchiamo l'oggetto dipendente nella lista
        for dipendente in self.dipendenti:
            if dipendente.id_dipendente == id_dipendente:
                # Salviamo nel DB
                id_db = sistemaSalvataggio.save_assenza(id_dipendente, tipo_assenza.value, data_inizio, data_fine)
                
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

    def modifica_dipendente(self, id_dipendente: int, nome: str, cognome: str, ferie: float, rol: float):
        result = sistemaSalvataggio.update_dipendente(id_dipendente, nome, cognome, ferie, rol)
        if result:
            dip = self.get_dipendente(id_dipendente)
            if dip:
                dip.nome = nome
                dip.cognome = cognome
                dip.ferie_rimanenti = ferie
                dip.rol_rimanenti = rol
            return True
        return False
        
    def rimuovi_assenza(self, id_dipendente: int, id_assenza: int):
        result = sistemaSalvataggio.delete_assenza(id_assenza)
        if result:
            dip = self.get_dipendente(id_dipendente)
            if dip:
                dip.assenze_programmate = [a for a in dip.assenze_programmate if getattr(a, 'id_assenza', None) != id_assenza]
            return True
        return False
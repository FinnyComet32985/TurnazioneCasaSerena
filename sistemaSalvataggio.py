import sqlite3
from sqlite3 import Date

from sistemaTurnazione.assegnazioneTurno import AssegnazioneTurno

def save_turno(data_turno: Date, tipo_fascia: str, stato: str) -> int | None:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()

    tipo_fascia_val = tipo_fascia.value
    stato_val = stato.value

    query = "INSERT INTO turno (dataTurno, fasciaOraria, stato) VALUES (?, ?, ?)"
    try:
        cursor.execute(query, (data_turno, tipo_fascia_val, stato_val))
        connection.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Errore durante il salvataggio del turno: {e}")
        return None
    finally:
        connection.close()

def save_dipendente(nome, cognome, stato, ferie_rimanenti, rol_rimanenti) -> int:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()
    

    query = "INSERT INTO dipendente (nome, cognome, ferieRimanenti, rolRimanenti, stato) VALUES (?, ?, ?, ?, ?)"
    cursor.execute(query, (nome, cognome, ferie_rimanenti, rol_rimanenti, stato))
    
    connection.commit()
    id_generato = cursor.lastrowid # Recupera l'ID autoincrementato
    connection.close()
    
    return id_generato


def remove_dipendente(id_dipendente) -> bool:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()

    query = "UPDATE dipendente SET stato = 'LICENZIATO' WHERE idDipendente = ?"
    cursor.execute(query, (id_dipendente,))
    
    connection.commit()

    if cursor.rowcount > 0:
        res = True
    else:
        res = False
    
    connection.close()
    return res


def save_assenza(id_dipendente, tipo_assenza, data_inizio, data_fine) -> int | bool:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()

    # Estraiamo il valore stringa dall'Enum per il salvataggio
    if tipo_assenza:
        stato_val = tipo_assenza.value
    else:
        return False

    query = "INSERT INTO assenza (idDipendente, tipo, dataInizio, dataFine) VALUES (?, ?, ?, ?)"

    try: 
        cursor.execute(query, (id_dipendente, stato_val, data_inizio, data_fine))
    
        connection.commit()
        id_generato = cursor.lastrowid # Recupera l'ID autoincrementato
        connection.close()
    
        return id_generato
    except sqlite3.Error as e:
        print("errore nell'esecuzione della query: ", e)
        return False
    finally:
        connection.close()

def save_assegnazione(id_turno: int, assegnazione: AssegnazioneTurno) -> bool:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()

    jolly_val = 1 if assegnazione.jolly else 0
    turno_breve_val = 1 if assegnazione.turnoBreve else 0

    # Assicurati che il dipendente abbia un ID valido
    if not hasattr(assegnazione.dipendente, 'id_dipendente') or assegnazione.dipendente.id_dipendente is None:
        print(f"Errore: Il dipendente {assegnazione.dipendente.nome} {assegnazione.dipendente.cognome} non ha un ID valido per l'assegnazione.")
        connection.close()
        return False

    query = "INSERT INTO lavora (idDipendente, idTurno, piano, jolly, turnoBreve) VALUES (?, ?, ?, ?, ?)"
    try:
        cursor.execute(query, (
            assegnazione.dipendente.id_dipendente,
            id_turno,
            assegnazione.piano,
            jolly_val,
            turno_breve_val
        ))
        connection.commit()
        return True
    except sqlite3.Error as e:
        print(f"Errore durante il salvataggio dell'assegnazione: {e}")
        return False
    finally:
        connection.close()
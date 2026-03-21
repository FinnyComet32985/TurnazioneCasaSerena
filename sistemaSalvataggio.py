import sqlite3
from sqlite3 import Date

from sistemaTurnazione.assegnazioneTurno import AssegnazioneTurno


#* SISTEMA DIPENDENTI
#  salvataggio nuovo dipendente
def save_dipendente(nome, cognome, stato, ferie_rimanenti, rol_rimanenti, banca_ore) -> int:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()
    

    query = "INSERT INTO dipendente (nome, cognome, ferieRimanenti, rolRimanenti, bancaOre, stato) VALUES (?, ?, ?, ?, ?, ?)"
    cursor.execute(query, (nome, cognome, ferie_rimanenti, rol_rimanenti, banca_ore, stato))
    
    connection.commit()
    id_generato = cursor.lastrowid # Recupera l'ID autoincrementato
    connection.close()
    
    return id_generato
#  licenziamento dipendente
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

#* SISTEMA ASSENZE
#  salvataggio nuova assenza
def save_assenza(id_dipendente: int, tipo_assenza: str, data_inizio, data_fine) -> int | bool:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()

    query = "INSERT INTO assenza (idDipendente, tipo, dataInizio, dataFine) VALUES (?, ?, ?, ?)"

    try: 
        cursor.execute(query, (id_dipendente, tipo_assenza, data_inizio, data_fine))
    
        connection.commit()
        id_generato = cursor.lastrowid # Recupera l'ID autoincrementato
        connection.close()
    
        return id_generato
    except sqlite3.Error as e:
        print("errore nell'esecuzione della query: ", e)
        return False
    finally:
        connection.close()


#* SISTEMA TURNI
#  salvataggio nuovo turno
def save_turno(data_turno: Date, tipo_fascia: str, stato: str) -> int | None:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()

    query = "INSERT INTO turno (dataTurno, fasciaOraria, stato) VALUES (?, ?, ?)"
    try:
        cursor.execute(query, (data_turno, tipo_fascia, stato))
        connection.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        # Se viola il vincolo UNIQUE, recuperiamo l'ID esistente
        query_select = "SELECT idTurno FROM turno WHERE dataTurno = ? AND fasciaOraria = ?"
        cursor.execute(query_select, (data_turno, tipo_fascia))
        result = cursor.fetchone()
        connection.close()
        if result:
            return result[0]
        return None
    except sqlite3.Error as e:
        print(f"Errore durante il salvataggio del turno: {e}")
        return None


def update_stato_turno(id_turno: int, nuovo_stato: str) -> bool:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()
    query = "UPDATE turno SET stato = ? WHERE idTurno = ?"
    success = False
    try:
        cursor.execute(query, (nuovo_stato, id_turno))
        connection.commit()
        success = True
    except sqlite3.Error as e:
        print(f"Errore SQL Update Stato Turno: {e}")
    finally:
        connection.close()
    return success


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
    except sqlite3.IntegrityError as e:
        # Qui catturiamo sia duplicati sia l'errore del TRIGGER sulle assenze
        print(f"Impossibile assegnare turno: {e}")
        return False
    except sqlite3.Error as e:
        print(f"Errore durante il salvataggio dell'assegnazione: {e}")
        return False
    finally:
        connection.close()

def update_dipendente(id_dipendente: int, nome: str, cognome: str, ferie: float, rol: float, banca_ore: float) -> bool:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()
    query = "UPDATE dipendente SET nome=?, cognome=?, ferieRimanenti=?, rolRimanenti=?, bancaOre=? WHERE idDipendente=?"
    success = False
    try:
        cursor.execute(query, (nome, cognome, ferie, rol, banca_ore, id_dipendente))
        connection.commit()
        success = True
    except sqlite3.Error as e:
        print(f"Errore SQL Update Dipendente: {e}")
    finally:
        connection.close()
    return success

def delete_assenza(id_assenza: int) -> bool:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()
    query = "DELETE FROM assenza WHERE idAssenza = ?"
    success = False
    try:
        cursor.execute(query, (id_assenza,))
        connection.commit()
        success = True
    except sqlite3.Error as e:
        print(f"Errore SQL Delete Assenza: {e}")
    finally:
        connection.close()
    return success

def remove_assegnazione_turno(id_turno: int, id_dipendente: int) -> bool:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()
    query = "DELETE FROM lavora WHERE idTurno = ? AND idDipendente = ?"
    success = False
    try:
        cursor.execute(query, (id_turno, id_dipendente))
        connection.commit()
        success = True
    except sqlite3.Error as e:
        print(f"Errore SQL Delete Assegnazione Turno: {e}")
    finally:
        connection.close()
    return success

def set_turno_breve(id_turno: int, id_dipendente: int, turno_breve: bool) -> bool:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()
    val = 1 if turno_breve else 0
    query = "UPDATE lavora SET turnoBreve = ? WHERE idTurno = ? AND idDipendente = ?"
    success = False
    try:
        cursor.execute(query, (val, id_turno, id_dipendente))
        connection.commit()
        success = True
    except sqlite3.Error as e:
        print(f"Errore SQL set_turno_breve: {e}")
    finally:
        connection.close()
    return success

def save_last_update(data: str):
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()
    query = "INSERT OR REPLACE INTO configurazione (chiave, valore) VALUES ('last_update', ?)"
    try:
        cursor.execute(query, (data,))
        connection.commit()
    except sqlite3.Error as e:
        print(f"Errore SQL Save Last Update: {e}")
    finally:
        connection.close()

def get_data_ultimo_turno(id_dipendente: int, tipo_fascia: str) -> str | None:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()
    query = """
        SELECT MAX(t.dataTurno) 
        FROM lavora l
        JOIN turno t ON l.idTurno = t.idTurno
        WHERE l.idDipendente = ? AND t.fasciaOraria = ?
    """
    try:
        cursor.execute(query, (id_dipendente, tipo_fascia))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Errore SQL get_data_ultimo_turno: {e}")
        return None
    finally:
        connection.close()

def reset_settimana(data_inizio: str, data_fine: str) -> bool:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()
    
    # Cancelliamo le assegnazioni (lavora) per i turni nel range specificato
    query_del = """
        DELETE FROM lavora 
        WHERE idTurno IN (
            SELECT idTurno FROM turno 
            WHERE dataTurno >= ? AND dataTurno <= ?
        )
    """
    
    # Riportiamo lo stato dei turni a 'GENERATA' (pronti per essere riempiti)
    query_upd = "UPDATE turno SET stato = 'GENERATA' WHERE dataTurno >= ? AND dataTurno <= ?"

    success = False
    try:
        cursor.execute(query_del, (data_inizio, data_fine))
        cursor.execute(query_upd, (data_inizio, data_fine))
        connection.commit()
        success = True
    except sqlite3.Error as e:
        print(f"Errore SQL Reset Settimana: {e}")
    finally:
        connection.close()
    return success

def save_config(chiave: str, valore: str) -> bool:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()
    query = "INSERT OR REPLACE INTO configurazione (chiave, valore) VALUES (?, ?)"
    try:
        cursor.execute(query, (chiave, str(valore)))
        connection.commit()
        return True
    except sqlite3.Error as e:
        print(f"Errore SQL Save Config: {e}")
        return False
    finally:
        connection.close()

def get_config(chiave: str) -> str | None:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()
    query = "SELECT valore FROM configurazione WHERE chiave=?"
    try:
        cursor.execute(query, (chiave,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Errore SQL Get Config: {e}")
        return None
    finally:
        connection.close()

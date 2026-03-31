from db.database import DBManager
from sistemaTurnazione.assegnazioneTurno import AssegnazioneTurno

#* SISTEMA DIPENDENTI
#  salvataggio nuovo dipendente
def save_dipendente(nome, cognome, stato, ferie_rimanenti, rol_rimanenti) -> int:
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    
    query = "INSERT INTO dipendente (nome, cognome, ferieRimanenti, rolRimanenti, stato) VALUES (%s, %s, %s, %s, %s) RETURNING idDipendente"
    cursor.execute(query, (nome, cognome, float(ferie_rimanenti), float(rol_rimanenti), stato))
    
    id_generato = cursor.fetchone()[0]
    connection.commit()
    cursor.close()
    DBManager.put_conn(connection)
    
    return id_generato

#  licenziamento dipendente
def remove_dipendente(id_dipendente) -> bool:
    connection = DBManager.get_conn()
    cursor = connection.cursor()

    query = "UPDATE dipendente SET stato = 'LICENZIATO' WHERE idDipendente = %s"
    cursor.execute(query, (id_dipendente,))
    
    connection.commit()

    if cursor.rowcount > 0:
        res = True
    else:
        res = False
    
    cursor.close()
    DBManager.put_conn(connection)
    return res

#  riassunzione dipendente
def riassumi_dipendente(id_dipendente) -> bool:
    connection = DBManager.get_conn()
    cursor = connection.cursor()

    query = "UPDATE dipendente SET stato = 'ASSUNTO' WHERE idDipendente = %s"
    cursor.execute(query, (id_dipendente,))
    
    connection.commit()

    if cursor.rowcount > 0:
        res = True
    else:
        res = False
    
    cursor.close()
    DBManager.put_conn(connection)
    return res

#* SISTEMA ASSENZE
#  salvataggio nuova assenza
def save_assenza(id_dipendente: int, tipo_assenza: str, data_inizio, data_fine) -> int:
    connection = DBManager.get_conn()
    cursor = connection.cursor()

    query = "INSERT INTO assenza (idDipendente, tipo, dataInizio, dataFine) VALUES (%s, %s, %s, %s) RETURNING idAssenza"

    try: 
        cursor.execute(query, (id_dipendente, tipo_assenza, data_inizio, data_fine))
        id_generato = cursor.fetchone()[0]
        connection.commit()
        return id_generato
    except Exception as e:
        print("errore nell'esecuzione della query: ", e)
        return False
    finally:
        cursor.close()
        DBManager.put_conn(connection)


#* SISTEMA TURNI
#  salvataggio nuovo turno
def save_turno(data_turno, tipo_fascia: str, stato: str) -> int:
    connection = DBManager.get_conn()
    cursor = connection.cursor()

    query = "INSERT INTO turno (dataTurno, fasciaOraria, stato) VALUES (%s, %s, %s) RETURNING idTurno"
    try:
        cursor.execute(query, (data_turno, tipo_fascia, stato))
        id_generato = cursor.fetchone()[0]
        connection.commit()
        return id_generato
    except Exception:
        # Se viola il vincolo UNIQUE, recuperiamo l'ID esistente
        connection.rollback()
        query_select = "SELECT idTurno FROM turno WHERE dataTurno = %s AND fasciaOraria = %s"
        cursor.execute(query_select, (data_turno, tipo_fascia))
        result = cursor.fetchone()
        cursor.close()
        DBManager.put_conn(connection)
        if result:
            return result[0]
        return None

def update_stato_turno(id_turno: int, nuovo_stato: str) -> bool:
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    query = "UPDATE turno SET stato = %s WHERE idTurno = %s"
    success = False
    try:
        cursor.execute(query, (nuovo_stato, id_turno))
        connection.commit()
        success = True
    except Exception as e:
        print(f"Errore SQL Update Stato Turno: {e}")
    finally:
        cursor.close()
        DBManager.put_conn(connection)
    return success


def save_assegnazione(id_turno: int, assegnazione: AssegnazioneTurno) -> bool:
    connection = DBManager.get_conn()
    cursor = connection.cursor()

    # Assicurati che il dipendente abbia un ID valido
    if not hasattr(assegnazione.dipendente, 'id_dipendente') or assegnazione.dipendente.id_dipendente is None:
        print(f"Errore: Il dipendente {assegnazione.dipendente.nome} {assegnazione.dipendente.cognome} non ha un ID valido per l'assegnazione.")
        cursor.close()
        DBManager.put_conn(connection)
        return False

    query = "INSERT INTO lavora (idDipendente, idTurno, piano, jolly, turnoBreve) VALUES (%s, %s, %s, %s, %s)"
    try:
        cursor.execute(query, (
            assegnazione.dipendente.id_dipendente,
            id_turno,
            assegnazione.piano,
            assegnazione.jolly,
            assegnazione.turnoBreve
        ))
        connection.commit()
        return True
    except Exception as e:
        # Qui catturiamo sia duplicati sia l'errore del TRIGGER sulle assenze
        print(f"Impossibile assegnare turno: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        DBManager.put_conn(connection)

def update_dipendente(id_dipendente: int, nome: str, cognome: str, ferie: float, rol: float) -> bool:
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    query = "UPDATE dipendente SET nome=%s, cognome=%s, ferieRimanenti=%s, rolRimanenti=%s WHERE idDipendente=%s"
    success = False
    try:
        cursor.execute(query, (nome, cognome, float(ferie), float(rol), id_dipendente))
        connection.commit()
        success = True
    except Exception as e:
        print(f"Errore SQL Update Dipendente: {e}")
    finally:
        cursor.close()
        DBManager.put_conn(connection)
    return success

def save_variazione_banca_ore(id_dipendente: int, key: str, valore: float, descrizione: str = "") -> bool:
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    # Postgres usa INSERT ... ON CONFLICT
    query = """
        INSERT INTO variazioneBancaOre (idDipendente, key, valore, descrizione) 
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (idDipendente, key) DO UPDATE SET valore = EXCLUDED.valore, descrizione = EXCLUDED.descrizione
    """
    success = False
    try:
        cursor.execute(query, (id_dipendente, key, float(valore), descrizione))
        connection.commit()
        success = True
    except Exception as e:
        print(f"Errore SQL Save Variazione Banca Ore: {e}")
    finally:
        cursor.close()
        DBManager.put_conn(connection)
    return success

def delete_variazione_banca_ore(id_dipendente: int, key: str) -> bool:
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    query = "DELETE FROM variazioneBancaOre WHERE idDipendente = %s AND key = %s"
    success = False
    try:
        cursor.execute(query, (id_dipendente, key))
        connection.commit()
        success = True
    except Exception as e:
        print(f"Errore SQL Delete Variazione Banca Ore: {e}")
    finally:
        cursor.close()
        DBManager.put_conn(connection)
    return success

def get_variazioni_banca_ore(id_dipendente: int) -> list:
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    query = "SELECT key, valore, descrizione FROM variazioneBancaOre WHERE idDipendente = %s"
    try:
        cursor.execute(query, (id_dipendente,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Errore SQL Get Variazioni Banca Ore: {e}")
        return []
    finally:
        cursor.close()
        DBManager.put_conn(connection)

def delete_assenza(id_assenza: int) -> bool:
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    query = "DELETE FROM assenza WHERE idAssenza = %s"
    success = False
    try:
        cursor.execute(query, (id_assenza,))
        connection.commit()
        success = True
    except Exception as e:
        print(f"Errore SQL Delete Assenza: {e}")
    finally:
        cursor.close()
        DBManager.put_conn(connection)
    return success

def remove_assegnazione_turno(id_turno: int, id_dipendente: int) -> bool:
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    query = "DELETE FROM lavora WHERE idTurno = %s AND idDipendente = %s"
    success = False
    try:
        cursor.execute(query, (id_turno, id_dipendente))
        connection.commit()
        success = True
    except Exception as e:
        print(f"Errore SQL Delete Assegnazione Turno: {e}")
    finally:
        cursor.close()
        DBManager.put_conn(connection)
    return success

def set_turno_breve(id_turno: int, id_dipendente: int, turno_breve: bool) -> bool:
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    query = "UPDATE lavora SET turnoBreve = %s WHERE idTurno = %s AND idDipendente = %s"
    success = False
    try:
        cursor.execute(query, (turno_breve, id_turno, id_dipendente))
        connection.commit()
        success = True
    except Exception as e:
        print(f"Errore SQL set_turno_breve: {e}")
    finally:
        cursor.close()
        DBManager.put_conn(connection)
    return success

def save_last_update(data: str):
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    query = """
        INSERT INTO configurazione (chiave, valore) VALUES ('last_update', %s)
        ON CONFLICT (chiave) DO UPDATE SET valore = EXCLUDED.valore
    """
    try:
        cursor.execute(query, (data,))
        connection.commit()
    except Exception as e:
        print(f"Errore SQL Save Last Update: {e}")
    finally:
        cursor.close()
        DBManager.put_conn(connection)

def get_data_ultimo_turno(id_dipendente: int, tipo_fascia: str) -> str | None:
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    query = """
        SELECT MAX(t.dataTurno) 
        FROM lavora l
        JOIN turno t ON l.idTurno = t.idTurno
        WHERE l.idDipendente = %s AND t.fasciaOraria = %s
    """
    try:
        cursor.execute(query, (id_dipendente, tipo_fascia))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Errore SQL get_data_ultimo_turno: {e}")
        return None
    finally:
        cursor.close()
        DBManager.put_conn(connection)

def reset_settimana(data_inizio: str, data_fine: str) -> bool:
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    
    # Cancelliamo le assegnazioni (lavora) per i turni nel range specificato,
    # TRANNE quelle di tipo RIPOSO che derivano da una NOTTE fatta prima dell'inizio del range.
    query_del = """
        DELETE FROM lavora 
        WHERE idTurno IN (
            SELECT idTurno FROM turno 
            WHERE dataTurno >= ? AND dataTurno <= ?
        )
        AND NOT EXISTS (
            SELECT 1 FROM turno t_curr
            WHERE t_curr.idTurno = lavora.idTurno
            AND t_curr.fasciaOraria = 'RIPOSO'
            AND EXISTS (
                SELECT 1 FROM turno t_prev
                JOIN lavora l_prev ON t_prev.idTurno = l_prev.idTurno
                WHERE l_prev.idDipendente = lavora.idDipendente
                AND t_prev.fasciaOraria = 'NOTTE'
                AND t_prev.dataTurno < %s
                AND (
                    t_curr.dataTurno - INTERVAL '1 day' = t_prev.dataTurno OR 
                    t_curr.dataTurno - INTERVAL '2 day' = t_prev.dataTurno
                )
            )
        )
    """
    
    # Riportiamo lo stato dei turni a 'GENERATO' (pronti per essere riempiti)
    query_upd = "UPDATE turno SET stato = 'GENERATO' WHERE dataTurno >= %s AND dataTurno <= %s"

    success = False
    try:
        cursor.execute(query_del, (data_inizio, data_fine, data_inizio))
        cursor.execute(query_upd, (data_inizio, data_fine))
        connection.commit()
        success = True
    except Exception as e:
        print(f"Errore SQL Reset Settimana: {e}")
    finally:
        cursor.close()
        DBManager.put_conn(connection)
    return success

def save_config(chiave: str, valore: str) -> bool:
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    query = """
        INSERT INTO configurazione (chiave, valore) VALUES (%s, %s)
        ON CONFLICT (chiave) DO UPDATE SET valore = EXCLUDED.valore
    """
    try:
        cursor.execute(query, (chiave, str(valore)))
        connection.commit()
        return True
    except Exception as e:
        print(f"Errore SQL Save Config: {e}")
        return False
    finally:
        cursor.close()
        DBManager.put_conn(connection)

def get_config(chiave: str) -> str | None:
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    query = "SELECT valore FROM configurazione WHERE chiave=%s"
    try:
        cursor.execute(query, (chiave,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Errore SQL Get Config: {e}")
        return None
    finally:
        cursor.close()
        DBManager.put_conn(connection)

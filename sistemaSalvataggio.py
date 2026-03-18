import sqlite3

from sistemaDipendenti.dipendente import Dipendente, StatoDipendente
from sistemaDipendenti.assenzaProgrammata import AssenzaProgrammata



def load_dipendenti() -> list[Dipendente] :
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()

    query = "select * from dipendente"

    cursor.execute(query)
    dipendenti_rows = cursor.fetchall()

    lista_dipendenti = []

    for dipendente_row in dipendenti_rows:

        # riga è una tupla: (id, nome, cognome, ferie, rol, stato)
        # Convertiamo la stringa dello stato nell'Enum
        stato_enum = StatoDipendente(dipendente_row[5]) if dipendente_row[5] else StatoDipendente.ASSUNTO
        
        dipendente = Dipendente(
            id_dipendente=dipendente_row[0],
            nome=dipendente_row[1],
            cognome=dipendente_row[2],
            ferie_rimanenti=dipendente_row[3],
            rol_rimanenti=dipendente_row[4],
            stato=stato_enum,
            assenze_programmate=[] # Per ora lista vuota, andrà caricata dalla tabella assenze
        )
        lista_dipendenti.append(dipendente)

        for dipendente in lista_dipendenti:
            query = "select * from assenza where idDipendente = ?"
            cursor.execute(query, (dipendente.id_dipendente,))
            assenze_rows = cursor.fetchall()

            for assenza_row in assenze_rows:
                assenza = AssenzaProgrammata(
                    id_assenza=assenza_row[0],
                    data_inizio=assenza_row[2],
                    data_fine=assenza_row[3],
                    tipo=assenza_row[1]
                )
                dipendente.assenze_programmate.append(assenza)

    
    connection.close()
    return lista_dipendenti


def load_turni():
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()

    query = "select * from turno"

    cursor.execute(query)
    turni = cursor.fetchall()

    for turno in turni:
        print(turno)

    

    connection.close()
    return 

def save_dipendente(dipendente) -> int:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()

    # Estraiamo il valore stringa dall'Enum per il salvataggio
    stato_val = dipendente.stato.value if dipendente.stato else 'ASSUNTO'

    query = "INSERT INTO dipendente (nome, cognome, ferieRimanenti, rolRimanenti, stato) VALUES (?, ?, ?, ?, ?)"
    cursor.execute(query, (dipendente.nome, dipendente.cognome, dipendente.ferie_rimanenti, dipendente.rol_rimanenti, stato_val))
    
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
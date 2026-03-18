import sqlite3

from sistemaDipendenti.dipendente import Dipendente, StatoDipendente


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

def salva_dipendente(dipendente):
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


def rimuovi_dipendente(id_dipendente):
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
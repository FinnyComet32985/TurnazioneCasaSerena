import sqlite3
from sistemaDipendenti.sistemaDipendenti import SistemaDipendenti
from sistemaTurnazione.turnazione import Turnazione

def load_dipendenti() -> SistemaDipendenti:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()

    query = "select * from dipendente"

    cursor.execute(query)
    dipendenti_rows = cursor.fetchall()

    # Istanziamo il sistema qui
    sistema = SistemaDipendenti()

    for dipendente_row in dipendenti_rows:
        # riga è una tupla: (id, nome, cognome, ferie, rol, stato)
        sistema.ripristina_dipendente(
            id_dipendente=dipendente_row[0], 
            nome=dipendente_row[1],
            cognome=dipendente_row[2], 
            ferie_rimanenti=dipendente_row[3], 
            rol_rimanenti=dipendente_row[4], 
            stato_str=dipendente_row[5]
        )

        # Carichiamo le assenze per questo dipendente
        query_assenze = "select * from assenza where idDipendente = ?"
        cursor.execute(query_assenze, (dipendente_row[0],))
        assenze_rows = cursor.fetchall()

        for assenza_row in assenze_rows:
            sistema.ripristina_assenza(
                id_dipendente=dipendente_row[0],
                id_assenza=assenza_row[0],
                tipo_assenza_str=assenza_row[1], # Assumo che row[1] sia il tipo come nel codice precedente
                data_inizio=assenza_row[2],
                data_fine=assenza_row[3]
            )
    
    connection.close()
    return sistema


def load_turni(sistema_dipendenti: SistemaDipendenti) -> Turnazione:
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()

    query = "select * from turno"
    cursor.execute(query)
    turni_rows = cursor.fetchall()

    turnazione = Turnazione()

    for turno_row in turni_rows:
        # turno_row: (idTurno, dataTurno, fasciaOraria, stato)
        id_turno = turno_row[0]
        
        turnazione.ripristina_fascia(
            id_turno=id_turno,
            data_str=turno_row[1],
            tipo_fascia_str=turno_row[2],
            stato_str=turno_row[3]
        )

        # Carichiamo le assegnazioni (lavora) per questo turno
        query_lavora = "SELECT idDipendente, piano, jolly, turnoBreve FROM lavora WHERE idTurno = ?"
        cursor.execute(query_lavora, (id_turno,))
        lavora_rows = cursor.fetchall()

        for lav in lavora_rows:
            # Risolviamo l'ID in Oggetto Dipendente usando il sistema passato
            dipendente_obj = sistema_dipendenti.get_dipendente(lav[0])
            if dipendente_obj is None:
                continue

            turnazione.ripristina_assegnazione(
                id_turno=id_turno,
                dipendente=dipendente_obj,
                piano=lav[1],
                jolly=bool(lav[2]),
                turno_breve=bool(lav[3])
            )
    
    connection.close()
    return turnazione
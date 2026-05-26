import re
import sqlite3
from datetime import date, datetime, timedelta
from sistemaDipendenti.sistemaDipendenti import SistemaDipendenti
from sistemaTurnazione.turnazione import Turnazione
from sistemaDipendenti.variazioneBancaOre import VariazioneBancaOre

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
        id_dip = dipendente_row[0]

        # Recuperiamo il saldo totale della banca ore sommando le variazioni dal nuovo database
        cursor.execute("SELECT SUM(valore) FROM variazioneBancaOre WHERE idDipendente = ?", (id_dip,))
        res_banca = cursor.fetchone()
        banca_ore_totale = res_banca[0] if res_banca and res_banca[0] is not None else 0.0

        # Recuperiamo le singole variazioni per popolare la lista in memoria e permettere storni corretti
        cursor.execute("SELECT key, valore, descrizione FROM variazioneBancaOre WHERE idDipendente = ?", (id_dip,))
        var_rows = cursor.fetchall()
        variazioni = [VariazioneBancaOre(r[0], r[1], r[2]) for r in var_rows]

        sistema.ripristina_dipendente(
            id_dipendente=id_dip, 
            nome=dipendente_row[1],
            cognome=dipendente_row[2], 
            ferie_rimanenti=dipendente_row[3], 
            rol_rimanenti=dipendente_row[4], 
            banca_ore=banca_ore_totale,
            stato_str=dipendente_row[5],
            variazioni=variazioni
        )

        # Carichiamo le assenze per questo dipendente
        query_assenze = "select * from assenza where idDipendente = ?"
        cursor.execute(query_assenze, (dipendente_row[0],))
        assenze_rows = cursor.fetchall()

        for assenza_row in assenze_rows:
            sistema.ripristina_assenza(
                id_dipendente=assenza_row[1],
                id_assenza=assenza_row[0],
                tipo_assenza_str=assenza_row[2],
                data_inizio=assenza_row[3],
                data_fine=assenza_row[4]
            )
    
    connection.close()
    return sistema


def load_turni(sistema_dipendenti: SistemaDipendenti) -> Turnazione:
    turnazione = Turnazione()
    turnazione.sistema_dipendenti = sistema_dipendenti
    turnazione.loaded_weeks = set()

    # Carichiamo le settimane recenti: precedente, corrente, successiva
    today = date.today()
    current_monday = today - timedelta(days=today.weekday())

    for offset in [-1, 0, 1]:
        d = current_monday + timedelta(weeks=offset)
        anno, settimana, _ = d.isocalendar()
        key = (anno, settimana)
        load_settimana(turnazione, key, sistema_dipendenti)
        turnazione.loaded_weeks.add(key)

    return turnazione


def load_settimana(turnazione: Turnazione, settimana_key: tuple[int, int], sistema_dipendenti: SistemaDipendenti):
    anno, settimana = settimana_key
    # Calcola il primo giorno (Lunedì) della settimana ISO
    primo_giorno = date.fromisocalendar(anno, settimana, 1)
    ultimo_giorno = primo_giorno + timedelta(days=6)

    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()

    # Recupera tutti i turni nel range di date della settimana
    query_turni = "SELECT idTurno, dataTurno, fasciaOraria, stato FROM turno WHERE dataTurno >= ? AND dataTurno <= ?"
    cursor.execute(query_turni, (primo_giorno.strftime("%Y-%m-%d"), ultimo_giorno.strftime("%Y-%m-%d")))
    turni_rows = cursor.fetchall()

    if not turni_rows:
        connection.close()
        return

    # Recupera tutte le assegnazioni della settimana
    query_lavora = """
        SELECT l.idTurno, l.idDipendente, l.piano, l.jolly, l.turnoBreve 
        FROM lavora l 
        JOIN turno t ON l.idTurno = t.idTurno 
        WHERE t.dataTurno >= ? AND t.dataTurno <= ?
    """
    cursor.execute(query_lavora, (primo_giorno.strftime("%Y-%m-%d"), ultimo_giorno.strftime("%Y-%m-%d")))
    lavora_rows = cursor.fetchall()
    connection.close()

    # Raggruppa le assegnazioni per idTurno
    lavora_by_turno = {}
    for lav in lavora_rows:
        id_turno = lav[0]
        lavora_by_turno.setdefault(id_turno, []).append(lav)

    for turno_row in turni_rows:
        id_turno = turno_row[0]
        
        turnazione.ripristina_fascia(
            id_turno=id_turno,
            data_str=turno_row[1],
            tipo_fascia_str=turno_row[2],
            stato_str=turno_row[3]
        )

        for lav in lavora_by_turno.get(id_turno, []):
            dipendente_obj = sistema_dipendenti.get_dipendente(lav[1])
            if dipendente_obj is None:
                continue

            turnazione.ripristina_assegnazione(
                id_turno=id_turno,
                dipendente=dipendente_obj,
                piano=lav[2],
                jolly=bool(lav[3]),
                turno_breve=bool(lav[4])
            )



def load_last_update():
    connection = sqlite3.connect('./db/turnazione.db')
    cursor = connection.cursor()

    query = "SELECT valore FROM configurazione WHERE chiave='last_update'"

    cursor.execute(query)
    result = cursor.fetchone()

    if result:
        connection.close()
        return result[0]
    else:
        connection.close()
        return None
    
    
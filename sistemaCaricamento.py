from datetime import datetime, date, timedelta
import re
from db.database import DBManager
from sistemaDipendenti.sistemaDipendenti import SistemaDipendenti
from sistemaTurnazione.turnazione import Turnazione
from sistemaTurnazione.fasciaOraria import FasciaOraria, TipoFascia, StatoFascia
from sistemaDipendenti.variazioneBancaOre import VariazioneBancaOre

def load_dipendenti() -> SistemaDipendenti:
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    try:
        query = "select * from dipendente"
        cursor.execute(query)
        dipendenti_rows = cursor.fetchall()

        sistema = SistemaDipendenti()

        for dipendente_row in dipendenti_rows:
            id_dip = dipendente_row[0]

            cursor.execute("SELECT SUM(valore) FROM variazioneBancaOre WHERE idDipendente = %s", (id_dip,))
            res_banca = cursor.fetchone()
            banca_ore_totale = res_banca[0] if res_banca and res_banca[0] is not None else 0.0

            cursor.execute("SELECT key, valore, descrizione FROM variazioneBancaOre WHERE idDipendente = %s", (id_dip,))
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

            query_assenze = "SELECT * FROM assenza WHERE idDipendente = %s"
            cursor.execute(query_assenze, (id_dip,))
            assenze_rows = cursor.fetchall()

            for assenza_row in assenze_rows:
                sistema.ripristina_assenza(
                    id_dipendente=assenza_row[1],
                    id_assenza=assenza_row[0],
                    tipo_assenza_str=assenza_row[2],
                    data_inizio=assenza_row[3],
                    data_fine=assenza_row[4]
                )
        return sistema
    finally:
        cursor.close()
        DBManager.put_conn(connection)

def _load_turni_and_assegnazioni_for_date_range(start_date: date, end_date: date, sistema_dipendenti: SistemaDipendenti) -> dict[tuple[int, int], dict[date, dict[TipoFascia, FasciaOraria]]]:
    """
    Carica turni e assegnazioni per un intervallo di date specificato.
    Questa è la funzione core che verrà riutilizzata.
    """
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    try:
        # Query per i turni nell'intervallo di date
        query_turni = "SELECT idTurno, dataTurno, fasciaOraria, stato FROM turno WHERE dataTurno >= %s AND dataTurno <= %s"
        cursor.execute(query_turni, (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
        turni_rows = cursor.fetchall()

        # Dizionario temporaneo per costruire la struttura
        loaded_turnations: dict[tuple[int, int], dict[date, dict[TipoFascia, FasciaOraria]]] = {}

        for turno_row in turni_rows:
            id_turno = turno_row[0]
            data_turno_str = turno_row[1]
            tipo_fascia_str = turno_row[2]
            stato_str = turno_row[3]
            if isinstance(data_turno_str, str):
                data_turno = datetime.strptime(data_turno_str, "%Y-%m-%d").date()
            else:
                # Se è già un oggetto date o datetime
                data_turno = data_turno_str.date() if hasattr(data_turno_str, "date") else data_turno_str

            tipo_fascia = TipoFascia(tipo_fascia_str)
            stato = StatoFascia(stato_str)

            fascia = FasciaOraria(data_turno, tipo_fascia, assegnazioni=[], stato=stato, id_turno=id_turno)

            anno, settimana, _ = data_turno.isocalendar()
            settimana_key = (anno, settimana)

            loaded_turnations.setdefault(settimana_key, {}).setdefault(data_turno, {})[tipo_fascia] = fascia

        # Ora carichiamo le assegnazioni per tutti i turni caricati
        if turni_rows:
            # Estraiamo tutti gli idTurno per una singola query batch
            id_turni_list = [row[0] for row in turni_rows]
            
            # Usiamo un placeholder dinamico per la lista di ID
            placeholders = ','.join(['%s'] * len(id_turni_list))
            query_lavora = f"SELECT idDipendente, idTurno, piano, jolly, turnoBreve FROM lavora WHERE idTurno IN ({placeholders})"
            cursor.execute(query_lavora, id_turni_list)
            lavora_rows = cursor.fetchall()

            for lav in lavora_rows:
                id_dipendente = lav[0]
                id_turno_assegnazione = lav[1]
                piano = lav[2]
                jolly = bool(lav[3])
                turno_breve = bool(lav[4])

                dipendente_obj = sistema_dipendenti.get_dipendente(id_dipendente)
                if dipendente_obj is None:
                    print(f"WARNING: Dipendente con ID {id_dipendente} non trovato per assegnazione turno {id_turno_assegnazione}.")
                    continue

                # Trova la fascia oraria corrispondente e aggiungi l'assegnazione
                for settimana_dict in loaded_turnations.values():
                    for giorno_dict in settimana_dict.values():
                        for fascia in giorno_dict.values():
                            if getattr(fascia, 'id_turno', None) == id_turno_assegnazione:
                                from sistemaTurnazione.assegnazioneTurno import AssegnazioneTurno # Import qui per evitare dipendenza circolare
                                assegnazione = AssegnazioneTurno(dipendente_obj, turnoBreve=turno_breve, piano=piano, jolly=jolly)
                                fascia.ripristina_assegnazione(assegnazione)
                                break # Trovata la fascia, passa alla prossima assegnazione
        return loaded_turnations
    finally:
        cursor.close()
        DBManager.put_conn(connection)

def load_initial_turni(sistema_dipendenti: SistemaDipendenti, weeks_before: int = 2, weeks_after: int = 2) -> dict[tuple[int, int], dict[date, dict[TipoFascia, FasciaOraria]]]:
    """
    Carica un numero limitato di turnazioni (settimane) intorno alla settimana corrente.
    """
    today = date.today()
    current_monday = today - timedelta(days=today.weekday()) # Lunedì della settimana corrente

    start_date = current_monday - timedelta(weeks=weeks_before)
    end_date = current_monday + timedelta(weeks=weeks_after) + timedelta(days=6) # Fine della settimana 'weeks_after'

    print(f"Caricamento turni iniziali dal {start_date} al {end_date}...")
    return _load_turni_and_assegnazioni_for_date_range(start_date, end_date, sistema_dipendenti)

def load_turni_for_week(anno: int, settimana: int, sistema_dipendenti: SistemaDipendenti) -> dict[tuple[int, int], dict[date, dict[TipoFascia, FasciaOraria]]]:
    """
    Carica tutti i turni e le assegnazioni per una specifica settimana ISO.
    """
    primo_giorno_settimana = date.fromisocalendar(anno, settimana, 1)
    ultimo_giorno_settimana = primo_giorno_settimana + timedelta(days=6)
    
    print(f"Caricamento turni per settimana {anno}-{settimana} ({primo_giorno_settimana} - {ultimo_giorno_settimana})...")
    return _load_turni_and_assegnazioni_for_date_range(primo_giorno_settimana, ultimo_giorno_settimana, sistema_dipendenti)


def load_last_update():
    connection = DBManager.get_conn()
    cursor = connection.cursor()
    try:
        query = "SELECT valore FROM configurazione WHERE chiave = 'last_update'"
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            return result[0]
        return None
    finally:
        cursor.close()
        DBManager.put_conn(connection)
    
    
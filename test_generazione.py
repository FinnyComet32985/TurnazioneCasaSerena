#!/usr/bin/env python3
"""
Test di generazione turnazione — backend diretto, senza GUI né DB permanente.

Utilizzo:
    python test_generazione.py              # Esegue tutti i test (usa un DB temporaneo)
    python test_generazione.py --baseline   # Solo test con limiti standard
    python test_generazione.py --stress     # Solo test con limiti aumentati
    python test_generazione.py --seed       # Genera solo il file seed SQL e esce
    python test_generazione.py --keep       # Mantiene il DB di test a esecuzione terminata

Il file crea un DB temporaneo in `db/turnazione_test.db`, lo usa per i test
e lo cancella al termine (a meno di --keep).
Per popolare manualmente il DB, eseguire init_db.py poi db/test_stress_data.sql.
"""

import argparse
import os
import random
import sqlite3
import sys
from datetime import date, timedelta, datetime

# ── Bootstrapping ──────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix terminal encoding on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TEST_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "turnazione_test.db")
SCHEMA_SQL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "schema.sql")
STRESS_DATA_SQL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "test_stress_data.sql")


def _read_sql(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def setup_test_db():
    """Crea il DB temporaneo: schema + seed data."""
    os.makedirs(os.path.dirname(TEST_DB), exist_ok=True)
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    conn = sqlite3.connect(TEST_DB)
    conn.executescript(_read_sql(SCHEMA_SQL))
    if os.path.exists(STRESS_DATA_SQL):
        conn.executescript(_read_sql(STRESS_DATA_SQL))
        seed_msg = " + " + os.path.basename(STRESS_DATA_SQL)
    else:
        seed_msg = ""
    conn.commit()
    conn.close()
    print(f"[OK] DB di test creato: {TEST_DB} (schema{seed_msg})")


def cleanup_test_db():
    """Rimuove il DB di test."""
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
            print(f"[OK] DB di test {TEST_DB} eliminato.")
        except PermissionError:
            # Sul Windows, sqlite3 può tenere il file aperto per un attimo dopo l'ultimo accesso
            import time
            time.sleep(1)
            try:
                os.remove(TEST_DB)
                print(f"[OK] DB di test {TEST_DB} eliminato.")
            except PermissionError:
                print(f"[WARN] DB di test {TEST_DB} non eliminato (ancora aperto).")


def patch_db():
    """Monkey-patch sqlite3.connect → punta su TEST_DB anziché sul DB reale."""
    import sqlite3 as sqlite3_mod
    original_connect = sqlite3_mod.connect
    main_marker = "turnazione.db"

    def patched_connect(db_path, *args, **kwargs):
        p = str(db_path)
        if main_marker in p and "turnazione_test.db" not in p:
            p = TEST_DB
        return original_connect(p, *args, **kwargs)

    import unittest.mock as mock
    patcher = mock.patch.object(sqlite3_mod, 'connect', patched_connect)
    patcher.start()
    return patcher


def summarize_result(label, sistema_dipendenti, turnazione, anno, settimane):
    """Analizza i risultati di una o più generazioni e produce un report."""
    print(f"\n{'─' * 60}")
    print(f"  ANALISI: {label}")
    print(f"{'─' * 60}")

    attivi = [d for d in sistema_dipendenti.get_lista_dipendenti()
              if d.stato.value == "ASSUNTO"]
    print(f"  Dipendenti attivi: {len(attivi)}")

    from sistemaTurnazione.fasciaOraria import TipoFascia

    grand_slots = 0
    grand_filled = 0
    grand_underfilled = []

    for settimana in settimane:
        wk = (anno, settimana)
        sett_dict = turnazione.get_turnazione_settimana(wk)
        primo = date.fromisocalendar(anno, settimana, 1)
        giorni = [primo + timedelta(days=i) for i in range(7)]

        wk_slots = 0
        wk_filled = 0

        for g in giorni:
            if g not in sett_dict:
                continue
            for tf in [TipoFascia.MATTINA, TipoFascia.POMERIGGIO, TipoFascia.NOTTE]:
                fascia = sett_dict[g].get(tf)
                if not fascia:
                    continue
                target = turnazione.limiti_fascia.get(tf, 0)
                actual = len(fascia.assegnazioni) if fascia.assegnazioni else 0
                wk_slots += target
                wk_filled += actual
                if actual < target:
                    grand_underfilled.append(
                        f"W{settimana} {g.strftime('%d/%m')} {tf.value}: {actual}/{target}")

        grand_slots += wk_slots
        grand_filled += wk_filled

        pct = round(wk_filled / wk_slots * 100, 1) if wk_slots else 0
        print(f"  Settimana {settimana}: {wk_filled}/{wk_slots} slot compilati ({pct}%)")

    total_pct = round(grand_filled / grand_slots * 100, 1) if grand_slots else 0
    print(f"\n  TOTALE: {grand_filled}/{grand_slots} slot compilati ({total_pct}%)")

    if grand_underfilled:
        print(f"\n  Fasce non completamente riempite ({len(grand_underfilled)}):")
        for u in grand_underfilled[:15]:
            print(f"    - {u}")
        if len(grand_underfilled) > 15:
            print(f"    ... e altri {len(grand_underfilled) - 15}")

    # Controllo ore settimanali per ogni dipendente
    print(f"\n  Riepilogo ore settimanali per dipendente:")
    for settimana in settimane:
        wk = (anno, settimana)
        print(f"\n  Settimana {settimana}:")
        for dip in attivi[:10]:
            ore = turnazione._get_ore_lavorate_settimana(dip.id_dipendente, wk)
            flag = " ⚠️" if ore > 38 else ""
            print(f"    {dip.cognome} {dip.nome[0]}.: {ore}h{flag}")
        if len(attivi) > 10:
            print(f"    ... (+{len(attivi) - 10} dipendenti)")

    print(f"{'=' * 60}\n")
    return total_pct >= 90


def run_generation(test_label, anno, settimane, config_overrides=None):
    """
    Esegue la generazione per le settimane indicate.
    config_overrides: dict {key: value} per sovrascrivere la configurazione.
    """
    patcher = patch_db()

    try:
        from sistemaDipendenti.sistemaDipendenti import SistemaDipendenti
        from sistemaTurnazione.turnazione import Turnazione
        from sistemaTurnazione.sistemaGenerazione import SistemaGenerazione
        from sistemaTurnazione.fasciaOraria import TipoFascia
        from sistemaCaricamento import load_dipendenti

        sistema_dipendenti = load_dipendenti()
        turnazione = Turnazione()
        turnazione.sistema_dipendenti = sistema_dipendenti
        turnazione.loaded_weeks = set()
        turnazione.load_configuration()

        if config_overrides:
            turnazione.limiti_fascia = {
                TipoFascia.MATTINA: 0,
                TipoFascia.POMERIGGIO: 0,
                TipoFascia.NOTTE: 0,
            }
            for tf in [TipoFascia.MATTINA, TipoFascia.POMERIGGIO, TipoFascia.NOTTE]:
                tf_name = tf.value
                for piano_key, val in config_overrides.items():
                    if piano_key.startswith(f"limit_{tf_name}_"):
                        ppart = piano_key.split("_")[-1]
                        if ppart.startswith("P"):
                            piano = int(ppart[1:])
                        elif ppart == "J":
                            piano = 'jolly'
                        else:
                            continue
                        turnazione.limiti_piani_fascia[tf][piano] = val
                turnazione.limiti_fascia[tf] = sum(v for k, v in turnazione.limiti_piani_fascia[tf].items())

        # Stampa configurazione
        print(f"\n  Configurazione per {test_label}:")
        for tf in [TipoFascia.MATTINA, TipoFascia.POMERIGGIO, TipoFascia.NOTTE]:
            slots = turnazione.limiti_piani_fascia.get(tf, {})
            total = turnazione.limiti_fascia.get(tf, 0)
            print(f"    {tf.value}: {dict(slots)} → totale {total}")

        gen = SistemaGenerazione(turnazione, sistema_dipendenti)
        for settimana in settimane:
            print(f"\n  [Generazione] Settimana {anno}-{settimana}")
            gen.genera_turnazione_automatica(anno, settimana, genera_piani=True)

        ok = summarize_result(test_label, sistema_dipendenti, turnazione, anno, settimane)
        return ok

    except Exception as e:
        print(f"\n  ERRORE: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        patcher.stop()


def run_baseline():
    """Test con limiti standard: Mattina=7, Pomeriggio=6, Notte=1."""
    print("\n" + "=" * 60)
    print("  TEST 1/5 — Limiti STANDARD (baseline)")
    print("=" * 60)
    return run_generation("Standard (baseline)", 2026, [10, 11, 12])


def run_increased():
    """Test con limiti aumentati: Mattina=12, Pomeriggio=8, Notte=2."""
    print("\n" + "=" * 60)
    print("  TEST 2/5 — Limiti AUMENTATI")
    print("=" * 60)
    configs = {
        # Mattina: 4+4+3+1 = 12
        "limit_MATTINA_P0": 4,
        "limit_MATTINA_P1": 4,
        "limit_MATTINA_P2": 3,
        "limit_MATTINA_J": 1,
        # Pomeriggio: 2+3+2+1 = 8
        "limit_POMERIGGIO_P0": 2,
        "limit_POMERIGGIO_P1": 3,
        "limit_POMERIGGIO_P2": 2,
        "limit_POMERIGGIO_J": 1,
        # Notte: 1+1 = 2
        "limit_NOTTE_P0": 1,
        "limit_NOTTE_P1": 1,
        "limit_NOTTE_P2": 0,
        "limit_NOTTE_J": 0,
    }
    return run_generation("Limiti aumentati", 2026, [10, 11, 12], config_overrides=configs)


def run_stress():
    """Test con limiti estremi: Mattina=15, Pomeriggio=10, Notte=3 (al collasso con 21 dipendenti)."""
    print("\n" + "=" * 60)
    print("  TEST 3/3 — Limiti ESTREMI (stress)")
    print("=" * 60)
    configs = {
        "limit_MATTINA_P0": 5,
        "limit_MATTINA_P1": 5,
        "limit_MATTINA_P2": 3,
        "limit_MATTINA_J": 2,
        "limit_POMERIGGIO_P0": 3,
        "limit_POMERIGGIO_P1": 3,
        "limit_POMERIGGIO_P2": 2,
        "limit_POMERIGGIO_J": 2,
        "limit_NOTTE_P0": 1,
        "limit_NOTTE_P1": 1,
        "limit_NOTTE_P2": 1,
        "limit_NOTTE_J": 0,
    }
    return run_generation("Limiti estremi", 2026, [10, 11], config_overrides=configs)


def run_moderate():
    """Test con limiti moderatamente aumentati: Mattina=9, Pomeriggio=7, Notte=1."""
    print("\n" + "=" * 60)
    print("  TEST 4/5 — Limiti MODERATI (crescita controllata)")
    print("=" * 60)
    configs = {
        "limit_MATTINA_P0": 3, "limit_MATTINA_P1": 3, "limit_MATTINA_P2": 2, "limit_MATTINA_J": 1,
        "limit_POMERIGGIO_P0": 2, "limit_POMERIGGIO_P1": 2, "limit_POMERIGGIO_P2": 2, "limit_POMERIGGIO_J": 1,
        "limit_NOTTE_P0": 1, "limit_NOTTE_P1": 0, "limit_NOTTE_P2": 0, "limit_NOTTE_J": 0,
    }
    return run_generation("Limiti moderati", 2026, [10, 11, 12], config_overrides=configs)


def run_8_6_2():
    """Test: Mattina=8, Pomeriggio=6, Notte=2."""
    print("\n" + "=" * 60)
    print("  TEST — 8 Mattina / 6 Pomeriggio / 2 Notte")
    print("=" * 60)
    configs = {
        "limit_MATTINA_P0": 3, "limit_MATTINA_P1": 3, "limit_MATTINA_P2": 1, "limit_MATTINA_J": 1,
        "limit_POMERIGGIO_P0": 2, "limit_POMERIGGIO_P1": 2, "limit_POMERIGGIO_P2": 1, "limit_POMERIGGIO_J": 1,
        "limit_NOTTE_P0": 1, "limit_NOTTE_P1": 1, "limit_NOTTE_P2": 0, "limit_NOTTE_J": 0,
    }
    return run_generation("8M/6P/2N", 2026, [10, 11, 12], config_overrides=configs)


def run_8_6_1():
    """Test: Mattina=8, Pomeriggio=6, Notte=1."""
    print("\n" + "=" * 60)
    print("  TEST — 8 Mattina / 6 Pomeriggio / 1 Notte")
    print("=" * 60)
    configs = {
        "limit_MATTINA_P0": 3, "limit_MATTINA_P1": 3, "limit_MATTINA_P2": 1, "limit_MATTINA_J": 1,
        "limit_POMERIGGIO_P0": 2, "limit_POMERIGGIO_P1": 2, "limit_POMERIGGIO_P2": 1, "limit_POMERIGGIO_J": 1,
        "limit_NOTTE_P0": 1, "limit_NOTTE_P1": 0, "limit_NOTTE_P2": 0, "limit_NOTTE_J": 0,
    }
    return run_generation("8M/6P/1N", 2026, [10, 11, 12], config_overrides=configs)


def run_more_nights():
    """Test con 2 notti/giorno — verifica se 21 dipendenti reggono 2 notti per sera."""
    print("\n" + "=" * 60)
    print("  TEST 5/5 — 2 NOTTI/giorno (stesso vincolo 1/settimana)")
    print("=" * 60)
    configs = {
        "limit_MATTINA_P0": 3, "limit_MATTINA_P1": 3, "limit_MATTINA_P2": 1, "limit_MATTINA_J": 0,
        "limit_POMERIGGIO_P0": 2, "limit_POMERIGGIO_P1": 2, "limit_POMERIGGIO_P2": 1, "limit_POMERIGGIO_J": 1,
        "limit_NOTTE_P0": 1, "limit_NOTTE_P1": 1, "limit_NOTTE_P2": 0, "limit_NOTTE_J": 0,
    }
    return run_generation("2 notti/giorno", 2026, [10], config_overrides=configs)


def main():
    parser = argparse.ArgumentParser(description="Test generazione turnazione (senza GUI)")
    parser.add_argument("--seed", action="store_true", help="Genere partito solo il seed SQL")
    parser.add_argument("--baseline", action="store_true", help="Solo scenario baseline")
    parser.add_argument("--stress", action="store_true", help="Solo scenario stress")
    parser.add_argument("--keep", action="store_true", help="Mantiene il DB di test")
    parser.add_argument("--custom", action="store_true", help="Test personalizzati (8M/6P/2N e 8M/6P/1N)")
    args = parser.parse_args()

    setup_test_db()

    try:
        if args.seed:
            return

        results = []
        run_all = not (args.baseline or args.stress or args.custom)

        if args.baseline or run_all:
            results.append(("Standard", run_baseline()))

        if run_all:
            results.append(("Aumentati", run_increased()))
            results.append(("Moderati", run_moderate()))

        if args.custom:
            results.append(("8M/6P/2N", run_8_6_2()))
            results.append(("8M/6P/1N", run_8_6_1()))

        if args.stress or run_all:
            results.append(("Estremi", run_stress()))
            results.append(("2Notti", run_more_nights()))

        # ── Riepilogo ──
        print("\n" + "=" * 60)
        print("  RIEPILOGO TEST")
        print("=" * 60)
        for label, ok in results:
            status = "✓ PASS" if ok else "✗ FAIL"
            print(f"  {status} {label}")
        print()

    finally:
        if not args.keep:
            cleanup_test_db()
        else:
            print(f"\n[INFO] DB di test conservato: {TEST_DB}")


if __name__ == "__main__":
    main()
-- TABELLA DIPENDENTE --
CREATE TABLE IF NOT EXISTS dipendente (
    idDipendente SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    cognome TEXT NOT NULL,
    ferieRimanenti REAL NOT NULL,
    rolRimanenti REAL NOT NULL,
    stato VARCHAR(20) CHECK(stato IN ('ASSUNTO', 'LICENZIATO')) NOT NULL DEFAULT 'ASSUNTO'
);

-- TABERLLA VARIAZIONE BANCA ORE
CREATE TABLE IF NOT EXISTS variazioneBancaOre (
    key VARCHAR(50) NOT NULL,
    idDipendente INTEGER NOT NULL,
    valore REAL NOT NULL,
    descrizione TEXT,
    PRIMARY KEY (key, idDipendente),
    FOREIGN KEY (idDipendente) REFERENCES dipendente(idDipendente)
);

-- TABELLA TURNO --
CREATE TABLE IF NOT EXISTS turno (
    idTurno SERIAL PRIMARY KEY,
    dataTurno DATE NOT NULL,
    fasciaOraria VARCHAR(20) CHECK(fasciaOraria IN ('MATTINA', 'POMERIGGIO', 'NOTTE', 'RIPOSO')) NOT NULL,
    stato VARCHAR(20) CHECK(stato IN ('GENERATO', 'MODIFICATO', 'APPROVATO', 'CREATO', 'VUOTA', 'GENERATA', 'APPROVATA')) NOT NULL,
    UNIQUE (dataTurno, fasciaOraria)
);

-- TABELLA LAVORA --
CREATE TABLE IF NOT EXISTS lavora (
    idDipendente INTEGER NOT NULL,
    idTurno INTEGER NOT NULL,
    piano INTEGER,
    jolly BOOLEAN NOT NULL DEFAULT FALSE,
    turnoBreve BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (idDipendente, idTurno),
    FOREIGN KEY (idDipendente) REFERENCES dipendente(idDipendente),
    FOREIGN KEY (idTurno) REFERENCES turno(idTurno) ON DELETE CASCADE
);

-- TABELLA ASSENZA --
CREATE TABLE IF NOT EXISTS assenza (
    idAssenza SERIAL PRIMARY KEY,
    idDipendente INTEGER NOT NULL,
    tipo VARCHAR(12) CHECK(tipo IN ('FERIE', 'ROL', 'CERTIFICATO')) NOT NULL,
    dataInizio TIMESTAMP NOT NULL,
    dataFine TIMESTAMP NOT NULL,
    CHECK (dataFine >= dataInizio),
    FOREIGN KEY (idDipendente) REFERENCES dipendente(idDipendente)
);

-- TABELLA CONFIGURAZIONE --
CREATE TABLE IF NOT EXISTS configurazione (
    chiave TEXT PRIMARY KEY,
    valore TEXT NOT NULL
);

-- FUNZIONE E TRIGGER PER CONTROLLO LICENZIAMENTO --
CREATE OR REPLACE FUNCTION check_dipendente_attivo_func()
RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT stato FROM dipendente WHERE idDipendente = NEW.idDipendente) = 'LICENZIATO' THEN
        RAISE EXCEPTION 'Non è possibile assegnare turni o assenze a un dipendente licenziato.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS prevent_lavora_licenziato ON lavora;
CREATE TRIGGER prevent_lavora_licenziato
BEFORE INSERT ON lavora
FOR EACH ROW EXECUTE FUNCTION check_dipendente_attivo_func();

DROP TRIGGER IF EXISTS prevent_assenza_licenziato ON assenza;
CREATE TRIGGER prevent_assenza_licenziato
BEFORE INSERT ON assenza
FOR EACH ROW EXECUTE FUNCTION check_dipendente_attivo_func();

-- FUNZIONE E TRIGGER PER CONTROLLO SOVRAPPOSIZIONE ASSENZA --
CREATE OR REPLACE FUNCTION check_assenza_before_insert_func()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM assenza a
        JOIN turno t ON t.idTurno = NEW.idTurno
        WHERE a.idDipendente = NEW.idDipendente
        AND t.dataTurno BETWEEN a.dataInizio::date AND a.dataFine::date
    ) THEN
        RAISE EXCEPTION 'Errore: Il dipendente è in ferie/malattia in questa data.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS check_assenza_before_insert ON lavora;
CREATE TRIGGER check_assenza_before_insert
BEFORE INSERT ON lavora
FOR EACH ROW EXECUTE FUNCTION check_assenza_before_insert_func();
-- TABELLA DIPENDENTE --
CREATE TABLE IF NOT EXISTS dipendente (
    idDipendente INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cognome TEXT NOT NULL,
    ferieRimanenti REAL NOT NULL,
    rolRimanenti REAL NOT NULL,
    stato VARCHAR(11) CHECK(stato IN ('ASSUNTO', 'LICENZIATO')) NOT NULL DEFAULT 'ASSUNTO'
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
    idTurno INTEGER PRIMARY KEY AUTOINCREMENT,
    dataTurno DATE NOT NULL,
    fasciaOraria VARCHAR(9) CHECK(fasciaOraria IN ('MATTINA', 'POMERIGGIO', 'NOTTE', 'RIPOSO')) NOT NULL,
    stato VARCHAR(9) CHECK(stato IN ('GENERATO', 'MODIFICATO', 'APPROVATO', 'CREATO', 'VUOTA')) NOT NULL,
    UNIQUE (dataTurno, fasciaOraria)
);

-- TABELLA LAVORA --
CREATE TABLE IF NOT EXISTS lavora (
    idDipendente INTEGER NOT NULL,
    idTurno INTEGER NOT NULL,
    piano INTEGER,
    jolly INTEGER CHECK(jolly IN (0, 1)) NOT NULL,
    turnoBreve INTEGER CHECK(turnoBreve IN (0, 1)) NOT NULL,
    PRIMARY KEY (idDipendente, idTurno),
    FOREIGN KEY (idDipendente) REFERENCES dipendente(idDipendente),
    FOREIGN KEY (idTurno) REFERENCES turno(idTurno) ON DELETE CASCADE
);

-- TABELLA ASSENZA --
CREATE TABLE IF NOT EXISTS assenza (
    idAssenza INTEGER PRIMARY KEY AUTOINCREMENT,
    idDipendente INTEGER NOT NULL,
    tipo VARCHAR(12) CHECK(tipo IN ('FERIE', 'ROL', 'CERTIFICATO')) NOT NULL,
    dataInizio DATETIME NOT NULL,
    dataFine DATETIME NOT NULL,
    CHECK (dataFine >= dataInizio),
    FOREIGN KEY (idDipendente) REFERENCES dipendente(idDipendente)
);

-- TABELLA CONFIGURAZIONE --
CREATE TABLE IF NOT EXISTS configurazione (
    chiave TEXT PRIMARY KEY,
    valore TEXT NOT NULL
);

-- TRIGGER CONTROLLO LICENZIAMENTO SU TURNI --
CREATE TRIGGER IF NOT EXISTS prevent_lavora_licenziato
BEFORE INSERT ON lavora
FOR EACH ROW
WHEN (SELECT stato FROM dipendente WHERE idDipendente = NEW.idDipendente) = 'LICENZIATO'
BEGIN
    SELECT RAISE(ABORT, 'Non è possibile assegnare turni a un dipendente licenziato.');
END;

-- TRIGGER CONTROLLO LICENZIAMENTO SU ASSENZE --
CREATE TRIGGER IF NOT EXISTS prevent_assenza_licenziato
BEFORE INSERT ON assenza
FOR EACH ROW
WHEN (SELECT stato FROM dipendente WHERE idDipendente = NEW.idDipendente) = 'LICENZIATO'
BEGIN
    SELECT RAISE(ABORT, 'Non è possibile aggiungere assenze a un dipendente licenziato.');
END;


-- Trigger per impedire assegnazione se il dipendente è assente
CREATE TRIGGER IF NOT EXISTS check_assenza_before_insert
BEFORE INSERT ON lavora
BEGIN
    SELECT CASE
        WHEN EXISTS (
            SELECT 1
            FROM assenza a
            JOIN turno t ON t.idTurno = NEW.idTurno
            WHERE a.idDipendente = NEW.idDipendente
            -- Controlliamo se la data del turno cade nel range dell'assenza.
            -- Usiamo date() per estrarre solo la parte YYYY-MM-DD dalle stringhe datetime
            AND t.dataTurno BETWEEN date(a.dataInizio) AND date(a.dataFine)
        )
        THEN RAISE(ABORT, 'Errore: Il dipendente è in ferie/malattia in questa data.')
    END;
END;
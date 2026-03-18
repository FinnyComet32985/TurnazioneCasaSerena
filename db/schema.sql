-- TABELLA DIPENDENTE --
CREATE TABLE IF NOT EXISTS dipendente (
    idDipendente INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cognome TEXT NOT NULL,
    ferieRimanenti REAL NOT NULL,
    rolRimanenti REAL NOT NULL,
    stato VARCHAR(11) CHECK(stato IN ('ASSUNTO', 'LICENZIATO')) NOT NULL DEFAULT 'ASSUNTO'
);

-- TABELLA TURNO --
CREATE TABLE IF NOT EXISTS turno (
    idTurno INTEGER PRIMARY KEY AUTOINCREMENT,
    dataTurno DATE NOT NULL,
    fasciaOraria VARCHAR(9) CHECK(fasciaOraria IN ('MATTINA', 'POMERIGGIO', 'NOTTE', 'RIPOSO')) NOT NULL,
    stato VARCHAR(9) CHECK(stato IN ('GENERATO', 'MODIFICATO', 'APPROVATO', 'CREATO')) NOT NULL
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
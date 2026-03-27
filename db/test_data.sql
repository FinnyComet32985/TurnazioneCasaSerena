-- Reset delle tabelle (opzionale, utile per pulire l'ambiente di test)
DELETE FROM lavora;
DELETE FROM variazioneBancaOre;
DELETE FROM assenza;
DELETE FROM turno;
DELETE FROM dipendente;
DELETE FROM configurazione;

-- Inserimento di 21 dipendenti con saldi ferie e ROL realistici
INSERT INTO dipendente (idDipendente, nome, cognome, ferieRimanenti, rolRimanenti, stato) VALUES
(1, 'Mario', 'Rossi', 22.5, 15.0, 'ASSUNTO'),
(2, 'Laura', 'Verdi', 18.0, 8.5, 'ASSUNTO'),
(3, 'Giovanni', 'Bianchi', 12.0, 4.0, 'ASSUNTO'),
(4, 'Elena', 'Neri', 25.0, 20.0, 'ASSUNTO'),
(5, 'Marco', 'Gialli', 10.5, 6.0, 'ASSUNTO'),
(6, 'Francesca', 'Viola', 15.0, 12.0, 'ASSUNTO'),
(7, 'Roberto', 'Bruno', 20.0, 10.0, 'ASSUNTO'),
(8, 'Silvia', 'Rosa', 24.5, 18.0, 'ASSUNTO'),
(9, 'Andrea', 'Costa', 8.0, 2.5, 'ASSUNTO'),
(10, 'Paola', 'Lungo', 19.0, 14.0, 'ASSUNTO'),
(11, 'Luca', 'Corti', 21.0, 16.5, 'ASSUNTO'),
(12, 'Marta', 'Fontana', 14.5, 9.0, 'ASSUNTO'),
(13, 'Stefano', 'Riva', 23.0, 11.5, 'ASSUNTO'),
(14, 'Chiara', 'Serra', 17.5, 7.0, 'ASSUNTO'),
(15, 'Fabio', 'Galli', 11.0, 5.5, 'ASSUNTO'),
(16, 'Giulia', 'Ponti', 26.0, 22.0, 'ASSUNTO'),
(17, 'Davide', 'Fabbri', 13.0, 10.5, 'ASSUNTO'),
(18, 'Sara', 'Marchetti', 20.5, 13.0, 'ASSUNTO'),
(19, 'Matteo', 'Rinaldi', 16.0, 8.0, 'ASSUNTO'),
(20, 'Valentina', 'Esposito', 22.0, 19.5, 'ASSUNTO'),
(21, 'Nicola', 'Romano', 15.5, 11.0, 'ASSUNTO');

-- Simulazione di assenze distribuite nel mese di Febbraio e Marzo 2025
INSERT INTO assenza (idDipendente, tipo, dataInizio, dataFine) VALUES
-- Mario: Una settimana di ferie a metà Febbraio
(1, 'FERIE', '2025-02-10 00:00:00', '2025-02-14 23:59:59'),
-- Laura: Certificato medico di 3 giorni
(2, 'CERTIFICATO', '2025-02-17 00:00:00', '2025-02-19 23:59:59'),
-- Giovanni: Qualche ora di ROL nel pomeriggio
(3, 'ROL', '2025-02-24 14:00:00', '2025-02-24 18:00:00'),
-- Marco: Ferie la prima settimana di Marzo
(5, 'FERIE', '2025-03-03 00:00:00', '2025-03-07 23:59:59'),
-- Silvia: Certificato a fine Febbraio
(8, 'CERTIFICATO', '2025-02-20 00:00:00', '2025-02-22 23:59:59'),
-- Marta: Ferie l'ultima settimana di Febbraio
(12, 'FERIE', '2025-02-24 00:00:00', '2025-02-28 23:59:59'),
-- Fabio: ROL mattutino
(15, 'ROL', '2025-02-26 08:00:00', '2025-02-26 12:00:00'),
-- Valentina: Ferie programmate a metà Marzo
(20, 'FERIE', '2025-03-10 00:00:00', '2025-03-14 23:59:59');

-- Configurazione parametri di sistema standard
INSERT INTO configurazione (chiave, valore) VALUES
('max_jolly', '1'),
('max_piano', '3'),
('limit_MATTINA', '7'),
('limit_POMERIGGIO', '6'),
('limit_NOTTE', '1'),
('last_update', '2025-02-01');

-- Aggiunta di alcune variazioni banca ore manuali per simulare lo storico
INSERT INTO variazioneBancaOre (key, idDipendente, valore, descrizione) VALUES
('DIR_INIT_001', 1, 4.5, 'Straordinari arretrati Gennaio'),
('DIR_INIT_002', 3, -2.0, 'Recupero ore per permesso privato'),
('DIR_INIT_003', 9, 10.0, 'Premio produzione concordato');

-- Test stress data: 21 dipendenti + assenze + configurazione standard con limiti granulari
-- Eseguido su un DB appena creato (dopo init_db) pertere dati di test puliti.
-- Le assenze sono posizionate su settimane di marzo 2026 per non influenzare le prime settimane.

DELETE FROM lavora;
DELETE FROM variazioneBancaOre;
DELETE FROM assenza;
DELETE FROM turno;
DELETE FROM dipendente;
DELETE FROM configurazione;

-- 21 dipendenti ASSUNTO con ferie e ROL vari
INSERT INTO dipendente (idDipendente, nome, cognome, ferieRimanenti, rolRimanenti, stato) VALUES
(1,  'Mario',      'Rossi',       22.5, 15.0, 'ASSUNTO'),
(2,  'Laura',      'Verdi',       18.0,  8.5, 'ASSUNTO'),
(3,  'Giovanni',   'Bianchi',     12.0,  4.0, 'ASSUNTO'),
(4,  'Elena',      'Neri',        25.0, 20.0, 'ASSUNTO'),
(5,  'Marco',      'Gialli',      10.5,  6.0, 'ASSUNTO'),
(6,  'Francesca',  'Viola',       15.0, 12.0, 'ASSUNTO'),
(7,  'Roberto',    'Bruno',       20.0, 10.0, 'ASSUNTO'),
(8,  'Silvia',     'Rosa',        24.5, 18.0, 'ASSUNTO'),
(9,  'Andrea',     'Costa',        8.0,  2.5, 'ASSUNTO'),
(10, 'Paola',      'Lungo',       19.0, 14.0, 'ASSUNTO'),
(11, 'Luca',       'Corti',       21.0, 16.5, 'ASSUNTO'),
(12, 'Marta',      'Fontana',     14.5,  9.0, 'ASSUNTO'),
(13, 'Stefano',    'Riva',        23.0, 11.5, 'ASSUNTO'),
(14, 'Chiara',     'Serra',       17.5,  7.0, 'ASSUNTO'),
(15, 'Fabio',      'Galli',       11.0,  5.5, 'ASSUNTO'),
(16, 'Giulia',     'Ponti',       26.0, 22.0, 'ASSUNTO'),
(17, 'Davide',     'Fabbri',      13.0, 10.5, 'ASSUNTO'),
(18, 'Sara',       'Marchetti',   20.5, 13.0, 'ASSUNTO'),
(19, 'Matteo',     'Rinaldi',     16.0,  8.0, 'ASSUNTO'),
(20, 'Valentina',  'Esposito',    22.0, 19.5, 'ASSUNTO'),
(21, 'Nicola',     'Romano',      15.5, 11.0, 'ASSUNTO');

-- Assenze sparse in settimane specifiche (per testare che il generatore le rispetti)
-- Mario: ferie settimana 11 (2026-03-16 a 2026-03-20)
INSERT INTO assenza (idDipendente, tipo, dataInizio, dataFine) VALUES
(1,  'FERIE',       '2026-03-16 00:00:00', '2026-03-20 23:59:59'),
-- Laura: certificato in settimana 10 (2026-03-13 a 2026-03-15)
(2,  'CERTIFICATO', '2026-03-13 00:00:00', '2026-03-15 23:59:59'),
-- Marco: ferie settimana 12 (2026-03-23 a 2026-03-27)
(5,  'FERIE',       '2026-03-23 00:00:00', '2026-03-27 23:59:59'),
-- Marta: ROL breve in settimana 11
(12, 'ROL',         '2026-03-18 14:00:00', '2026-03-18 18:00:00'),
-- Valentina: ferie settimana 13 (2026-03-30 a 2026-04-03)
(20, 'FERIE',       '2026-03-30 00:00:00', '2026-04-03 23:59:59');

-- Configurazione standard (limiti granulari per piano e fascia)
-- Defaults: Mattina=3+3+1+0jolly=7, Pomeriggio=2+2+1+1jolly=6, Notte=1+0+0+0jolly=1
INSERT INTO configurazione (chiave, valore) VALUES
('max_jolly', '1'),
('max_piano', '3'),
('limit_MATTINA_P0', '3'),
('limit_MATTINA_P1', '3'),
('limit_MATTINA_P2', '1'),
('limit_MATTINA_J', '0'),
('limit_POMERIGGIO_P0', '2'),
('limit_POMERIGGIO_P1', '2'),
('limit_POMERIGGIO_P2', '1'),
('limit_POMERIGGIO_J', '1'),
('limit_NOTTE_P0', '1'),
('limit_NOTTE_P1', '0'),
('limit_NOTTE_P2', '0'),
('limit_NOTTE_J', '0'),
('last_update', '2026-03-01');

-- Variazioni banca ore per simulare storico
INSERT INTO variazioneBancaOre (key, idDipendente, valore, descrizione) VALUES
('DIR_INIT_001', 1,  4.5, 'Straordinari arretrati'),
('DIR_INIT_002', 3, -2.0, 'Recupero ore permesso'),
('DIR_INIT_003', 9, 10.0, 'Premio produzione');
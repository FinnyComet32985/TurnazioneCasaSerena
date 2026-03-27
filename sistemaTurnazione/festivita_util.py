from datetime import date, timedelta

def calcola_pasqua(anno):
    """Algoritmo di Meeus/Jones/Butcher per il calcolo della Pasqua."""
    a = anno % 19
    b = anno // 100
    c = anno % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    L = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * L) // 451
    mese = (h + L - 7 * m + 114) // 31
    giorno = ((h + L - 7 * m + 114) % 31) + 1
    return date(anno, mese, giorno)

def get_festivita_italiane(anno):
    """Ritorna un set di date festive (rosse) per l'anno specificato."""
    pasqua = calcola_pasqua(anno)
    pasquetta = pasqua + timedelta(days=1)
    
    return {
        date(anno, 1, 1), date(anno, 1, 6), pasqua, pasquetta,
        date(anno, 4, 25), date(anno, 5, 1), date(anno, 6, 2),
        date(anno, 8, 15), date(anno, 11, 1), date(anno, 12, 8),
        date(anno, 12, 25), date(anno, 12, 26)
    }

def get_vigilie(anno):
    """Ritorna le date delle vigilie per la rotazione (non rosse in calendario)."""
    return {date(anno, 12, 24), date(anno, 12, 31)}
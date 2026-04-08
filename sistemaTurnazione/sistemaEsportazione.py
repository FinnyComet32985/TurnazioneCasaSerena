import os
from datetime import datetime, timedelta, date
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase.pdfmetrics import stringWidth

from sistemaTurnazione.fasciaOraria import TipoFascia
from sistemaDipendenti.dipendente import StatoDipendente

def genera_pdf_settimanale(path, monday, sistema_dipendenti, turnazione, fasce_disponibili):
    """Genera un PDF in formato A4 verticale della turnazione settimanale."""
    
    # Configurazione documento (A4 Verticale) - Margini ottimizzati per singola pagina
    doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.2*cm, bottomMargin=1.2*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    # --- STILI PERSONALIZZATI ---
    style_h1 = ParagraphStyle('H1', parent=styles['Normal'], fontSize=14, leading=16, alignment=1, spaceAfter=1, fontName='Helvetica-Bold')
    style_h2 = ParagraphStyle('H2', parent=styles['Normal'], fontSize=11, leading=13, alignment=1, spaceAfter=5, fontName='Helvetica')
    style_info = ParagraphStyle('Info', parent=styles['Normal'], fontSize=8.5, leading=10, spaceAfter=2)
    
    # --- INTESTAZIONE ---
    elements.append(Paragraph("ASSOCIAZIONE \"CASA SERENA\"", style_h1))
    elements.append(Paragraph("MATINO", style_h2))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=10))
    
    elements.append(Paragraph("<b>TURNI OSS</b>", style_h1))
    
    # Calcolo Mesi e Anno
    sunday = monday + timedelta(days=6)
    mesi_ita = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO", "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
    m1 = mesi_ita[monday.month - 1]
    m2 = mesi_ita[sunday.month - 1]
    testo_mese = f"{m1} {monday.year}" if m1 == m2 else f"{m1} / {m2} {sunday.year}"
    
    elements.append(Paragraph(testo_mese, style_h2))
    elements.append(Paragraph(f"DAL {monday.strftime('%d/%m/%Y')} AL {sunday.strftime('%d/%m/%Y')}", style_h2))
    elements.append(Spacer(1, 5))
    
    # --- SEZIONE ASSENZE (DIPENDENTE ferie / rol / certificato DAL ... AL ...) ---
    dipendenti = sistema_dipendenti.get_lista_dipendenti()

    # Identifica i cognomi duplicati tra i dipendenti assunti per la gestione omonimi
    dipendenti_attivi = [d for d in dipendenti if d.stato == StatoDipendente.ASSUNTO]
    cognomi_list = [d.cognome for d in dipendenti_attivi]
    duplicati_cognomi = {c for c in cognomi_list if cognomi_list.count(c) > 1}

    week_start = date(monday.year, monday.month, monday.day)
    week_end = date(sunday.year, sunday.month, sunday.day)
    fmt_db = "%Y-%m-%d %H:%M:%S"
    
    found_assenza = False
    for dip in dipendenti:
        for ass in dip.assenze_programmate:
            try:
                dt_inizio = datetime.strptime(ass.data_inizio, fmt_db).date()
                dt_fine = datetime.strptime(ass.data_fine, fmt_db).date()
                
                # Se l'assenza interseca la settimana corrente
                if max(week_start, dt_inizio) <= min(week_end, dt_fine):
                    testo = f"• <b>{dip.nome.upper()} {dip.cognome.upper()}</b> {ass.tipo.lower()} DAL {dt_inizio.strftime('%d/%m')} AL {dt_fine.strftime('%d/%m')}"
                    elements.append(Paragraph(testo, style_info))
                    found_assenza = True
            except: continue
            
    if found_assenza:
        elements.append(Spacer(1, 8))

    # --- TABELLA TURNI ---
    anno, sett, _ = monday.isocalendar()
    settimana_dict = turnazione.get_turnazione_settimana((anno, sett))
    
    if not settimana_dict:
        elements.append(Paragraph("<i>Nessuna turnazione definita per questa settimana.</i>", style_info))
    else:
        # Header Tabella
        data = [["GIORNO", "MATTINA", "POMERIGGIO", "NOTTE", "RIPOSO"]]
        giorni_nomi = ["LUN", "MAR", "MER", "GIO", "VEN", "SAB", "DOM"]
        
        for i in range(7):
            dt = monday + timedelta(days=i)
            giorno_str = f"{giorni_nomi[i]} {dt.day}"
            row = [giorno_str]
            
            fasce_giorno = settimana_dict.get(dt, {})
            for tipo in fasce_disponibili:
                fascia = fasce_giorno.get(tipo)
                if fascia and fascia.assegnazioni:
                    nomi = []
                    for ass in fascia.assegnazioni:
                        tag = ""
                        if getattr(ass, 'piano', None) is not None: 
                            tag += f" {'PT' if ass.piano == 0 else f'P{ass.piano}'}"
                        if getattr(ass, 'jolly', False): tag += " J"
                        if getattr(ass, 'turnoBreve', False): tag += " C"
                        
                        # Mostra l'iniziale solo se il cognome non è unico
                        if ass.dipendente.cognome in duplicati_cognomi:
                            nome_display = f"{ass.dipendente.cognome} {ass.dipendente.nome[0]}."
                        else:
                            nome_display = ass.dipendente.cognome
                        
                        nomi.append(f"{nome_display}{tag}")
                    
                    # Organizzazione nomi: due per riga solo se non superano la larghezza cella
                    col_idx = fasce_disponibili.index(tipo) + 1
                    col_w_pts = [2.2*cm, 3.8*cm, 3.8*cm, 3.8*cm, 3.4*cm][col_idx]
                    limit_w = col_w_pts - 12 # Sottraiamo il padding interno (6pt per lato)
                    
                    nomi_wrapped = []
                    current_line = ""
                    count_in_line = 0
                    
                    for n in nomi:
                        if not current_line:
                            current_line = n
                            count_in_line = 1
                        else:
                            test_line = f"{current_line}  |  {n}"
                            # Se ci sono già 2 nomi o se il terzo non entrerebbe, andiamo a capo
                            if count_in_line < 2 and stringWidth(test_line, 'Helvetica-Bold', 11) < limit_w:
                                current_line = test_line
                                count_in_line += 1
                            else:
                                nomi_wrapped.append(current_line)
                                current_line = n
                                count_in_line = 1
                    if current_line:
                        nomi_wrapped.append(current_line)
                    row.append("\n".join(nomi_wrapped))
                else:
                    row.append("-")
            data.append(row)

        # Larghezza totale A4 (21cm) - Margini (4cm) = 17cm disponibili
        table = Table(data, colWidths=[2.2*cm, 3.8*cm, 3.8*cm, 3.8*cm, 3.4*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11), # Ingrandito a 11
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), 
            ('TOPPADDING', (0, 0), (-1, -1), 5), # Padding ridotto per far stare tutto in una pagina
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEADING', (0, 0), (-1, -1), 13), # Interlinea ottimizzata
        ]))
        
        elements.append(table)

    doc.build(elements)
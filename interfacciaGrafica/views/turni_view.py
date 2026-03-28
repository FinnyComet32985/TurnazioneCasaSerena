from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QFileDialog,
    QSpinBox, QHeaderView, QMessageBox, QComboBox, QDialog, QCheckBox,
    QFrame, QScrollArea, QSizePolicy, QAbstractItemView, QProgressBar, QCompleter, QMenu,
    QProgressDialog, QApplication
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QSize, QDate, QRect, pyqtSignal
from datetime import datetime, date, timedelta

# Import per accedere ai riferimenti
from sistemaTurnazione.fasciaOraria import TipoFascia, StatoFascia
from sistemaDipendenti.dipendente import StatoDipendente
from sistemaDipendenti.assenzaProgrammata import TipoAssenza

# Import del modulo di esportazione
from sistemaTurnazione.sistemaEsportazione import genera_pdf_settimanale
from sistemaTurnazione.festivita_util import get_festivita_italiane

class AssignTurnoDialog(QDialog):
    def __init__(self, dipendenti, dt_turno, tipo_fascia, parent=None, assegnazione_esistente=None):
        super().__init__(parent)
        self.assegnazione_esistente = assegnazione_esistente
        self.setWindowTitle(f"Assegna Turno - {dt_turno} ({tipo_fascia})" if not assegnazione_esistente else f"Modifica Turno - {dt_turno} ({tipo_fascia})")
        self.setFixedWidth(350)
        self.id_scelto = None
        self.piano_scelto = 0
        self.jolly_scelto = False
        self.corto_scelto = False
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Selezione Dipendente
        layout.addWidget(QLabel("<b>Seleziona il Dipendente:</b>"))
        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo.lineEdit().setPlaceholderText("Cerca dipendente...")
        
        # Stile per la combo ricercabile
        self.combo.setStyleSheet("""
            QComboBox { color: #0f172a; background-color: white; border: 1px solid #cbd5e1; padding: 6px; border-radius: 4px; }
            QComboBox QLineEdit { color: #0f172a; background: transparent; border: none; }
            QComboBox QAbstractItemView { color: #0f172a; background-color: white; selection-background-color: #f1f5f9; selection-color: #0f172a; outline: none; }
        """)
        
        # Configura il completatore per cercare all'interno del testo
        completer = self.combo.completer()
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        
        # Aggiungiamo un item vuoto all'inizio o usiamo currentIndex -1
        # L'approccio migliore con Editable è caricare tutto e forzare -1
        for dip in dipendenti:
            if dip.stato.name == "ASSUNTO":
                self.combo.addItem(f"{dip.nome} {dip.cognome}", userData=dip.id_dipendente)
        
        # Forza la combo ad essere vuota all'apertura
        self.combo.setCurrentIndex(-1)
        self.combo.lineEdit().setText("")
        layout.addWidget(self.combo)
        
        # Selezione Piano
        layout.addWidget(QLabel("<b>Piano di lavoro:</b>"))
        self.combo_piano = QComboBox()
        self.combo_piano.addItems(["Piano Terra", "Piano 1", "Piano 2"])
        self.combo_piano.setStyleSheet("color: #0f172a; background-color: white; border: 1px solid #cbd5e1; padding: 6px; border-radius: 4px;")
        layout.addWidget(self.combo_piano)
        
        # Opzioni aggiuntive
        opts_layout = QHBoxLayout()
        self.check_jolly = QCheckBox("Operatore Jolly")
        self.check_jolly.setStyleSheet("font-weight: 500;")
        
        self.check_corto = QCheckBox("Turno Corto")
        self.check_corto.setStyleSheet("font-weight: 500;")
        # Abilita "Corto" solo se è mattina
        if tipo_fascia != TipoFascia.MATTINA.value:
            self.check_corto.setEnabled(False)
            self.check_corto.setToolTip("Disponibile solo per il turno di Mattina")
            
        opts_layout.addWidget(self.check_jolly)
        opts_layout.addWidget(self.check_corto)
        
        # Pre-selezione se in modifica
        if self.assegnazione_esistente:
            index = self.combo.findData(self.assegnazione_esistente.dipendente.id_dipendente)
            if index >= 0:
                self.combo.setCurrentIndex(index)
                self.combo.setEnabled(False) # Non si cambia il dipendente in modifica
            
            p = getattr(self.assegnazione_esistente, 'piano', 0)
            if p is None: p = 0
            
            # Indici 0, 1, 2 per Piano Terra, 1, 2
            self.combo_piano.setCurrentIndex(p if 0 <= p <= 2 else 0)
            
            self.check_jolly.setChecked(getattr(self.assegnazione_esistente, 'jolly', False))
            self.check_corto.setChecked(getattr(self.assegnazione_esistente, 'turnoBreve', False))
            
            self.save_btn_text = "Salva Modifiche"
        else:
            self.save_btn_text = "Conferma Assegnazione"

        layout.addLayout(opts_layout)
        
        # Pulsanti
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton(self.save_btn_text)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("background-color: #2563eb; color: white; border-radius: 6px; padding: 8px; font-weight: bold;")
        
        btn_annulla = QPushButton("Annulla")
        btn_annulla.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_annulla.setStyleSheet("background-color: #f1f5f9; color: #475569; border-radius: 6px; padding: 8px;")
        
        self.save_btn.clicked.connect(self.accept)
        btn_annulla.clicked.connect(self.reject)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(btn_annulla)
        
        layout.addLayout(btn_layout)
        
    def accept(self):
        self.id_scelto = self.combo.currentData()
        self.piano_scelto = self.combo_piano.currentIndex()
        self.jolly_scelto = self.check_jolly.isChecked()
        self.corto_scelto = self.check_corto.isChecked()
        super().accept()

class WeekSelectorDialog(QDialog):
    def __init__(self, current_date, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleziona Settimana")
        self.setFixedWidth(320)
        self.selected_date = current_date
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Anno
        layout.addWidget(QLabel("Anno:"))
        self.combo_anno = QComboBox()
        current_year = current_date.year
        for y in range(current_year - 5, current_year + 6):
            self.combo_anno.addItem(str(y), y)
        self.combo_anno.setCurrentText(str(current_year))
        self.combo_anno.currentIndexChanged.connect(self.update_weeks)
        layout.addWidget(self.combo_anno)

        # Mese
        layout.addWidget(QLabel("Mese:"))
        self.combo_mese = QComboBox()
        mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
                "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        for i, m in enumerate(mesi):
            self.combo_mese.addItem(m, i + 1)
        self.combo_mese.setCurrentIndex(current_date.month - 1)
        self.combo_mese.currentIndexChanged.connect(self.update_weeks)
        layout.addWidget(self.combo_mese)

        # Settimana
        layout.addWidget(QLabel("Settimana:"))
        self.combo_settimana = QComboBox()
        layout.addWidget(self.combo_settimana)

        self.update_weeks() # Popola le settimane iniziali

        # Bottoni
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Seleziona")
        btn_ok.setStyleSheet("background-color: #3b82f6; color: white; padding: 8px; border-radius: 4px; font-weight: bold;")
        btn_ok.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        
        layout.addLayout(btn_layout)

    def update_weeks(self):
        year = self.combo_anno.currentData()
        month = self.combo_mese.currentData()
        
        self.combo_settimana.clear()
        
        # Calcola il primo giorno del mese
        first_day = date(year, month, 1)
        # Trova il lunedì della settimana che contiene il 1° del mese (o il lunedì precedente)
        current_monday = first_day - timedelta(days=first_day.weekday())
        
        # Aggiungi settimane finché il lunedì è ancora nel mese corrente (o appena fuori ma la settimana copre il mese)
        # Una logica semplice: mostriamo 6 settimane a partire dal primo lunedì trovato
        for _ in range(6):
            sunday = current_monday + timedelta(days=6)
            
            # Se la settimana è completamente fuori dal mese successivo, ci fermiamo
            if current_monday.month > month and current_monday.year == year:
                 break
            if current_monday.year > year:
                break
                
            label = f"{current_monday.strftime('%d %b')} - {sunday.strftime('%d %b')}"
            self.combo_settimana.addItem(label, current_monday)
            
            current_monday += timedelta(weeks=1)

    def accept(self):
        self.selected_date = self.combo_settimana.currentData()
        super().accept()

class DayWidget(QWidget):
    def __init__(self, dt, holidays, parent=None):
        super().__init__(parent)
        self.dt = dt
        self.holidays = holidays
        self.setAutoFillBackground(False) # Disabilita il riempimento automatico per disegnarlo noi

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 15, 0, 15) # Padding verticale per il contenuto
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        giorni_settimana = ["LUN", "MAR", "MER", "GIO", "VEN", "SAB", "DOM"]
        day_abbr = giorni_settimana[self.dt.weekday()]
        
        lbl_abbr = QLabel(day_abbr)
        lbl_abbr.setStyleSheet("font-weight: bold; color: #64748b; font-size: 11px; background: transparent;")
        lbl_abbr.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_num = QLabel(str(self.dt.day))
        lbl_num.setStyleSheet("font-weight: 800; color: #0f172a; font-size: 18px; background: transparent;")
        lbl_num.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(lbl_abbr)
        layout.addWidget(lbl_num)

        # Determina i colori una sola volta
        self.bg_color = QColor("white")
        if self.dt == date.today():
            self.bg_color = QColor("#eff6ff") # Blu chiarissimo
            lbl_num.setStyleSheet(lbl_num.styleSheet() + " color: #2563eb;")
        elif self.dt in self.holidays:
            self.bg_color = QColor("#fef2f2") # Rosso chiarissimo
        elif self.dt.weekday() >= 5: # Sabato o Domenica
            self.bg_color = QColor("#f8fafc") # Grigio chiarissimo

    def paintEvent(self, event):
        painter = QPainter(self)
        # Disegna lo sfondo sull'intero rettangolo del widget
        painter.fillRect(self.rect(), self.bg_color)
        
        # Disegna le linee della griglia (Destra e Sotto)
        painter.setPen(QColor("#e2e8f0"))
        painter.drawLine(self.rect().topRight(), self.rect().bottomRight())
        painter.drawLine(self.rect().bottomLeft(), self.rect().bottomRight())
        
        super().paintEvent(event) # Lascia che l'evento di base disegni i figli (le label)

class DipendentePill(QFrame):
    deleteRequested = pyqtSignal(int) # id_dipendente
    editRequested = pyqtSignal(object) # assegnazione
    highlightRequested = pyqtSignal(int) # id_dipendente

    def __init__(self, assegnazione, data_turno, interfaccia, is_highlighted=False, parent=None):
        super().__init__(parent)
        self.assegnazione = assegnazione
        self.is_highlighted = is_highlighted
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setFixedHeight(24)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        dipendente = assegnazione.dipendente

        # Identifica se esistono altri dipendenti assunti con lo stesso cognome
        dipendenti_attivi = [d for d in interfaccia.sistema_dipendenti.get_lista_dipendenti() if d.stato == StatoDipendente.ASSUNTO]
        cognomi_attivi = [d.cognome for d in dipendenti_attivi]
        if cognomi_attivi.count(dipendente.cognome) > 1:
             nome_display = f"{dipendente.cognome} {dipendente.nome[0]}."
        else:
             nome_display = dipendente.cognome

        nome_str = f"<b>{nome_display}</b>"
        
        # Indicatori: [P1] [J] [C]
        info_tags = []
        if getattr(assegnazione, 'piano', None) is not None:
            p_label = "PT" if assegnazione.piano == 0 else f"P{assegnazione.piano}"
            info_tags.append(f"<span style='color: #2563eb;'>{p_label}</span>")
        if getattr(assegnazione, 'jolly', False):
            info_tags.append("<span style='color: #7c3aed;'>J</span>")
        if getattr(assegnazione, 'turnoBreve', False):
            info_tags.append("<span style='color: #ea580c;'>C</span>")
            
        tags_str = " ".join(info_tags)
        final_text = f"{nome_str} {tags_str}" if info_tags else nome_str
        
        lbl = QLabel(final_text)
        lbl.setStyleSheet("font-size: 11px; color: #334155; background: transparent; border: none;")
        layout.addWidget(lbl)
        
        # Controllo se il dipendente è in assenza in questa data per colorare la pillola di rosso
        is_absent = interfaccia.sistema_dipendenti.verifica_assenza(dipendente.id_dipendente, data_turno)
        
        if is_absent:
            bg_pill, border_pill, bg_hover, border_hover = "#fee2e2", "#ef4444", "#fecaca", "#dc2626"
            border_width = "1px"
        elif is_highlighted:
            # Blu acceso per l'evidenziazione
            bg_pill, border_pill, bg_hover, border_hover = "#eff6ff", "#3b82f6", "#dbeafe", "#2563eb"
            border_width = "2px"
        else:
            bg_pill, border_pill, bg_hover, border_hover = "white", "#cbd5e1", "#f8fafc", "#94a3b8"
            border_width = "1px"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_pill};
                border: {border_width} solid {border_pill};
                border-radius: 6px;
            }}
            QFrame:hover {{
                border: 1px solid {border_hover};
                background-color: {bg_hover};
            }}
        """)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { 
                background-color: white; 
                border: 1px solid #cbd5e1; 
                border-radius: 6px; 
                padding: 4px;
            }
            QMenu::item { 
                padding: 6px 24px; 
                color: #334155; 
                border-radius: 4px;
                font-size: 11px;
            }
            QMenu::item:selected { 
                background-color: #f1f5f9; 
                color: #0f172a; 
            }
        """)
        
        highlight_text = "Rimuovi Evidenzia" if self.is_highlighted else "Evidenzia Turni"
        highlight_icon = "./interfacciaGrafica/assets/eye-off.svg" if self.is_highlighted else "./interfacciaGrafica/assets/eye.svg"
        highlight_action = menu.addAction(highlight_text)
        highlight_action.setIcon(self.get_colored_icon(highlight_icon, "#3b82f6"))
        
        edit_action = menu.addAction("Modifica")
        edit_action.setIcon(self.get_colored_icon("./interfacciaGrafica/assets/pencil.svg", "#000000"))
        
        delete_action = menu.addAction("Elimina")
        delete_action.setIcon(self.get_colored_icon("./interfacciaGrafica/assets/trash-bin.svg", "#dc2626"))
        
        action = menu.exec(self.mapToGlobal(pos))
        if action == edit_action:
            self.editRequested.emit(self.assegnazione)
        elif action == highlight_action:
            self.highlightRequested.emit(self.assegnazione.dipendente.id_dipendente)
        elif action == delete_action:
            self.deleteRequested.emit(self.assegnazione.dipendente.id_dipendente)

    def get_colored_icon(self, icon_path, color_hex):
        pixmap = QPixmap(icon_path)
        if pixmap.isNull(): return QIcon()
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(color_hex))
        painter.end()
        icon = QIcon(pixmap)
        # Forza la stessa pixmap anche per lo stato disabilitato (evita il grigio di sistema)
        icon.addPixmap(pixmap, QIcon.Mode.Disabled, QIcon.State.Off)
        icon.addPixmap(pixmap, QIcon.Mode.Disabled, QIcon.State.On)
        return icon

class ShiftCellWidget(QWidget):
    clicked = pyqtSignal(int, int) # Segnale personalizzato per il click
    pillDeleteRequested = pyqtSignal(int, int, int) # row, col, id_dipendente
    pillEditRequested = pyqtSignal(int, int, object) # row, col, assegnazione
    pillHighlightRequested = pyqtSignal(int, int, int) # row, col, id_dipendente

    def __init__(self, row, col, stato, assegnazioni, data_turno, interfaccia, highlighted_id=None, parent=None):
        super().__init__(parent)
        self.row = row
        self.col = col
        self.data_turno = data_turno
        self.interfaccia = interfaccia
        
        # Layout a griglia (2 colonne) per i dipendenti
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(4)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        # Mapping colori stati (Migliorato per visibilità)
        colors = {
            StatoFascia.APPROVATA: ("#dcfce7", "#166534"), # Verde
            StatoFascia.MODIFICATA: ("#ffedd5", "#9a3412"), # Arancio
            StatoFascia.GENERATA: ("#f5f3ff", "#5b21b6"), # Viola (AI)
            StatoFascia.CREATO: ("#f0f9ff", "#075985"), # Blu (Auto)
            StatoFascia.VUOTA: ("#ffffff", "#94a3b8")
        }
        
        bg, fg = colors.get(stato, ("white", "#334155"))
        self.bg_color = QColor(bg)
        
        # Se non ci sono assegnazioni, la cella deve essere bianca (non colorata)
        if not assegnazioni:
            self.bg_color = QColor("white")
            # Usa colore neutro per il testo di aggiunta
            fg_empty = "#94a3b8" 
            lbl = QLabel("+ Aggiungi")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color: {fg_empty}; font-size: 11px; font-weight: 500; background: transparent; border: none;")
            self.layout.addWidget(lbl, 0, 0)
        else:
            # Aggiunge le pillole in una griglia
            for i, ass in enumerate(assegnazioni):
                r = i // 3 # 3 colonne
                c = i % 3
                is_highlighted = (highlighted_id == ass.dipendente.id_dipendente)
                pill = DipendentePill(ass, self.data_turno, self.interfaccia, is_highlighted=is_highlighted)
                self.layout.addWidget(pill, r, c)
                pill.deleteRequested.connect(lambda id_dipendente: self.pillDeleteRequested.emit(self.row, self.col, id_dipendente))
                pill.editRequested.connect(lambda assegnazione: self.pillEditRequested.emit(self.row, self.col, assegnazione))
                pill.highlightRequested.connect(lambda id_dipendente: self.pillHighlightRequested.emit(self.row, self.col, id_dipendente))
                
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.bg_color)
        
        # Bordi griglia
        painter.setPen(QColor("#e2e8f0"))
        painter.drawLine(self.rect().topRight(), self.rect().bottomRight())
        painter.drawLine(self.rect().bottomLeft(), self.rect().bottomRight())
        painter.end()

    def mousePressEvent(self, event):
        # Emette clicked solo se il click è ESATTAMENTE sul widget e non su un figlio (pillola)
        # e solo se è il tasto sinistro
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.pos())
            # Se child è None o è una label di testo "+ Aggiungi", allora è un click vuoto
            if child is None or isinstance(child, QLabel):
                self.clicked.emit(self.row, self.col)
        super().mousePressEvent(event)

class ShiftHeaderView(QHeaderView):
    def __init__(self, orientation, parent, fasce, orari):
        super().__init__(orientation, parent)
        self.fasce = fasce
        self.orari = orari
        self.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        
        # Sfondo Header (Grigetto chiaro per differenziare)
        painter.fillRect(rect, QColor("#f8fafc"))
        
        # Bordi (Sotto e Destra per separazione pulita)
        painter.setPen(QColor("#e2e8f0"))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        if logicalIndex < self.count() - 1: # Non disegna il bordo per l'ultima colonna
            painter.drawLine(rect.topRight(), rect.bottomRight())

        if logicalIndex == 0:
            # Colonna 0: "TURNO"
            painter.setPen(QColor("#64748b"))
            font = painter.font()
            font.setBold(True)
            font.setPointSize(9)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "TURNO")
            
        elif (logicalIndex - 1) < len(self.fasce):
            tipo_fascia = self.fasce[logicalIndex - 1]
            
            # --- DATI ---
            icon_map = {
                TipoFascia.MATTINA: ("sunny.svg", "#f59e0b"),
                TipoFascia.POMERIGGIO: ("partly-sunny.svg", "#ea580c"),
                TipoFascia.NOTTE: ("moon.svg", "#4f46e5"),
                TipoFascia.RIPOSO: ("home.svg", "#64748b")
            }
            
            icon_name, color_hex = icon_map.get(tipo_fascia, ("help-circle.svg", "#64748b"))
            
            orari_list = self.orari.get(tipo_fascia.value, [])
            orario_str = ""
            if orari_list and len(orari_list) == 2 and tipo_fascia != TipoFascia.RIPOSO:
                h_start, h_end = orari_list
                orario_str = f"{h_start:02d}:00 - {h_end:02d}:00"

            # --- DISEGNO ---
            # Calcolo Posizionamento Verticale (Centrato)
            # Altezza totale stimata: 24(icon) + 4(gap) + 16(title) + 2(gap) + 12(time) = ~58px
            content_height = 58
            start_y = rect.top() + (rect.height() - content_height) // 2
            
            # 1. Icona
            icon_size = 24
            pix = QPixmap(f"./interfacciaGrafica/assets/{icon_name}")
            if not pix.isNull():
                # Ricolora
                colored_pix = QPixmap(pix.size())
                colored_pix.fill(Qt.GlobalColor.transparent)
                p = QPainter(colored_pix)
                p.drawPixmap(0, 0, pix)
                p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                p.fillRect(pix.rect(), QColor(color_hex))
                p.end()
                
                # Scalata e centrata X
                scaled = colored_pix.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                icon_x = rect.left() + (rect.width() - icon_size) // 2
                painter.drawPixmap(icon_x, int(start_y), scaled)

            current_y = start_y + icon_size + 4
            
            # 2. Titolo
            painter.setPen(QColor("#334155"))
            f = painter.font()
            f.setBold(True)
            f.setPointSize(10)
            painter.setFont(f)
            title_rect = QRect(rect.left(), int(current_y), rect.width(), 20)
            painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop, tipo_fascia.value)
            
            current_y += 18
            
            # 3. Orario
            if orario_str:
                painter.setPen(QColor("#94a3b8"))
                f.setBold(False)
                f.setPointSize(8)
                painter.setFont(f)
                time_rect = QRect(rect.left(), int(current_y), rect.width(), 16)
                painter.drawText(time_rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop, orario_str)

        painter.restore()

class TurniView(QWidget):
    def __init__(self, interfaccia):
        super().__init__()
        self.interfaccia = interfaccia
        self.fasce_disponibili = [TipoFascia.MATTINA, TipoFascia.POMERIGGIO, TipoFascia.NOTTE, TipoFascia.RIPOSO]
        self.highlighted_dip_id = None # ID del dipendente da evidenziare
        
        # Inizializza alla data di oggi (lunedì della settimana corrente)
        today = date.today()
        self.current_monday = today - timedelta(days=today.weekday())
        self.holidays = set()
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)
        self.setMinimumWidth(1100)

        # Stile Scrollbar Moderno
        self.scrollbar_style = """
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none;
                background: #f1f5f9;
                width: 8px;
                border-radius: 4px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """
        
        # --- HEADER NAVIGATION ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        # Bottone Indietro
        btn_prev = QPushButton()
        btn_prev.setIcon(QIcon("./interfacciaGrafica/assets/arrow-back.svg"))
        btn_prev.setFixedSize(40, 40)
        btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_prev.setStyleSheet("QPushButton { border: 1px solid #cbd5e1; border-radius: 20px; background-color: white; } QPushButton:hover { background-color: #f1f5f9; }")
        btn_prev.clicked.connect(self.prev_week)
        
        # Label Centrale (Cliccabile)
        self.lbl_week_range = QPushButton("...")
        self.lbl_week_range.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lbl_week_range.setFixedHeight(40)
        self.lbl_week_range.setMinimumWidth(250)
        self.lbl_week_range.setStyleSheet("""
            QPushButton {
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                background-color: white;
                color: #0f172a;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #f8fafc; border-color: #94a3b8; }
        """)
        self.lbl_week_range.clicked.connect(self.open_week_selector)
        
        # Bottone Avanti
        btn_next = QPushButton()
        btn_next.setIcon(QIcon("./interfacciaGrafica/assets/arrow-forward.svg"))
        btn_next.setFixedSize(40, 40)
        btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_next.setStyleSheet("QPushButton { border: 1px solid #cbd5e1; border-radius: 20px; background-color: white; } QPushButton:hover { background-color: #f1f5f9; }")
        btn_next.clicked.connect(self.next_week)
        
        # Bottone Oggi
        self.btn_today = QPushButton(" Oggi")
        self.btn_today.setIcon(self.get_colored_icon("./interfacciaGrafica/assets/calendar-number.svg", "#3b82f6")) # Blu
        self.btn_today.setIconSize(QSize(20, 20))
        self.btn_today.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_today.setFixedHeight(40)
        self.btn_today.setFixedWidth(100)
        self.btn_today.clicked.connect(self.go_today)
        
        header_layout.addWidget(btn_prev)
        header_layout.addWidget(self.lbl_week_range)
        header_layout.addWidget(btn_next)
        header_layout.addSpacing(10)
        header_layout.addWidget(self.btn_today)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # --- ACTION BUTTONS (MOVED TO HEADER) ---
        action_btn_layout = QHBoxLayout()
        action_btn_layout.setSpacing(10)
        btn_style_header = """
            QPushButton {
                background-color: white; border: 1px solid #cbd5e1; border-radius: 6px;
                padding: 8px 16px; font-weight: bold; color: #334155; font-size: 13px;
            }
            QPushButton:hover { background-color: #f8fafc; border-color: #94a3b8; }
        """
        approve_style = """
            QPushButton {
                background-color: #f0fdf4; border: 1px solid #a7f3d0; border-radius: 6px;
                padding: 8px 16px; font-weight: bold; color: #166534; font-size: 13px;
            }
            QPushButton:hover { background-color: #dcfce7; border-color: #6ee7b7; }
        """
        genera_style = """
            QPushButton {
                background-color: #f5f3ff; border: 1px solid #ddd6fe; border-radius: 8px;
                padding: 8px 16px; font-weight: bold; color: #5b21b6; font-size: 13px;
            }
            QPushButton:hover { background-color: #ede9fe; }
        """
        # Stile Arancione per Riapri Settimana
        reopen_style = """
            QPushButton {
                background-color: #fff7ed; border: 1px solid #fdba74; border-radius: 6px;
                padding: 8px 16px; font-weight: bold; color: #c2410c; font-size: 13px;
            }
            QPushButton:hover { background-color: #ffedd5; border-color: #fb923c; }
        """
        svuota_style = """
            QPushButton {
                background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 6px;
                padding: 8px 16px; font-weight: bold; color: #991b1b; font-size: 13px;
            }
            QPushButton:hover { background-color: #fee2e2; border-color: #fca5a5; }
        """
        self.btn_genera = QPushButton(" Genera")
        self.btn_genera.setIcon(self.get_colored_icon("./interfacciaGrafica/assets/sparkles.svg", "#5b21b6"))
        self.btn_genera.setIconSize(QSize(20, 20))
        self.btn_genera.setStyleSheet(genera_style)
        
        self.btn_modifica = QPushButton(" Riapri Settimana")
        self.btn_modifica.setIcon(self.get_colored_icon("./interfacciaGrafica/assets/lock-open.svg", "#c2410c"))
        self.btn_modifica.setIconSize(QSize(20, 20))
        self.btn_modifica.setStyleSheet(reopen_style)
        
        self.btn_approva = QPushButton(" Approva")
        self.btn_approva.setIcon(self.get_colored_icon("./interfacciaGrafica/assets/checkbox.svg", "#166534"))
        self.btn_approva.setIconSize(QSize(20, 20))
        self.btn_svuota = QPushButton(" Svuota")
        self.btn_svuota.setIcon(self.get_colored_icon("./interfacciaGrafica/assets/trash-bin.svg", "#991b1b"))
        self.btn_svuota.setIconSize(QSize(20, 20))
        self.btn_pdf = QPushButton(" Esporta")
        self.btn_pdf.setIcon(self.get_colored_icon("./interfacciaGrafica/assets/document-attach.svg", "#334155"))
        self.btn_pdf.setIconSize(QSize(20, 20))
        
        self.btn_approva.setStyleSheet(approve_style)
        self.btn_svuota.setStyleSheet(svuota_style)
        self.btn_pdf.setStyleSheet(btn_style_header)

        self.btn_genera.clicked.connect(self.genera_turni_auto)
        self.btn_approva.clicked.connect(self.approva_settimana_ui)
        self.btn_modifica.clicked.connect(self.riapri_settimana_ui)
        self.btn_svuota.clicked.connect(self.svuota_settimana_ui)
        self.btn_pdf.clicked.connect(self.esporta_pdf)

        action_btn_layout.addWidget(self.btn_genera)
        action_btn_layout.addWidget(self.btn_modifica)
        action_btn_layout.addWidget(self.btn_approva)
        action_btn_layout.addWidget(self.btn_svuota)
        action_btn_layout.addWidget(self.btn_pdf)
        header_layout.addLayout(action_btn_layout)

        # --- DASHBOARD CARD ---
        dashboard_layout = QHBoxLayout()
        dashboard_layout.setSpacing(20)

        # Card 1: Copertura Turni (ex Personale Attivo)
        active_card = QFrame()
        active_card.setObjectName("active_card")
        active_card.setMinimumWidth(300)
        active_card.setStyleSheet("""
            #active_card {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
        """)
        active_layout = QVBoxLayout(active_card)
        active_layout.setContentsMargins(20, 20, 20, 20)
        
        # Contenuto Copertura
        top_row = QHBoxLayout()
        
        v_labels = QVBoxLayout()
        lbl_active_title = QLabel("COPERTURA TURNI")
        lbl_active_title.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold; letter-spacing: 0.5px;")
        
        self.lbl_coverage_perc = QLabel("0%")
        self.lbl_coverage_perc.setStyleSheet("color: #3b82f6; font-size: 32px; font-weight: 800;")
        
        v_labels.addWidget(lbl_active_title)
        v_labels.addWidget(self.lbl_coverage_perc)
        
        # Icona (Pie chart statica o simile, usiamo una variante colorata)
        icon_chart = QLabel()
        pix_p = QPixmap("./interfacciaGrafica/assets/pie-chart.svg") # Fallback o nuova icona
        # Se non hai pie-chart usa quella esistente o un placeholder, qui riuso una generica
        if pix_p.isNull():
             pix_p = QPixmap("./interfacciaGrafica/assets/options.svg") # Placeholder

        if not pix_p.isNull():
            painter = QPainter(pix_p)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pix_p.rect(), QColor("#3b82f6")) # Blu
            painter.end()
            icon_chart.setPixmap(pix_p.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        icon_chart.setStyleSheet("background-color: transparent; padding: 0px;")
        
        top_row.addLayout(v_labels)
        top_row.addStretch()
        top_row.addWidget(icon_chart)
        
        active_layout.addLayout(top_row)
        
        # Sottotitolo per dettagli (es. 45/50 turni)
        self.lbl_coverage_detail = QLabel("Calcolo in corso...")
        self.lbl_coverage_detail.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 500; margin-top: 5px;")
        active_layout.addWidget(self.lbl_coverage_detail)
        
        # --- Breakdown Copertura per Fascia ---
        active_layout.addSpacing(20)
        self.coverage_bars = {} # Dizionario per aggiornare le barre: {TipoFascia: (ProgressBar, Label)}
        
        fasce_colors = {
            TipoFascia.MATTINA: "#f59e0b",   # Amber (Sole)
            TipoFascia.POMERIGGIO: "#ea580c", # Orange (Tramonto)
            TipoFascia.NOTTE: "#4f46e5"      # Indigo (Luna)
        }
        
        for tipo in [TipoFascia.MATTINA, TipoFascia.POMERIGGIO, TipoFascia.NOTTE]:
            row = QHBoxLayout()
            row.setSpacing(10)
            
            lbl_fascia = QLabel(tipo.value.capitalize())
            lbl_fascia.setFixedWidth(75)
            lbl_fascia.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 600;")
            
            pbar = QProgressBar()
            pbar.setFixedHeight(8)
            pbar.setTextVisible(False)
            color = fasce_colors.get(tipo, "#cbd5e1")
            pbar.setStyleSheet(f"QProgressBar {{ border: none; background-color: #f1f5f9; border-radius: 4px; }} QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}")
            
            val_lbl = QLabel("0/0")
            val_lbl.setStyleSheet("color: #334155; font-size: 11px; font-weight: bold;")
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            val_lbl.setFixedWidth(40)
            
            row.addWidget(lbl_fascia)
            row.addWidget(pbar)
            row.addWidget(val_lbl)
            
            active_layout.addLayout(row)
            self.coverage_bars[tipo] = (pbar, val_lbl)
        
        active_layout.addStretch() 
        
        # Card 2: Assenze Correnti
        abs_card = QFrame()
        abs_card.setObjectName("abs_card")
        abs_card.setMinimumWidth(300)
        abs_card.setStyleSheet("""
            #abs_card {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
        """)
        abs_layout_card = QVBoxLayout(abs_card)
        abs_layout_card.setContentsMargins(20, 20, 20, 20)

        lbl_abs_title = QLabel("ASSENZE CORRENTI")
        lbl_abs_title.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold; letter-spacing: 0.5px;")
        abs_layout_card.addWidget(lbl_abs_title)
        
        # Header Colonne Assenze
        abs_header = QHBoxLayout()
        abs_header.setContentsMargins(0, 5, 0, 5)
        abs_header.addWidget(QLabel("DIPENDENTE"), stretch=2)
        # Allineamento centrale per il titolo TIPO per matchare le pillole
        abs_header.addWidget(QLabel("TIPO"), stretch=1, alignment=Qt.AlignmentFlag.AlignCenter)
        abs_header.addWidget(QLabel("PERIODO"), stretch=1, alignment=Qt.AlignmentFlag.AlignRight)
        # Applichiamo uno stile leggero per gli header
        for i in range(abs_header.count()): abs_header.itemAt(i).widget().setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
        abs_layout_card.addLayout(abs_header)

        # Lista scrollabile
        scroll_abs = QScrollArea()
        scroll_abs.setWidgetResizable(True)
        scroll_abs.setFixedHeight(120)
        scroll_abs.setStyleSheet(self.scrollbar_style)
        
        abs_content = QWidget()
        abs_content.setStyleSheet("background-color: transparent;")
        self.abs_layout = QVBoxLayout(abs_content)
        self.abs_layout.setContentsMargins(0, 5, 5, 0)
        self.abs_layout.setSpacing(8)
        self.abs_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_abs.setWidget(abs_content)
        abs_layout_card.addWidget(scroll_abs)
        
        # Card 3: Riepilogo Settimanale
        self.summary_card = self.create_summary_card()
        dashboard_layout.addWidget(active_card, stretch=1)
        dashboard_layout.addWidget(abs_card, stretch=1)
        dashboard_layout.addWidget(self.summary_card, stretch=1)
        
        layout.addLayout(dashboard_layout)
        
        # --- LEGENDA COLORI (Sotto le card, prima della tabella) ---
        legenda_layout = QHBoxLayout()
        legenda_layout.setContentsMargins(15, 0, 15, 0) # Margine maggiore per allinearsi alle card
        legenda_layout.setSpacing(15)
        
        def create_legend_item(color_hex, text):
            item = QWidget()
            it_layout = QHBoxLayout(item)
            it_layout.setContentsMargins(0, 0, 0, 0)
            it_layout.setSpacing(6)
            
            circle = QFrame()
            circle.setFixedSize(14, 14) # Un po' più grande per leggibilità
            circle.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #cbd5e1; border-radius: 7px;")
            
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 600;") # Font più chiaro
            
            it_layout.addWidget(circle)
            it_layout.addWidget(lbl)
            return item
            
        legenda_layout.addWidget(create_legend_item("#f5f3ff", "Generato (AI)"))
        legenda_layout.addWidget(create_legend_item("#f0f9ff", "Creato"))
        legenda_layout.addWidget(create_legend_item("#ffedd5", "Modificato (Manuale)"))
        legenda_layout.addWidget(create_legend_item("#dcfce7", "Approvato"))
        legenda_layout.addStretch()
        
        layout.addLayout(legenda_layout)
        layout.addSpacing(5) # Un po' di aria prima della tabella

        # --- TABELLA (O Empty State) ---
        self.body_container = QWidget()
        self.body_layout = QVBoxLayout(self.body_container)
        self.body_layout.setContentsMargins(0, 0, 0, 0) # No margine superiore
        
        self.table = QTableWidget()
        # +1 colonna per il widget del giorno
        self.table.setColumnCount(len(self.fasce_disponibili) + 1)
        
        # Header personalizzato
        self.header_view = ShiftHeaderView(Qt.Orientation.Horizontal, self.table, self.fasce_disponibili, self.interfaccia.turnazione.ORARIO_TURNI)
        self.header_view.setFixedHeight(80) # Altezza identica alle righe (80px) per uniformità
        self.table.setHorizontalHeader(self.header_view)

        self.table.verticalHeader().setVisible(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setShowGrid(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #e2e8f0;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
            QTableWidget::item {
                border-bottom: 1px solid #e2e8f0;
                border-right: 1px solid #e2e8f0;
                padding: 0px;
                color: #334155;
            }
        """)

        # Colonna 0 per i giorni
        self.table.setColumnWidth(0, 80)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        # Le altre colonne si espandono
        for i in range(1, self.table.columnCount()):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        self.table.cellClicked.connect(self.on_cell_clicked)
        
        # --- EMPTY STATE CONTAINER ---
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_label = QLabel("Nessun turno trovato per questa settimana.")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_genera = QPushButton(" Genera Turni (A.I.)")
        btn_genera.setIcon(self.get_colored_icon("./interfacciaGrafica/assets/sparkles.svg", "#ffffff"))
        btn_genera.setIconSize(QSize(20, 20))
        btn_crea_zero = QPushButton(" Crea da zero")
        btn_crea_zero.setIcon(self.get_colored_icon("./interfacciaGrafica/assets/document.svg", "#ffffff"))
        btn_crea_zero.setIconSize(QSize(20, 20))
        btn_genera.setFixedWidth(250)
        btn_crea_zero.setFixedWidth(250)
        
        btn_genera.setStyleSheet("padding: 10px; background-color: #6366f1; color: white; border-radius: 4px; font-weight: bold;")
        btn_crea_zero.setStyleSheet("padding: 10px; background-color: #10b981; color: white; border-radius: 4px; font-weight: bold;")
        
        btn_genera.clicked.connect(self.genera_turni_auto)
        btn_crea_zero.clicked.connect(self.crea_da_zero)
        
        btns_hlayout = QHBoxLayout()
        btns_hlayout.addStretch()
        btns_hlayout.addWidget(btn_genera)
        btns_hlayout.addWidget(btn_crea_zero)
        btns_hlayout.addStretch()
        
        empty_layout.addStretch()
        empty_layout.addWidget(empty_label)
        empty_layout.addSpacing(20)
        empty_layout.addLayout(btns_hlayout)
        empty_layout.addStretch()
        
        self.body_layout.addWidget(self.table)
        self.body_layout.addWidget(self.empty_widget)
        
        layout.addWidget(self.body_container, stretch=1)
        
        self.aggiorna_tabella()
        
    def showEvent(self, event):
        """Ricarica i dati ogni volta che la vista viene visualizzata."""
        super().showEvent(event)
        self.aggiorna_tabella()

    def vai_a_data(self, target_date: date):
        """Sposta la visualizzazione alla settimana della data specificata."""
        self.current_monday = target_date - timedelta(days=target_date.weekday())
        self.aggiorna_tabella()

    def prev_week(self):
        self.current_monday -= timedelta(weeks=1)
        self.aggiorna_tabella()

    def next_week(self):
        self.current_monday += timedelta(weeks=1)
        self.aggiorna_tabella()

    def go_today(self):
        today = date.today()
        self.current_monday = today - timedelta(days=today.weekday())
        self.aggiorna_tabella()

    def open_week_selector(self):
        dialog = WeekSelectorDialog(self.current_monday, self)
        if dialog.exec():
            self.current_monday = dialog.selected_date
            self.aggiorna_tabella()

    def update_header_ui(self):
        # Aggiorna label range
        sunday = self.current_monday + timedelta(days=6)
        # Formato: "15 Maggio - 21 Maggio 2025" o "29 Dic - 04 Gen 2026"
        mesi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
        
        m1 = mesi[self.current_monday.month - 1]
        m2 = mesi[sunday.month - 1]
        
        label_text = f"{self.current_monday.day} {m1} - {sunday.day} {m2} {sunday.year}"
        self.lbl_week_range.setText(label_text)

        # Aggiorna bottone Oggi
        today = date.today()
        this_monday = today - timedelta(days=today.weekday())
        if self.current_monday == this_monday:
             self.btn_today.setStyleSheet("background-color: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; font-weight: bold; border-radius: 8px;")
             self.btn_today.setIcon(self.get_colored_icon("./interfacciaGrafica/assets/calendar-number.svg", "#3b82f6")) # Blu acceso anche se disabilitato
             self.btn_today.setEnabled(False)
        else:
             self.btn_today.setStyleSheet("background-color: white; color: #0f172a; border: 1px solid #cbd5e1; font-weight: normal; border-radius: 8px;")
             self.btn_today.setIcon(self.get_colored_icon("./interfacciaGrafica/assets/calendar-number.svg", "#3b82f6"))
             self.btn_today.setEnabled(True)

        # Controllo stato approvazione per pulsanti
        anno, settimana, _ = self.current_monday.isocalendar()
        settimana_dict = self.interfaccia.turnazione.get_turnazione_settimana((anno, settimana))
        
        is_approved = False
        if settimana_dict:
            for g in settimana_dict.values():
                for f in g.values():
                    if f.stato == StatoFascia.APPROVATA:
                        is_approved = True
                        break
                if is_approved: break
        
        if is_approved:
            self.btn_genera.hide()
            self.btn_approva.hide()
            self.btn_svuota.hide()
            self.btn_modifica.show()
            self.btn_pdf.show()
        else:
            self.btn_genera.show()
            self.btn_approva.show()
            self.btn_svuota.show()
            self.btn_modifica.hide()
            self.btn_pdf.hide()

    def update_dashboard_data(self):
        # 1. Copertura Turni (Calcolata sui limiti configurati)
        # Recupera i limiti dal sistema
        limiti = self.interfaccia.turnazione.limiti_fascia # dict[TipoFascia, int]
        
        # Calcola target per fascia
        targets = {
            TipoFascia.MATTINA: limiti.get(TipoFascia.MATTINA, 0) * 7,
            TipoFascia.POMERIGGIO: limiti.get(TipoFascia.POMERIGGIO, 0) * 7,
            TipoFascia.NOTTE: limiti.get(TipoFascia.NOTTE, 0) * 7
        }
        
        actuals = {
            TipoFascia.MATTINA: 0,
            TipoFascia.POMERIGGIO: 0,
            TipoFascia.NOTTE: 0
        }
        
        # Conta i turni effettivamente assegnati nella settimana corrente
        anno, settimana, _ = self.current_monday.isocalendar()
        settimana_dict = self.interfaccia.turnazione.get_turnazione_settimana((anno, settimana))
        
        if settimana_dict:
            for day_fasce in settimana_dict.values():
                for tipo, fascia in day_fasce.items():
                    if tipo in actuals:
                        actuals[tipo] += len(fascia.assegnazioni)
        
        # Totali generali
        total_target = sum(targets.values())
        total_actual = sum(actuals.values())
        
        perc = (total_actual / total_target * 100) if total_target > 0 else 0
        self.lbl_coverage_perc.setText(f"{int(perc)}%")
        self.lbl_coverage_detail.setText(f"{total_actual} / {total_target} Turni assegnati")
        
        # Aggiorna le barre di dettaglio
        for tipo, (pbar, lbl) in self.coverage_bars.items():
            tgt = targets.get(tipo, 0)
            act = actuals.get(tipo, 0)
            
            # Evita divisione per zero nel massimo della progress bar
            pbar.setMaximum(tgt if tgt > 0 else 1)
            # Cap a 100% se il numero di assegnati supera il target
            pbar.setValue(min(act, tgt))
            lbl.setText(f"{act}/{tgt}")

        # Aggiorna le due liste dinamiche
        dipendenti = self.interfaccia.sistema_dipendenti.get_lista_dipendenti()
        self.update_current_absences(dipendenti)
        self.update_weekly_summary(dipendenti)

    def update_current_absences(self, dipendenti):

        # 2. Assenze Correnti (che intersecano la settimana visualizzata)
        week_start = datetime.combine(self.current_monday, datetime.min.time())
        week_end = datetime.combine(self.current_monday + timedelta(days=6), datetime.max.time())
        
        # Svuota lista attuale
        while self.abs_layout.count():
            child = self.abs_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        found_abs = False
        fmt = "%Y-%m-%d %H:%M:%S"
        
        for dip in dipendenti:
            for ass in dip.assenze_programmate:
                try:
                    dt_inizio = datetime.strptime(ass.data_inizio, fmt)
                    dt_fine = datetime.strptime(ass.data_fine, fmt)
                    
                    # Verifica intersezione
                    if max(week_start, dt_inizio) <= min(week_end, dt_fine):
                        found_abs = True
                        self.create_absence_item(dip, ass, dt_inizio, dt_fine)
                except ValueError:
                    continue
        
        if not found_abs:
             lbl_none = QLabel("Nessuna assenza prevista.")
             lbl_none.setStyleSheet("color: #94a3b8; font-style: italic; margin-top: 10px;")
             lbl_none.setAlignment(Qt.AlignmentFlag.AlignCenter)
             self.abs_layout.addWidget(lbl_none)

    def create_absence_item(self, dip, ass, start, end):
        item = QWidget()
        item.setStyleSheet("background-color: transparent;")
        h_layout = QHBoxLayout(item)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(10)
        
        lbl_name = QLabel(f"{dip.nome} {dip.cognome}") 
        lbl_name.setStyleSheet("font-weight: 600; color: #334155;") 
        
        tipo = TipoAssenza(ass.tipo)
        pill = QLabel(tipo.value)
        pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pill.setFixedSize(80, 24)
        
        # Stile Pillola
        bg = "#f1f5f9"
        fg = "#475569"
        border = "#e2e8f0"
        
        if tipo == TipoAssenza.FERIE: bg, fg, border = "#dcfce7", "#166534", "#bbf7d0"
        elif tipo == TipoAssenza.ROL: bg, fg, border = "#fef9c3", "#854d0e", "#fde047"
        elif tipo == TipoAssenza.CERTIFICATO: bg, fg, border = "#fee2e2", "#991b1b", "#fecaca"
            
        pill.setStyleSheet(f"background-color: {bg}; color: {fg}; border: 1px solid {border}; border-radius: 6px; font-size: 11px; font-weight: bold;")
        
        lbl_dates = QLabel(f"{start.strftime('%d/%m')} -> {end.strftime('%d/%m')}")
        lbl_dates.setStyleSheet("color: #64748b; font-size: 12px;")
        lbl_dates.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        h_layout.addWidget(lbl_name, stretch=2) # Stretch per allineare con header
        # Allineamento centrale per la pillola
        h_layout.addWidget(pill, stretch=1, alignment=Qt.AlignmentFlag.AlignCenter)
        # h_layout.addStretch() # Rimosso per usare stretch factor
        h_layout.addWidget(lbl_dates, stretch=1)
        
        self.abs_layout.addWidget(item)

    def update_weekly_summary(self, dipendenti):
        anno, settimana, _ = self.current_monday.isocalendar()
        settimana_key = (anno, settimana)
        settimana_dict = self.interfaccia.turnazione.get_turnazione_settimana(settimana_key)

        # Svuota lista attuale
        while self.summary_layout.count():
            child = self.summary_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not settimana_dict:
            lbl_none = QLabel("Nessun turno da riepilogare.")
            lbl_none.setStyleSheet("color: #94a3b8; font-style: italic; margin-top: 10px;")
            lbl_none.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.summary_layout.addWidget(lbl_none)
            return

        # Verifica se la settimana è APPROVATA
        is_approved = False
        for giorno_dict in settimana_dict.values():
            for fascia in giorno_dict.values():
                if fascia.stato == StatoFascia.APPROVATA:
                    is_approved = True
                    break
            if is_approved: break

        # Trova tutti i dipendenti coinvolti
        dipendenti_coinvolti_ids = set()
        for giorno_dict in settimana_dict.values():
            for fascia in giorno_dict.values():
                for assegnazione in fascia.assegnazioni:
                    dipendenti_coinvolti_ids.add(assegnazione.dipendente.id_dipendente)
        
        for dip_id in sorted(list(dipendenti_coinvolti_ids)):
            dip = self.interfaccia.sistema_dipendenti.get_dipendente(dip_id)
            if not dip: continue

            # Recuperiamo il dettaglio ore (lavorate, assenze, saldo)
            ore_lav, ore_ass, delta = self.interfaccia.turnazione.get_dettaglio_ore_settimanale(
                dip_id, settimana_key, self.interfaccia.sistema_dipendenti
            )

            summary_item = self.create_summary_item(dip, ore_lav, ore_ass, delta, is_approved)
            self.summary_layout.addWidget(summary_item)

    def create_summary_card(self):
        card = QFrame()
        card.setObjectName("summary_card")
        card.setMinimumWidth(300)
        card.setStyleSheet("#summary_card { background-color: white; border: 1px solid #e2e8f0; border-radius: 12px; }")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QHBoxLayout()
        header.setSpacing(10)
        title = QLabel("RIEPILOGO")
        title.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold; letter-spacing: 0.5px;")
        
        info_badge = QWidget()
        info_badge.setStyleSheet("background-color: #eff6ff; border-radius: 4px;")
        badge_layout = QHBoxLayout(info_badge)
        badge_layout.setContentsMargins(6, 4, 8, 4)
        badge_layout.setSpacing(5)
        
        icon = QLabel()
        pix = QPixmap("./interfacciaGrafica/assets/information-circle.svg")
        p = QPainter(pix)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        p.fillRect(pix.rect(), QColor("#3b82f6"))
        p.end()
        icon.setPixmap(pix.scaled(14, 14, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        badge_text = QLabel("Base contrattuale: 38h")
        badge_text.setStyleSheet("color: #3b82f6; font-size: 11px; font-weight: 600; background: transparent;")
        
        badge_layout.addWidget(icon)
        badge_layout.addWidget(badge_text)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(info_badge)
        layout.addLayout(header)

        # Header Colonne Riepilogo
        summary_header = QHBoxLayout()
        summary_header.setContentsMargins(0, 10, 0, 5)
        summary_header.addWidget(QLabel("DIPENDENTE"), stretch=2)
        summary_header.addWidget(QLabel("ORE LAVORATE"), stretch=1, alignment=Qt.AlignmentFlag.AlignCenter)
        summary_header.addWidget(QLabel("STATO"), stretch=1, alignment=Qt.AlignmentFlag.AlignRight)
        for i in range(summary_header.count()): 
            w = summary_header.itemAt(i).widget()
            if w:
                w.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold;")
        layout.addLayout(summary_header)

        # Scroll Area per la lista
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(120)
        scroll.setStyleSheet(self.scrollbar_style)
        
        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        self.summary_layout = QVBoxLayout(content)
        self.summary_layout.setContentsMargins(0, 5, 5, 0)
        self.summary_layout.setSpacing(8)
        self.summary_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        return card

    def create_summary_item(self, dip, ore_lav, ore_ass, delta, is_approved):
        item = QWidget()
        item.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(item)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(10)
        
        lbl_name = QLabel(f"<b>{dip.nome} {dip.cognome}</b>")
        lbl_name.setStyleSheet("color: #334155;")
        layout.addWidget(lbl_name)
        
        # Calcolo visualizzazione parziale (Ore / Max) e differenza
        max_ore = self.interfaccia.turnazione.MAX_ORE
        ore_totali = ore_lav + ore_ass
        
        # Testo principale: "38.00 / 38h" con eventuale delta (+2.0)
        delta_str = f" ({delta:+.2f})" if delta != 0 else ""
        text_ore = f"<b>{ore_totali:.2f}{delta_str}</b> / {max_ore}h"
        
        # Se ci sono assenze, mostriamo il dettaglio sotto: "(30.40L + 7.60A)"
        if ore_ass > 0:
            text_ore += f"<br/><span style='font-size: 10px; color: #64748b;'>{ore_lav:.2f}L + {ore_ass:.2f}A</span>"
        
        style_ore = "color: #334155;"
        if delta > 0:
            style_ore = "color: #ef4444; font-weight: bold;"

        lbl_ore = QLabel(text_ore)
        lbl_ore.setStyleSheet(style_ore)
        
        pill = QLabel()
        pill.setFixedWidth(120) # Larghezza fissa per allineamento
        pill.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if not is_approved:
            # Se non approvato, mostra stato provvisorio
            pill.setText("In Corso")
            pill.setStyleSheet("background-color: #f1f5f9; color: #94a3b8; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 11px; font-weight: bold; padding: 4px 8px;")
        else:
            # Se approvato, mostra il calcolo banca ore effettivo
            if delta > 0:
                pill.setText(f"Banca Ore (+{delta:.2f}h)")
                # Arancione deciso per differenziare dai ROL (giallo/ambra)
                pill.setStyleSheet("background-color: #ffedd5; color: #c2410c; border: 1px solid #fdba74; border-radius: 6px; font-size: 11px; font-weight: bold; padding: 4px 8px;")
            elif delta < 0:
                pill.setText(f"Banca Ore (-{abs(delta):.2f}h)")
                # Stesso arancione per coerenza "Banca Ore", indicando debito
                pill.setStyleSheet("background-color: #ffedd5; color: #c2410c; border: 1px solid #fdba74; border-radius: 6px; font-size: 11px; font-weight: bold; padding: 4px 8px;")
            else:
                pill.setText("In Regola")
                pill.setStyleSheet("background-color: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 11px; font-weight: bold; padding: 4px 8px;")
        
        layout.addWidget(lbl_name, stretch=2)
        layout.addWidget(lbl_ore, stretch=1, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(pill, stretch=1, alignment=Qt.AlignmentFlag.AlignRight)
        return item

    def create_day_widget(self, dt: date):
        # Usa la nuova classe DayWidget che gestisce il disegno in modo corretto
        return DayWidget(dt, self.holidays, self)

    def aggiorna_tabella(self):
        # Calcola le festività per l'anno della settimana corrente
        y1 = self.current_monday.year
        y2 = (self.current_monday + timedelta(days=6)).year
        self.holidays = get_festivita_italiane(y1)
        if y1 != y2:
            self.holidays.update(get_festivita_italiane(y2))

        self.update_header_ui()
        self.update_dashboard_data()
        
        anno, settimana, _ = self.current_monday.isocalendar()
        
        settimana_dict = self.interfaccia.turnazione.get_turnazione_settimana((anno, settimana))
        
        # Se la settimana non ha alcun turno, mostriamo i bottoni "crea" / "genera"
        if not settimana_dict:
            self.table.hide()
            self.empty_widget.show()
        else:
            self.empty_widget.hide()
            self.table.show()
            self.renderizza_tabella(settimana_dict)
            
    def renderizza_tabella(self, settimana_dict):
        # Mettiamo i giorni in ordine
        date_ordinari = sorted(list(settimana_dict.keys()))
        self.table.setRowCount(len(date_ordinari))
        
        self.date_rows = date_ordinari
        
        # --- Fix Altezza Tabella (Adatta al contenuto) ---
        # Header (80px) + Righe (80px * N) + Bordi (2px)
        total_h = 80 + (len(date_ordinari) * 80) + 2
        self.table.setMaximumHeight(total_h)

        for row, dt_turno in enumerate(date_ordinari):
            self.table.setRowHeight(row, 80) # Altezza fissa per le righe
            
            # Colonna 0: Giorno
            day_widget = self.create_day_widget(dt_turno)
            self.table.setCellWidget(row, 0, day_widget)
            
            fasce_giorno = settimana_dict[dt_turno]
            
            for col, tipo_fascia in enumerate(self.fasce_disponibili):
                table_col = col + 1 # Offset di 1 per la colonna giorno

                if tipo_fascia in fasce_giorno:
                    fascia = fasce_giorno[tipo_fascia]
                    assegnazioni = fascia.assegnazioni
                    stato = fascia.stato
                else:
                    assegnazioni = []
                    stato = StatoFascia.VUOTA

                # Utilizziamo il nuovo widget personalizzato
                cell_widget = ShiftCellWidget(row, table_col, stato, assegnazioni, dt_turno, self.interfaccia, highlighted_id=self.highlighted_dip_id, parent=self.table)
                cell_widget.clicked.connect(self.on_cell_clicked)
                cell_widget.pillDeleteRequested.connect(self.rimuovi_dipendente_da_turno)
                cell_widget.pillEditRequested.connect(self.modifica_assegnazione_turno)
                cell_widget.pillHighlightRequested.connect(self.toggle_highlight)
                self.table.setCellWidget(row, table_col, cell_widget)

    def toggle_highlight(self, row, col, id_dipendente):
        """Attiva o disattiva l'evidenziazione per un dipendente specifico."""
        if self.highlighted_dip_id == id_dipendente:
            self.highlighted_dip_id = None
        else:
            self.highlighted_dip_id = id_dipendente
        self.aggiorna_tabella()

    def rimuovi_dipendente_da_turno(self, row, col, id_dipendente):
        tipo_fascia = self.fasce_disponibili[col - 1]
        dt_turno = self.date_rows[row]
        
        # Check approvazione
        anno, settimana, _ = dt_turno.isocalendar()
        fascia = self.interfaccia.turnazione.turnazioneSettimanale.get((anno, settimana), {}).get(dt_turno, {}).get(tipo_fascia)
        if fascia and fascia.stato == StatoFascia.APPROVATA:
            QMessageBox.information(self, "Blocco Modifica", "Questa settimana è stata APPROVATA e i conteggi banca ore sono stati consolidati.\n\nPer apportare modifiche, clicca sul pulsante 'Riapri Settimana' in alto a destra.")
            return

        # Conferma eliminazione
        res = QMessageBox.question(self, "Elimina Turno", "Sei sicuro di voler rimuovere questo dipendente dal turno?")
        if res == QMessageBox.StandardButton.Yes:
            if self.interfaccia.turnazione.rimuovi_assegnazione(id_dipendente, dt_turno, tipo_fascia):
                self.aggiorna_tabella()

    def modifica_assegnazione_turno(self, row, col, assegnazione):
        tipo_fascia = self.fasce_disponibili[col - 1]
        dt_turno = self.date_rows[row]
        
        # Check approvazione
        anno, settimana, _ = dt_turno.isocalendar()
        fascia = self.interfaccia.turnazione.turnazioneSettimanale.get((anno, settimana), {}).get(dt_turno, {}).get(tipo_fascia)
        if fascia and fascia.stato == StatoFascia.APPROVATA:
            QMessageBox.information(self, "Blocco Modifica", "Questa settimana è stata APPROVATA e i conteggi banca ore sono stati consolidati.\n\nPer apportare modifiche, clicca sul pulsante 'Riapri Settimana' in alto a destra.")
            return
        
        dipendenti = self.interfaccia.sistema_dipendenti.get_lista_dipendenti()
        dialog = AssignTurnoDialog(dipendenti, dt_turno, tipo_fascia.value, self, assegnazione_esistente=assegnazione)
        
        if dialog.exec():
            # In caso di modifica, rimuoviamo la vecchia assegnazione e inseriamo la nuova
            # (è il modo più pulito per aggiornare i trigger del DB se necessari)
            id_dip = assegnazione.dipendente.id_dipendente
            self.interfaccia.turnazione.rimuovi_assegnazione(id_dip, dt_turno, tipo_fascia)
            
            try:
                self.interfaccia.turnazione.assegna_turno(
                    self.interfaccia.sistema_dipendenti, 
                    id_dip, 
                    dt_turno, 
                    tipo_fascia, 
                    dialog.piano_scelto, 
                    dialog.jolly_scelto, 
                    dialog.corto_scelto
                )
                self.aggiorna_tabella()
            except ValueError as e:
                QMessageBox.critical(self, "Errore", str(e))
                self.aggiorna_tabella()

    def on_cell_clicked(self, row, col):
        if col == 0: return # Ignora click sulla colonna del giorno

        tipo_fascia = self.fasce_disponibili[col - 1]
        dt_turno = self.date_rows[row]
        
        dipendenti = self.interfaccia.sistema_dipendenti.get_lista_dipendenti()
        
        # Recupera la fascia selezionata per controllare lo stato
        anno, settimana, _ = dt_turno.isocalendar()
        fascia = self.interfaccia.turnazione.turnazioneSettimanale.get((anno, settimana), {}).get(dt_turno, {}).get(tipo_fascia)
        
        if fascia and fascia.stato == StatoFascia.APPROVATA:
            QMessageBox.information(self, "Blocco Modifica", "Questa settimana è stata APPROVATA e i conteggi banca ore sono stati consolidati.\n\nPer apportare modifiche, clicca sul pulsante 'Riapri Settimana' in alto a destra.")
            return

        dialog = AssignTurnoDialog(dipendenti, dt_turno, tipo_fascia.value, self)
        if dialog.exec() and dialog.id_scelto is not None:
            # Esegui assegnazione con parametri estesi
            try:
                self.interfaccia.turnazione.assegna_turno(
                    self.interfaccia.sistema_dipendenti, 
                    dialog.id_scelto, 
                    dt_turno, 
                    tipo_fascia, 
                    dialog.piano_scelto, 
                    dialog.jolly_scelto, 
                    dialog.corto_scelto
                )
                self.aggiorna_tabella()
            except Exception as e:
                QMessageBox.warning(self, "Errore", f"Impossibile assegnare: {str(e)}")
                    
    def crea_da_zero(self):
        anno, settimana, _ = self.current_monday.isocalendar()
        
        # Generiamo le 7 date per quella settimana ISO!
        giorni = [date.fromisocalendar(anno, settimana, i) for i in range(1, 8)]
        
        for giorno in giorni:
            for fascia in self.fasce_disponibili:
                # Aggiungiamo i contenitori a database per la tabella
                self.interfaccia.turnazione.add_turno(giorno, fascia)
                
        # Ricarichiamo
        self.aggiorna_tabella()
        
    def genera_turni_auto(self):
        # Conferma
        reply = QMessageBox.question(self, "Generazione Automatica", 
                                   "Vuoi avviare la generazione automatica dei turni per questa settimana usando l'algoritmo di rotazione?\n\nNota: i turni esistenti verranno mantenuti, verranno riempiti solo i posti vacanti.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            anno, settimana, _ = self.current_monday.isocalendar()
            
            # Feedback visivo di caricamento
            progress = QProgressDialog(self)
            # Aggiungiamo dei ritorni a capo per dare respiro al testo senza la barra
            progress.setLabelText("\nGenerazione automatica in corso... Attendere.\n")
            progress.setWindowTitle("Elaborazione")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            
            # Togliamo la barra di caricamento che rimaneva ferma
            bar = progress.findChild(QProgressBar)
            if bar:
                bar.hide()

            progress.setMinimumWidth(350)
            progress.setMinimumDuration(0) # Appare istantaneamente
            progress.setCancelButton(None)
            
            # Applichiamo uno stile forte al testo interno
            progress.setStyleSheet("QLabel { color: #1e293b; font-weight: bold; font-size: 14px; qproperty-alignment: AlignCenter; }")

            progress.show()
            # Processiamo gli eventi due volte per essere sicuri che il sistema operativo disegni la finestra
            QApplication.processEvents()
            QApplication.processEvents()
            
            from sistemaTurnazione.sistemaGenerazione import SistemaGenerazione
            generatore = SistemaGenerazione(self.interfaccia.turnazione, self.interfaccia.sistema_dipendenti)
            
            esito = generatore.genera_turnazione_automatica(anno, settimana, genera_piani=True)
            
            progress.close()
            
            if esito:
                QMessageBox.information(self, "Completato", "Turnazione generata con successo.")
                self.aggiorna_tabella()
            else:
                QMessageBox.critical(self, "Errore", "Si è verificato un errore durante la generazione.")

    def approva_settimana_ui(self):
        # --- Controllo preventivo della copertura dei turni ---
        limiti = self.interfaccia.turnazione.limiti_fascia
        total_target = sum(limiti.get(tf, 0) * 7 for tf in [TipoFascia.MATTINA, TipoFascia.POMERIGGIO, TipoFascia.NOTTE])
        
        anno, settimana, _ = self.current_monday.isocalendar()
        settimana_dict = self.interfaccia.turnazione.get_turnazione_settimana((anno, settimana))
        
        total_actual = 0
        if settimana_dict:
            for day_fasce in settimana_dict.values():
                for tipo, fascia in day_fasce.items():
                    if tipo in [TipoFascia.MATTINA, TipoFascia.POMERIGGIO, TipoFascia.NOTTE]:
                        total_actual += len(fascia.assegnazioni)
        
        perc = (total_actual / total_target * 100) if total_target > 0 else 0
        
        if perc < 100:
            QMessageBox.warning(self, "Approvazione Negata", 
                                f"Impossibile approvare la settimana: la copertura dei turni è al {int(perc)}%.\n\n"
                                "Assicurati di aver coperto tutti i posti vacanti secondo i limiti configurati prima di procedere.")
            return

        reply = QMessageBox.question(self, "Approvazione Settimana", 
                                   "Con l'approvazione, i saldi ore verranno consolidati nella banca ore dei dipendenti e la settimana verrà bloccata.\n\nVuoi procedere?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            anno, settimana, _ = self.current_monday.isocalendar()
            if self.interfaccia.turnazione.approva_settimana(self.interfaccia.sistema_dipendenti, (anno, settimana)):
                QMessageBox.information(self, "Approvata", "Settimana approvata e banca ore aggiornata.")
                self.aggiorna_tabella()
            else:
                QMessageBox.warning(self, "Errore", "Impossibile approvare la settimana.")

    def riapri_settimana_ui(self):
        reply = QMessageBox.question(self, "Riapertura Settimana", 
                                   "Riaprendo la settimana, i saldi banca ore precedentemente calcolati verranno stornati.\n\nVuoi proseguire con lo sblocco?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            anno, settimana, _ = self.current_monday.isocalendar()
            if self.interfaccia.turnazione.riapri_settimana(self.interfaccia.sistema_dipendenti, (anno, settimana)):
                QMessageBox.information(self, "Riaperta", "Settimana riaperta. I turni sono ora modificabili.")
                self.aggiorna_tabella()
            else:
                QMessageBox.warning(self, "Errore", "Impossibile riaprire la settimana.")

    def svuota_settimana_ui(self):
        reply = QMessageBox.question(self, "Svuota Settimana", 
                                   "Sei sicuro di voler cancellare TUTTE le assegnazioni della settimana corrente?\n\nI dati non salvati andranno persi e i turni torneranno allo stato iniziale.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            anno, settimana, _ = self.current_monday.isocalendar()
            if self.interfaccia.turnazione.svuota_settimana(anno, settimana):
                QMessageBox.information(self, "Svuotata", "Tutte le assegnazioni della settimana sono state rimosse.")
                self.aggiorna_tabella()
            else:
                QMessageBox.warning(self, "Errore", "Impossibile svuotare la settimana. Verifica che non sia già approvata.")

    def esporta_pdf(self):
        """Apre il dialogo di salvataggio e richiama la generazione del PDF."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Esporta Turnazione PDF", 
            f"Turni_Settimana_{self.current_monday.strftime('%Y_%W')}.pdf", 
            "PDF Files (*.pdf)"
        )
        
        if not path:
            return

        try:
            genera_pdf_settimanale(
                path, 
                self.current_monday, 
                self.interfaccia.sistema_dipendenti, 
                self.interfaccia.turnazione, 
                self.fasce_disponibili
            )
            
            res = QMessageBox.information(self, "PDF Generato", f"Il file è stato salvato con successo in:\n{path}", 
                                          QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Ok)
            if res == QMessageBox.StandardButton.Open:
                import os
                os.startfile(path)
        except Exception as e:
            QMessageBox.critical(self, "Errore Esportazione", f"Errore durante la creazione del PDF:\n{str(e)}")

    def get_colored_icon(self, icon_path, color_hex):
        """Ricolora un'icona SVG/PNG usando QPainter"""
        pixmap = QPixmap(icon_path)
        if pixmap.isNull():
            return QIcon()
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(color_hex))
        painter.end()
        icon = QIcon(pixmap)
        icon.addPixmap(pixmap, QIcon.Mode.Disabled, QIcon.State.Off)
        icon.addPixmap(pixmap, QIcon.Mode.Disabled, QIcon.State.On)
        return icon

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, 
    QSpinBox, QHeaderView, QMessageBox, QComboBox, QDialog,
    QFrame, QScrollArea, QSizePolicy, QAbstractItemView
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QSize, QDate, QRect
from datetime import datetime, date, timedelta

# Importiamo TipoFascia per accedere ai riferimenti dei turni
from sistemaTurnazione.fasciaOraria import TipoFascia
from sistemaDipendenti.assenzaProgrammata import TipoAssenza

class AssignTurnoDialog(QDialog):
    def __init__(self, dipendenti, dt_turno, tipo_fascia, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Assegna Turno - {dt_turno} ({tipo_fascia})")
        self.setFixedWidth(350)
        self.id_scelto = None
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Seleziona il Dipendente:"))
        self.combo = QComboBox()
        self.combo.setStyleSheet("color: #0f172a; background-color: white; border: 1px solid #cbd5e1; padding: 4px;")
        for dip in dipendenti:
            # Opzionale: filtrare solo quelli 'ASSUNTI'
            if dip.stato.name == "ASSUNTO":
                self.combo.addItem(f"{dip.nome} {dip.cognome}", userData=dip.id_dipendente)
        layout.addWidget(self.combo)
        
        btn_layout = QHBoxLayout()
        btn_salva = QPushButton("Assegna")
        btn_annulla = QPushButton("Annulla")
        btn_salva.clicked.connect(self.accept)
        btn_annulla.clicked.connect(self.reject)
        btn_layout.addWidget(btn_salva)
        btn_layout.addWidget(btn_annulla)
        
        layout.addLayout(btn_layout)
        
    def accept(self):
        self.id_scelto = self.combo.currentData()
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
        elif (self.dt.month, self.dt.day) in self.holidays:
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
        
        # Inizializza alla data di oggi (lunedì della settimana corrente)
        today = date.today()
        self.current_monday = today - timedelta(days=today.weekday())
        
        # Lista di festività fisse (mese, giorno)
        self.holidays = [
            (1, 1), (1, 6), (4, 25), (5, 1), (6, 2), 
            (8, 15), (11, 1), (12, 8), (12, 25), (12, 26)
        ]
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
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
        self.btn_today = QPushButton("Oggi")
        self.btn_today.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_today.setFixedHeight(40)
        self.btn_today.setFixedWidth(80)
        self.btn_today.clicked.connect(self.go_today)
        
        header_layout.addWidget(btn_prev)
        header_layout.addWidget(self.lbl_week_range)
        header_layout.addWidget(btn_next)
        header_layout.addSpacing(10)
        header_layout.addWidget(self.btn_today)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # --- DASHBOARD CARD ---
        dashboard_layout = QHBoxLayout()
        dashboard_layout.setSpacing(20)

        # Card 1: Personale Attivo
        active_card = QFrame()
        active_card.setObjectName("active_card")
        active_card.setStyleSheet("""
            #active_card {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
        """)
        active_layout = QVBoxLayout(active_card)
        active_layout.setContentsMargins(20, 20, 20, 20)
        
        # Contenuto Personale Attivo
        top_row = QHBoxLayout()
        
        v_labels = QVBoxLayout()
        lbl_active_title = QLabel("PERSONALE ATTIVO")
        lbl_active_title.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold; letter-spacing: 0.5px;")
        self.lbl_active_count = QLabel("0")
        self.lbl_active_count.setStyleSheet("color: #3b82f6; font-size: 32px; font-weight: 800;")
        v_labels.addWidget(lbl_active_title)
        v_labels.addWidget(self.lbl_active_count)
        
        icon_people = QLabel()
        pix_p = QPixmap("./interfacciaGrafica/assets/people.svg")
        if not pix_p.isNull():
            painter = QPainter(pix_p)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pix_p.rect(), QColor("#3b82f6")) # Blu
            painter.end()
            icon_people.setPixmap(pix_p.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        icon_people.setStyleSheet("background-color: transparent; padding: 0px;")
        
        top_row.addLayout(v_labels)
        top_row.addStretch()
        top_row.addWidget(icon_people)
        
        active_layout.addLayout(top_row)
        active_layout.addStretch() # Spinge in alto il contenuto
        
        dashboard_layout.addWidget(active_card)

        # Card 2: Assenze Correnti
        abs_card = QFrame()
        abs_card.setObjectName("abs_card")
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
        
        # Lista scrollabile
        scroll_abs = QScrollArea()
        scroll_abs.setWidgetResizable(True)
        scroll_abs.setFixedHeight(120)
        scroll_abs.setStyleSheet("border: none; background: transparent;")
        
        abs_content = QWidget()
        self.abs_layout = QVBoxLayout(abs_content)
        self.abs_layout.setContentsMargins(0, 5, 0, 0)
        self.abs_layout.setSpacing(8)
        self.abs_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_abs.setWidget(abs_content)
        abs_layout_card.addWidget(scroll_abs)
        
        dashboard_layout.addWidget(abs_card, stretch=2)

        # Bottoni Azione
        btns_container = QVBoxLayout()
        btns_container.setSpacing(15)
        
        btn_style = """
            QPushButton {
                background-color: white;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 15px;
                text-align: left;
                font-weight: bold;
                color: #334155;
            }
            QPushButton:hover {
                background-color: #f8fafc;
                border-color: #94a3b8;
                color: #0f172a;
            }
        """
        
        self.btn_modifica = QPushButton("✏️  Modifica")
        self.btn_modifica.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_modifica.setStyleSheet(btn_style)
        
        self.btn_approva = QPushButton("✅  Approva")
        self.btn_approva.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_approva.setStyleSheet(btn_style)
        
        self.btn_pdf = QPushButton("📄  Esporta PDF")
        self.btn_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pdf.setStyleSheet(btn_style)
        
        btns_container.addWidget(self.btn_modifica)
        btns_container.addWidget(self.btn_approva)
        btns_container.addWidget(self.btn_pdf)
        btns_container.addStretch()
        
        dashboard_layout.addLayout(btns_container, stretch=1)
        
        layout.addLayout(dashboard_layout)

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
        
        btn_genera = QPushButton("✨ Genera Turni (A.I.)")
        btn_crea_zero = QPushButton("📝 Crea da zero (Svuota Tabella)")
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
             self.btn_today.setEnabled(False)
        else:
             self.btn_today.setStyleSheet("background-color: white; color: #0f172a; border: 1px solid #cbd5e1; font-weight: normal; border-radius: 8px;")
             self.btn_today.setEnabled(True)

    def update_dashboard_data(self):
        # 1. Personale Attivo (Statica, o filtrata per quelli attivi in data lunedì)
        dipendenti = self.interfaccia.sistema_dipendenti.get_lista_dipendenti()
        active_count = sum(1 for d in dipendenti if d.stato.name == "ASSUNTO")
        self.lbl_active_count.setText(str(active_count))

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
        
        h_layout.addWidget(lbl_name)
        h_layout.addWidget(pill)
        h_layout.addStretch()
        h_layout.addWidget(lbl_dates)
        
        self.abs_layout.addWidget(item)

    def create_day_widget(self, dt: date):
        # Usa la nuova classe DayWidget che gestisce il disegno in modo corretto
        return DayWidget(dt, self.holidays, self)

    def aggiorna_tabella(self):
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
                    assegnati = ", ".join([f"{a.dipendente.nome} {a.dipendente.cognome}" for a in fascia.assegnazioni])
                    testo = assegnati if assegnati else "+ Aggiungi"
                else:
                    testo = "+ Aggiungi" 

                item = QTableWidgetItem(testo)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                if testo == "+ Aggiungi":
                    item.setForeground(QColor("#94a3b8"))
                else:
                    item.setForeground(QColor("#334155"))
                    item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                    
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable) 
                
                self.table.setItem(row, table_col, item)

    def on_cell_clicked(self, row, col):
        if col == 0: return # Ignora click sulla colonna del giorno

        tipo_fascia = self.fasce_disponibili[col - 1]
        dt_turno = self.date_rows[row]
        
        dipendenti = self.interfaccia.sistema_dipendenti.get_lista_dipendenti()
        dialog = AssignTurnoDialog(dipendenti, dt_turno, tipo_fascia.value, self)
        if dialog.exec() and dialog.id_scelto is not None:
            # Esegui assegnazione (per ora Piano=0, Jolly=False, Breve=False)
            try:
                self.interfaccia.turnazione.assegna_turno(
                    self.interfaccia.sistema_dipendenti, 
                    dialog.id_scelto, 
                    dt_turno, 
                    tipo_fascia, 
                    0, False, False
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
        QMessageBox.information(self, "Coming Soon", "Questa funzionalità applicherà algoritmi per generare tutti i turni.")

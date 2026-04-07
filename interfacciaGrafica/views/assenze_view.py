from path_util import resource_path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QMessageBox, QDialog, QLineEdit, QFormLayout, QComboBox, 
    QProgressBar, QScrollArea, QGridLayout, QDoubleSpinBox, QDateTimeEdit, QFrame, QMenu
)
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor, QAction
from PyQt6.QtCore import Qt, QSize, QDateTime, pyqtSignal
from sistemaDipendenti.assenzaProgrammata import TipoAssenza
from datetime import datetime, date, timedelta

class AddAssenzaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aggiungi Assenza")
        self.setFixedWidth(400)
        
        layout = QFormLayout(self)
        layout.setSpacing(15)
        
        self.tipo_combo = QComboBox()
        for tipo in TipoAssenza:
            self.tipo_combo.addItem(tipo.value, userData=tipo)
        self.tipo_combo.currentIndexChanged.connect(self.update_input_format)
        self.tipo_combo.setStyleSheet("""
            QComboBox { background-color: white; color: #0f172a; border: 1px solid #cbd5e1; padding: 5px; border-radius: 4px; }
            QComboBox QAbstractItemView { background-color: white; color: #0f172a; selection-background-color: #f1f5f9; }
        """)
            
        self.inizio_input = QDateTimeEdit(QDateTime.currentDateTime())
        self.fine_input = QDateTimeEdit(QDateTime.currentDateTime())
        
        # Impostazioni grafiche selettori
        for widget in [self.inizio_input, self.fine_input]:
            widget.setCalendarPopup(True)
            widget.setMinimumWidth(250)
            widget.setStyleSheet("background-color: white; color: #0f172a; padding: 5px; border: 1px solid #cbd5e1; border-radius: 4px;")
            # Allarghiamo il popup del calendario per far sì che la domenica sia visibile e non tagliata
            if widget.calendarWidget():
                widget.calendarWidget().setMinimumWidth(300)
        
        layout.addRow("Tipo:", self.tipo_combo)
        self.lbl_inizio = QLabel("Data Inizio:")
        self.lbl_fine = QLabel("Data Fine:")
        layout.addRow(self.lbl_inizio, self.inizio_input)
        layout.addRow(self.lbl_fine, self.fine_input)
        
        btn_layout = QHBoxLayout()
        btn_salva = QPushButton("Aggiungi")
        btn_annulla = QPushButton("Annulla")
        btn_salva.clicked.connect(self.accept)
        btn_annulla.clicked.connect(self.reject)
        btn_layout.addWidget(btn_salva)
        btn_layout.addWidget(btn_annulla)
        
        layout.addRow(btn_layout)
        self.update_input_format()
        
    def update_input_format(self):
        tipo = self.tipo_combo.currentData()
        if tipo == TipoAssenza.ROL:
            fmt = "dd/MM/yyyy HH:mm"
            self.lbl_inizio.setText("Inizio (Data e Ora):")
            self.lbl_fine.setText("Fine (Data e Ora):")
        else:
            fmt = "dd/MM/yyyy"
            self.lbl_inizio.setText("Giorno Inizio:")
            self.lbl_fine.setText("Giorno Fine:")
            
        self.inizio_input.setDisplayFormat(fmt)
        self.fine_input.setDisplayFormat(fmt)
        
    def get_data(self):
        tipo = self.tipo_combo.currentData()
        dt_inizio = self.inizio_input.dateTime().toPyDateTime()
        dt_fine = self.fine_input.dateTime().toPyDateTime()
        
        # Se è FERIE o CERTIFICATO, normalizziamo le ore per coprire l'intera giornata
        if tipo != TipoAssenza.ROL:
            dt_inizio = dt_inizio.replace(hour=0, minute=0, second=0)
            dt_fine = dt_fine.replace(hour=23, minute=59, second=59)
            
        return tipo, dt_inizio, dt_fine

class EditSaldiDialog(QDialog):
    def __init__(self, ferie_attuali, rol_attuali, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modifica Saldi Ferie/ROL")
        self.setFixedWidth(300)
        
        layout = QFormLayout(self)
        
        self.spin_ferie = QDoubleSpinBox()
        self.spin_rol = QDoubleSpinBox()
        for spin in [self.spin_ferie, self.spin_rol]:
            spin.setStyleSheet("background-color: white; color: #0f172a; border: 1px solid #cbd5e1; padding: 5px; border-radius: 4px;")

        self.spin_ferie.setRange(-100, 365)
        self.spin_ferie.setValue(ferie_attuali)
        self.spin_ferie.setSuffix(" gg")
        
        self.spin_rol.setRange(-1000, 1000)
        self.spin_rol.setValue(rol_attuali)
        self.spin_rol.setSuffix(" ore")
        
        layout.addRow("Ferie Residue:", self.spin_ferie)
        layout.addRow("ROL Residui:", self.spin_rol)
        
        btn_layout = QHBoxLayout()
        btn_salva = QPushButton("Salva")
        btn_annulla = QPushButton("Annulla")
        btn_salva.clicked.connect(self.accept)
        btn_annulla.clicked.connect(self.reject)
        btn_layout.addWidget(btn_salva)
        btn_layout.addWidget(btn_annulla)
        
        layout.addRow(btn_layout)
    
    def get_data(self):
        return self.spin_ferie.value(), self.spin_rol.value()

class AssenzaCard(QFrame):
    deleteRequested = pyqtSignal(object)
    editRequested = pyqtSignal(object)

    def __init__(self, assenza, parent=None):
        super().__init__(parent)
        self.assenza = assenza
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setObjectName("assenza_card")
        self.setStyleSheet("""
            #assenza_card {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            #assenza_card:hover { border-color: #3b82f6; }
            QLabel { color: #0f172a; background: transparent; }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        
        # Icona e Stile basato sul tipo
        tipo_assenza = TipoAssenza(assenza.tipo)
        config = {
            TipoAssenza.FERIE: ("interfacciaGrafica/assets/american-football.svg", "#f0fdf4", "#16a34a"),
            TipoAssenza.ROL: ("interfacciaGrafica/assets/time.svg", "#fefce8", "#ca8a04"),
            TipoAssenza.CERTIFICATO: ("interfacciaGrafica/assets/medkit.svg", "#fee2e2", "#dc2626")
        }
        icon_path, bg_color, icon_color = config.get(tipo_assenza)

        icon_label = QLabel()
        icon_label.setFixedSize(40, 40)
        icon_label.setStyleSheet(f"background-color: {bg_color}; border-radius: 20px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        pixmap = QPixmap(resource_path(icon_path))
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(icon_color))
        painter.end()
        icon_label.setPixmap(pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        # Info Testuali
        txt_layout = QVBoxLayout()
        lbl_title = QLabel(f"<b>{tipo_assenza.value.upper()}</b>")
        
        fmt_in = "%Y-%m-%d %H:%M:%S"
        dt_inizio = datetime.strptime(assenza.data_inizio, fmt_in)
        dt_fine = datetime.strptime(assenza.data_fine, fmt_in)
        
        lbl_dates = QLabel(f"{dt_inizio.strftime('%d %b %Y')}  →  {dt_fine.strftime('%d %b %Y')}")
        lbl_dates.setStyleSheet("font-size: 13px; color: #64748b;")
        
        txt_layout.addWidget(lbl_title)
        txt_layout.addWidget(lbl_dates)

        # Durata a destra
        delta = dt_fine - dt_inizio
        durata_str = f"{delta.days + 1} gg" if tipo_assenza != TipoAssenza.ROL else f"{delta.total_seconds()/3600:.1f} ore"
        lbl_durata = QLabel(durata_str)
        lbl_durata.setStyleSheet("font-weight: bold; color: #0f172a;")

        layout.addWidget(icon_label)
        layout.addLayout(txt_layout)
        layout.addStretch()
        layout.addWidget(lbl_durata)

    def show_context_menu(self, pos):
        # Impedisce la modifica o eliminazione se l'assenza è già conclusa
        fmt_in = "%Y-%m-%d %H:%M:%S"
        dt_fine = datetime.strptime(self.assenza.data_fine, fmt_in)
        if dt_fine < datetime.now():
            msg = QMessageBox(self)
            msg.setWindowTitle("Azione non consentita")
            msg.setText("Impossibile modificare o eliminare un'assenza già conclusa.")
            msg.setIcon(QMessageBox.Icon.Information)
            # Forziamo i colori per garantire la leggibilità indipendentemente dal tema di sistema
            msg.setStyleSheet("""
                QMessageBox { background-color: white; }
                QLabel { color: #0f172a; font-size: 14px; }
                QPushButton { 
                    background-color: #f1f5f9; 
                    color: #0f172a; 
                    border: 1px solid #cbd5e1; 
                    padding: 6px 20px; 
                    border-radius: 4px; 
                }
                QPushButton:hover { background-color: #e2e8f0; }
            """)
            msg.exec()
            return

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: white; border: 1px solid #cbd5e1; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 6px 24px; color: #334155; border-radius: 4px; }
            QMenu::item:selected { background-color: #f1f5f9; color: #3b82f6; }
        """)
        
        edit_act = QAction("Modifica Periodo", self)
        edit_act.setIcon(self.get_colored_icon("interfacciaGrafica/assets/pencil.svg", "#3b82f6"))
        delete_act = QAction("Elimina Assenza", self)
        delete_act.setIcon(self.get_colored_icon("interfacciaGrafica/assets/trash-bin.svg", "#dc2626"))
        
        menu.addAction(edit_act)
        menu.addSeparator()
        menu.addAction(delete_act)
        
        action = menu.exec(self.mapToGlobal(pos))
        if action == edit_act:
            self.editRequested.emit(self.assenza)
        elif action == delete_act:
            self.deleteRequested.emit(self.assenza)

    def get_colored_icon(self, path, color):
        pix = QPixmap(resource_path(path))
        painter = QPainter(pix)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pix.rect(), QColor(color))
        painter.end()
        return QIcon(pix)

class AssenzeView(QWidget):
    navigazioneTurni = pyqtSignal(date)

    def __init__(self, interfaccia):
        super().__init__()
        self.interfaccia = interfaccia
        self.current_dip_id = None
        self.is_large_layout = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 20, 0, 0) # No margini laterali, solo sopra
        main_layout.setSpacing(20)

        # --- Header ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Assenze Programmate")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f172a;")
        
        self.btn_add = QPushButton("  Aggiungi Assenza")
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.setIcon(QIcon(resource_path("interfacciaGrafica/assets/add-circle.svg")))
        self.btn_add.setIconSize(QSize(20, 20))
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6; color: white; border: none;
                padding: 10px 24px; border-radius: 8px; font-weight: bold; font-size: 15px;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        self.btn_add.clicked.connect(self.cmd_add_assenza)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_add)

        # --- Body (Riepilogo a sx, Lista a dx) ---
        body_layout = QHBoxLayout()
        body_layout.setSpacing(30)
        
        # Colonna Sinistra: Container Verticale
        left_column = QWidget()
        left_column.setStyleSheet("background-color: transparent;")
        self.left_layout = QVBoxLayout(left_column)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(20)
        
        self.riepilogo_card = self.create_riepilogo_ui()
        self.left_layout.addWidget(self.riepilogo_card)
        self.left_layout.addStretch()
        
        body_layout.addWidget(left_column, alignment=Qt.AlignmentFlag.AlignTop)
        
        # Colonna Destra: Lista Assenze
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        # Overlay Container
        overlay = QWidget()
        self.overlay_layout = QGridLayout(overlay)
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_content = QWidget()
        scroll_content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        scroll_content.setStyleSheet("background-color: transparent;")
        self.lista_assenze_layout = QVBoxLayout(scroll_content)
        self.lista_assenze_layout.setSpacing(15)
        self.lista_assenze_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.lista_assenze_layout.setContentsMargins(0, 0, 0, 100) # Spazio per non coprire l'ultimo elemento
        
        scroll_area.setWidget(scroll_content)
        # self.info_card = self.create_info_card() # NASCOSTO TEMPORANEAMENTE

        self.overlay_layout.addWidget(scroll_area, 0, 0)
        # info_card posizionata dinamicamente (Disabilitato)
        
        body_layout.addWidget(overlay, stretch=1)

        main_layout.addLayout(header_layout)
        main_layout.addLayout(body_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Se l'altezza è sufficiente (> 550px per ospitare Resoconto + Info), sposta a sinistra
        is_large = self.height() > 550
        
        if is_large != self.is_large_layout:
            self.is_large_layout = is_large
            self.update_info_card_position()
            
    def update_info_card_position(self):
        if not hasattr(self, 'info_card'): return

        self.info_card.setParent(None)
        
        if self.is_large_layout:
            # --- POSIZIONE: Colonna Sinistra ---
            # Inserisce dopo il riepilogo
            self.left_layout.insertWidget(1, self.info_card)
            
            # Stile Statico
            self.info_card.setStyleSheet("""
                #info_card {
                    background-color: #eff6ff;
                    border: 1px solid #dbeafe;
                    border-radius: 8px;
                }
            """)
            self.info_card.layout().setContentsMargins(15, 15, 15, 15)
            
        else:
            # --- POSIZIONE: Overlay Destra ---
            self.overlay_layout.addWidget(self.info_card, 0, 0, Qt.AlignmentFlag.AlignBottom)
            
            # Stile Overlay (Sfumato)
            self.info_card.setStyleSheet("""
                #info_card {
                    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(239, 246, 255, 0), stop:0.3 #eff6ff, stop:1 #eff6ff);
                    border: 1px solid #dbeafe;
                    border-top: none;
                    border-bottom-left-radius: 8px;
                    border-bottom-right-radius: 8px;
                    border-top-left-radius: 0px;
                    border-top-right-radius: 0px;
                }
            """)
            self.info_card.layout().setContentsMargins(20, 40, 20, 20)

    def create_riepilogo_ui(self):
        card = QWidget()
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setObjectName("riepilogo_card")
        card.setFixedWidth(350)
        card.setMaximumHeight(450) # Altezza massima per forzare lo scroll interno su schermi piccoli
        card.setStyleSheet("""
            #riepilogo_card {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
            QLabel {
                color: #0f172a;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Titolo Generale + Bottone Modifica
        header_layout = QHBoxLayout()
        title_lbl = QLabel("Resoconto Mensile")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #0f172a; margin-bottom: 5px;")
        
        # Preparo l'icona ricolorandola di blu
        pix_pencil = QPixmap(resource_path("interfacciaGrafica/assets/pencil.svg"))
        if not pix_pencil.isNull():
            painter = QPainter(pix_pencil)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pix_pencil.rect(), QColor("#3b82f6"))
            painter.end()

        self.btn_modifica = QPushButton("  Modifica")
        self.btn_modifica.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_modifica.setIcon(QIcon(pix_pencil))
        self.btn_modifica.setIconSize(QSize(14, 14))
        self.btn_modifica.setStyleSheet("""
            QPushButton {
                color: #3b82f6;
                background: transparent;
                border: none;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { text-decoration: underline; }
        """)
        self.btn_modifica.clicked.connect(self.cmd_modifica_resoconto)

        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_modifica)
        layout.addLayout(header_layout)

        layout.addSpacing(10)

        # --- Scroll Area Interna ---
        scroll_internal = QScrollArea()
        scroll_internal.setWidgetResizable(True)
        scroll_internal.setStyleSheet("""
            QScrollArea { border: none; background-color: transparent; }
            QWidget { background-color: transparent; }
            QScrollBar:vertical {
                border: none;
                background: #f1f5f9;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #cbd5e1;
                min-height: 20px;
                border-radius: 3px;
            }
        """)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 5, 0) # Margine destro per scrollbar
        content_layout.setSpacing(20)

        # Ferie
        header_ferie = QHBoxLayout()
        header_ferie.addWidget(QLabel("<b>Ferie Residue</b>"))
        header_ferie.addStretch()
        self.lbl_ferie = QLabel()
        self.lbl_ferie.setStyleSheet("color: #64748b; font-weight: bold;")
        header_ferie.addWidget(self.lbl_ferie)
        content_layout.addLayout(header_ferie)

        self.progress_ferie = QProgressBar()
        self.progress_ferie.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                background-color: #f1f5f9;
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: #22c55e; /* Green */
                border-radius: 3px;
            }
        """)
        self.progress_ferie.setTextVisible(False)
        content_layout.addWidget(self.progress_ferie)

        # ROL
        header_rol = QHBoxLayout()
        header_rol.addWidget(QLabel("<b>ROL Residui</b>"))
        header_rol.addStretch()
        self.lbl_rol = QLabel()
        self.lbl_rol.setStyleSheet("color: #64748b; font-weight: bold;")
        header_rol.addWidget(self.lbl_rol)
        content_layout.addLayout(header_rol)

        self.progress_rol = QProgressBar()
        self.progress_rol.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                background-color: #f1f5f9;
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: #f59e0b; /* Amber */
                border-radius: 3px;
            }
        """)
        self.progress_rol.setTextVisible(False)
        content_layout.addWidget(self.progress_rol)

        # Certificati (Sub-Card)
        cert_subcard = QWidget()
        cert_subcard.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        cert_subcard.setObjectName("cert_subcard")
        cert_subcard.setStyleSheet("""
            #cert_subcard {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-left: 5px solid #ef4444;
                border-radius: 8px;
            }
        """)
        cert_layout = QVBoxLayout(cert_subcard)
        cert_layout.setContentsMargins(20, 15, 20, 15)
        cert_layout.setSpacing(2)

        lbl_cert_title = QLabel("Certificati Medici")
        lbl_cert_title.setStyleSheet("color: #64748b; font-weight: bold; font-size: 13px; border: none; background: transparent;")
        cert_layout.addWidget(lbl_cert_title)

        self.lbl_certificati = QLabel()
        self.lbl_certificati.setStyleSheet("font-size: 26px; font-weight: 800; color: #0f172a; border: none; background: transparent;")
        cert_layout.addWidget(self.lbl_certificati)
        
        content_layout.addWidget(cert_subcard)
        content_layout.addStretch()
        
        scroll_internal.setWidget(content_widget)
        layout.addWidget(scroll_internal)
        
        return card

    def create_info_card(self):
        info_card = QWidget()
        info_card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        info_card.setObjectName("info_card")
        # Stile applicato dinamicamente
        info_layout = QHBoxLayout(info_card)
        info_layout.setSpacing(10)

        info_icon = QLabel()
        
        pixmap = QPixmap(resource_path("interfacciaGrafica/assets/information-circle.svg"))
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor("#1e3a8a")) # Blu Scuro (uguale al testo)
        painter.end()
        
        info_icon.setPixmap(pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        info_text = QLabel("Parte dei ROL maturati dovranno essere utilizzati o pagati entro il...")
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #1e3a8a; font-size: 13px; border: none; background: transparent;")

        info_layout.addWidget(info_icon)
        info_layout.addWidget(info_text)

        return info_card

    def load_data(self, id_dipendente):
        self.current_dip_id = id_dipendente
        dip = self.interfaccia.sistema_dipendenti.get_dipendente(id_dipendente)
        if not dip: return

        # Gestione visibilità bottoni in base allo stato
        is_attivo = dip.stato.name == "ASSUNTO"
        self.btn_add.setVisible(is_attivo)
        # Se il bottone modifica esiste (è stato creato in create_riepilogo_ui), lo gestiamo
        if hasattr(self, 'btn_modifica'):
             self.btn_modifica.setVisible(is_attivo)


        # --- Aggiorna Riepilogo ---
        # Calcolo i totali basandomi sul saldo inizio mese (Attuale + Consumato nel mese)
        now = datetime.now()
        mese_corrente_inizio = datetime(now.year, now.month, 1)
        if now.month == 12:
            mese_succ_inizio = datetime(now.year + 1, 1, 1)
        else:
            mese_succ_inizio = datetime(now.year, now.month + 1, 1)
            
        ferie_consumate = 0.0
        rol_consumati = 0.0
        
        assenze = self.interfaccia.sistema_dipendenti.get_assenze_dipendente(id_dipendente)
        fmt = "%Y-%m-%d %H:%M:%S"
        
        for ass in assenze:
            try:
                dt_inizio = datetime.strptime(ass.data_inizio, fmt)
                dt_fine = datetime.strptime(ass.data_fine, fmt)
                # Intersezione con il mese corrente
                start = max(dt_inizio, mese_corrente_inizio)
                end = min(dt_fine, mese_succ_inizio)
                
                if start < end:
                    delta = end - start
                    if ass.tipo == TipoAssenza.FERIE.value:
                        ferie_consumate += delta.total_seconds() / 86400
                    elif ass.tipo == TipoAssenza.ROL.value:
                        rol_consumati += delta.total_seconds() / 3600
            except ValueError:
                continue

        ferie_inizio_mese = dip.ferie_rimanenti + ferie_consumate
        rol_inizio_mese = dip.rol_rimanenti + rol_consumati

        perc_ferie = (dip.ferie_rimanenti / ferie_inizio_mese) * 100 if ferie_inizio_mese > 0 else 0
        self.progress_ferie.setValue(int(perc_ferie))
        self.lbl_ferie.setText(f"{dip.ferie_rimanenti:.2f} / {ferie_inizio_mese:.2f} giorni")

        perc_rol = (dip.rol_rimanenti / rol_inizio_mese) * 100 if rol_inizio_mese > 0 else 0
        self.progress_rol.setValue(int(perc_rol))
        self.lbl_rol.setText(f"{dip.rol_rimanenti:.2f} / {rol_inizio_mese:.2f} ore")

        num_certificati = sum(1 for a in assenze if a.tipo == TipoAssenza.CERTIFICATO.value)
        self.lbl_certificati.setText(str(num_certificati))

        # --- Aggiorna Lista Assenze ---
        while self.lista_assenze_layout.count():
            child = self.lista_assenze_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Filtra assenze (Future/Presenti vs Passate)
        now = datetime.now()
        fmt = "%Y-%m-%d %H:%M:%S"
        
        future = []
        past = []
        
        for a in assenze:
            try:
                # Consideriamo passata se la data fine è precedente a ora
                dt_fine = datetime.strptime(a.data_fine, fmt)
                if dt_fine < now:
                    past.append(a)
                else:
                    future.append(a)
            except ValueError:
                future.append(a) # Fallback in caso di errore data

        if not future and not past:
            self.lista_assenze_layout.setContentsMargins(0, 0, 0, 0)
            self.lista_assenze_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_empty = QLabel("Nessuna assenza programmata.")
            lbl_empty.setStyleSheet("color: #64748b; font-size: 16px; font-style: italic;")
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lista_assenze_layout.addWidget(lbl_empty)
        else:
            # Margine ridotto dato che la card info è nascosta
            self.lista_assenze_layout.setContentsMargins(0, 0, 0, 20)
            self.lista_assenze_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            
            # Assenze Future: Ordinate dalla più vicina (reverse=False)
            for assenza in sorted(future, key=lambda a: a.data_inizio, reverse=False):
                card = self.create_assenza_card(assenza)
                card.deleteRequested.connect(self.cmd_delete_assenza)
                card.editRequested.connect(self.cmd_edit_assenza)
                self.lista_assenze_layout.addWidget(card)

            # Se ci sono assenze passate, mostra bottone toggle
            if past:
                self.btn_toggle_past = QPushButton("Visualizza assenze passate ▼")
                self.btn_toggle_past.setCursor(Qt.CursorShape.PointingHandCursor)
                self.btn_toggle_past.setStyleSheet("""
                    QPushButton {
                        border: none; background: transparent; color: #64748b;
                        font-weight: bold; font-size: 14px; padding: 10px; margin-top: 10px;
                    }
                    QPushButton:hover { color: #3b82f6; background-color: #f8fafc; border-radius: 6px; }
                """)
                self.btn_toggle_past.clicked.connect(self.toggle_past_assenze)
                self.lista_assenze_layout.addWidget(self.btn_toggle_past)
                
                self.container_past = QWidget()
                self.layout_past = QVBoxLayout(self.container_past)
                self.layout_past.setContentsMargins(0, 0, 0, 0)
                self.layout_past.setSpacing(15)
                
                # Assenze Passate: Ordinate dalla più recente (reverse=True)
                for assenza in sorted(past, key=lambda a: a.data_inizio, reverse=True):
                    card = self.create_assenza_card(assenza)
                    # Opzionale: Rendi le card passate leggermente trasparenti o diverse
                    self.layout_past.addWidget(card)
                    
                self.container_past.setVisible(False)
                self.lista_assenze_layout.addWidget(self.container_past)

    def toggle_past_assenze(self):
        if self.container_past.isVisible():
            self.container_past.hide()
            self.btn_toggle_past.setText("Visualizza assenze passate ▼")
        else:
            self.container_past.show()
            self.btn_toggle_past.setText("Nascondi assenze passate ▲")

    def create_assenza_card(self, assenza):
        return AssenzaCard(assenza)

    def cmd_delete_assenza(self, assenza):
        res = QMessageBox.question(self, "Elimina Assenza", 
            f"Sei sicuro di voler eliminare questa registrazione di {assenza.tipo}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if res == QMessageBox.StandardButton.Yes:
            # Nota: Assumiamo che esista il metodo nel backend o usiamo quello esistente
            # Se non esiste, dovrai implementare la rimozione nel sistemaDipendenti
            success = self.interfaccia.sistema_dipendenti.rimuovi_assenza(self.current_dip_id, assenza.id_assenza)
            if success:
                self.load_data(self.current_dip_id)
            else:
                QMessageBox.critical(self, "Errore", "Impossibile eliminare l'assenza.")

    def cmd_edit_assenza(self, assenza):
        dialog = AddAssenzaDialog(self)
        dialog.setWindowTitle("Modifica Assenza")
        # Pre-popolamento (conversione date)
        fmt = "%Y-%m-%d %H:%M:%S"
        dialog.tipo_combo.setCurrentText(assenza.tipo)
        dialog.inizio_input.setDateTime(QDateTime.fromString(assenza.data_inizio, Qt.DateFormat.ISODate))
        dialog.fine_input.setDateTime(QDateTime.fromString(assenza.data_fine, Qt.DateFormat.ISODate))
        
        if dialog.exec():
            tipo, dt_inizio, dt_fine = dialog.get_data()
            str_inizio = dt_inizio.strftime(fmt)
            str_fine = dt_fine.strftime(fmt)
            
            # Rimuoviamo la vecchia e aggiungiamo la nuova per gestire correttamente i saldi
            self.interfaccia.sistema_dipendenti.rimuovi_assenza(self.current_dip_id, assenza.id_assenza)
            success = self.interfaccia.sistema_dipendenti.aggiungi_assenza(
                self.current_dip_id, tipo, str_inizio, str_fine
            )
            
            if success:
                QMessageBox.information(self, "Successo", "Assenza modificata correttamente.")
                self.load_data(self.current_dip_id)
            else:
                QMessageBox.critical(self, "Errore", "Errore durante la modifica.")

    def cmd_add_assenza(self):
        if not self.current_dip_id: return
        
        dialog = AddAssenzaDialog(self)
        if dialog.exec():
            tipo, dt_inizio, dt_fine = dialog.get_data()
            if tipo and dt_inizio and dt_fine:
                str_inizio = dt_inizio.strftime("%Y-%m-%d %H:%M:%S")
                str_fine = dt_fine.strftime("%Y-%m-%d %H:%M:%S")
                
                success = self.interfaccia.sistema_dipendenti.aggiungi_assenza(
                    self.current_dip_id, tipo, str_inizio, str_fine
                )
                if success == "SOVRAPPOSIZIONE":
                    QMessageBox.warning(self, "Attenzione", "Il dipendente ha già un'assenza registrata in questo periodo.")
                    return
                if success:
                    # Controllo se il dipendente era già presente in turnazione
                    start_d = dt_inizio.date()
                    end_d = dt_fine.date()
                    conflict_date = None
                    
                    curr = start_d
                    while curr <= end_d:
                        anno, sett, _ = curr.isocalendar()
                        assegnazioni = self.interfaccia.turnazione.get_assegnazioni_dipendente((anno, sett), self.current_dip_id)
                        if any(f.data_turno == curr for f, ass in assegnazioni):
                            conflict_date = curr
                            break
                        curr += timedelta(days=1)
                    
                    if conflict_date:
                        res = QMessageBox.question(self, "Conflitto Turnazione", 
                            f"Assenza aggiunta con successo. Tuttavia il dipendente era già presente in turnazione il {conflict_date.strftime('%d/%m/%Y')}.\n\nVuoi andare alla turnazione per modificarla ora?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                        if res == QMessageBox.StandardButton.Yes:
                            self.navigazioneTurni.emit(conflict_date)
                    
                    self.load_data(self.current_dip_id)
                else:
                    QMessageBox.critical(self, "Errore", "Impossibile aggiungere l'assenza.")
            else:
                QMessageBox.warning(self, "Dati non validi", "Il formato della data non è corretto.")

    def cmd_modifica_resoconto(self):
        if not self.current_dip_id: return
        
        dip = self.interfaccia.sistema_dipendenti.get_dipendente(self.current_dip_id)
        if not dip: return

        dialog = EditSaldiDialog(dip.ferie_rimanenti, dip.rol_rimanenti, self)
        if dialog.exec():
            new_ferie, new_rol = dialog.get_data()
            
            # Riutilizziamo la funzione generica di modifica passando i nuovi saldi
            success = self.interfaccia.sistema_dipendenti.modifica_dipendente(
                id_dipendente=dip.id_dipendente,
                nome=dip.nome,
                cognome=dip.cognome,
                ferie=new_ferie,
                rol=new_rol,
                banca_ore=dip.banca_ore
            )
            if success:
                self.load_data(self.current_dip_id)
            else:
                QMessageBox.critical(self, "Errore", "Impossibile aggiornare i saldi.")
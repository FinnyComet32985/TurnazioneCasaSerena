from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget,
    QMessageBox, QDialog, QLineEdit, QFormLayout, QComboBox, 
    QProgressBar, QScrollArea, QGridLayout
)
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor
from PyQt6.QtCore import Qt, QSize
from sistemaDipendenti.assenzaProgrammata import TipoAssenza
from datetime import datetime

class AddAssenzaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aggiungi Assenza")
        
        layout = QFormLayout(self)
        
        self.tipo_combo = QComboBox()
        for tipo in TipoAssenza:
            self.tipo_combo.addItem(tipo.value, userData=tipo)
            
        self.inizio_input = QLineEdit(datetime.now().strftime("%d/%m/%Y %H:%M"))
        self.fine_input = QLineEdit(datetime.now().strftime("%d/%m/%Y %H:%M"))
        
        layout.addRow("Tipo:", self.tipo_combo)
        layout.addRow("Data Inizio (GG/MM/AAAA HH:MM):", self.inizio_input)
        layout.addRow("Data Fine (GG/MM/AAAA HH:MM):", self.fine_input)
        
        btn_layout = QHBoxLayout()
        btn_salva = QPushButton("Aggiungi")
        btn_annulla = QPushButton("Annulla")
        btn_salva.clicked.connect(self.accept)
        btn_annulla.clicked.connect(self.reject)
        btn_layout.addWidget(btn_salva)
        btn_layout.addWidget(btn_annulla)
        
        layout.addRow(btn_layout)
        
    def get_data(self):
        try:
            tipo = self.tipo_combo.currentData()
            dt_inizio = datetime.strptime(self.inizio_input.text(), "%d/%m/%Y %H:%M")
            dt_fine = datetime.strptime(self.fine_input.text(), "%d/%m/%Y %H:%M")
            return tipo, dt_inizio, dt_fine
        except ValueError:
            return None, None, None

class AssenzeView(QWidget):
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
        self.btn_add.setIcon(QIcon("./interfacciaGrafica/assets/add-circle.svg"))
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
        title_lbl = QLabel("Resoconto")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #0f172a; margin-bottom: 5px;")
        
        # Preparo l'icona ricolorandola di blu
        pix_pencil = QPixmap("./interfacciaGrafica/assets/pencil.svg")
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
        
        pixmap = QPixmap("./interfacciaGrafica/assets/information-circle.svg")
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
        # Valori massimi basati su CCNL (26gg ferie, 32h ROL)
        FERIE_ANNUE = 26
        ROL_ANNUI = 32

        perc_ferie = (dip.ferie_rimanenti / FERIE_ANNUE) * 100 if FERIE_ANNUE > 0 else 0
        self.progress_ferie.setValue(int(perc_ferie))
        self.lbl_ferie.setText(f"{dip.ferie_rimanenti:.2f} / {FERIE_ANNUE} giorni")

        perc_rol = (dip.rol_rimanenti / ROL_ANNUI) * 100 if ROL_ANNUI > 0 else 0
        self.progress_rol.setValue(int(perc_rol))
        self.lbl_rol.setText(f"{dip.rol_rimanenti:.2f} / {ROL_ANNUI} ore")

        assenze = self.interfaccia.sistema_dipendenti.get_assenze_dipendente(id_dipendente)
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
        card = QWidget()
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setObjectName("assenza_card")
        card.setStyleSheet("""
            #assenza_card {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QLabel {
                color: #0f172a;
                background-color: transparent;
                border: none;
            }
        """)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Icona
        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        tipo_assenza = TipoAssenza(assenza.tipo)
        icon_path = ""
        bg_color = ""
        icon_color = ""

        if tipo_assenza == TipoAssenza.FERIE:
            icon_path = "./interfacciaGrafica/assets/american-football.svg"
            bg_color = "#f0fdf4"  # Light Green
            icon_color = "#16a34a" # Dark Green
        elif tipo_assenza == TipoAssenza.ROL:
            icon_path = "./interfacciaGrafica/assets/time.svg"
            bg_color = "#fefce8"
            icon_color = "#ca8a04"
        elif tipo_assenza == TipoAssenza.CERTIFICATO:
            icon_path = "./interfacciaGrafica/assets/medkit.svg"
            bg_color = "#fee2e2"
            icon_color = "#dc2626"

        icon_label.setStyleSheet(f"background-color: {bg_color}; border-radius: 24px;")
        
        # Ricolorazione SVG (se necessario)
        pixmap = QPixmap(icon_path)
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(icon_color))
        painter.end()
        
        icon_label.setPixmap(pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        # Titolo (Accanto all'icona)
        lbl_title = QLabel(f"<b>{tipo_assenza.value.upper()}</b>")
        lbl_title.setStyleSheet("font-size: 16px; color: #0f172a;")

        # Info (A destra)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        fmt_in = "%Y-%m-%d %H:%M:%S"
        fmt_out = "%d %b %Y"
        dt_inizio = datetime.strptime(assenza.data_inizio, fmt_in)
        dt_fine = datetime.strptime(assenza.data_fine, fmt_in)
        
        lbl_date = QLabel(f"{dt_inizio.strftime(fmt_out)}  →  {dt_fine.strftime(fmt_out)}")
        lbl_date.setStyleSheet("font-size: 14px; color: #0f172a; font-weight: bold;")
        lbl_date.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Calcolo durata
        delta = dt_fine - dt_inizio
        giorni = delta.days
        ore = (delta.seconds / 3600) % 24
        durata_str = ""
        if giorni > 0:
            durata_str += f"{giorni} giorni"
        if ore > 0:
            if durata_str: durata_str += " e "
            durata_str += f"{int(ore)} ore"
        
        lbl_durata = QLabel(durata_str)
        lbl_durata.setStyleSheet("color: #64748b;")
        lbl_durata.setAlignment(Qt.AlignmentFlag.AlignRight)

        info_layout.addWidget(lbl_date)
        info_layout.addWidget(lbl_durata)

        layout.addWidget(icon_label)
        layout.addWidget(lbl_title)
        layout.addStretch()
        layout.addLayout(info_layout)

        return card

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
                if success:
                    self.load_data(self.current_dip_id) # Ricarica i dati
                else:
                    QMessageBox.critical(self, "Errore", "Impossibile aggiungere l'assenza.")
            else:
                QMessageBox.warning(self, "Dati non validi", "Il formato della data non è corretto.")

    def cmd_modifica_resoconto(self):
        QMessageBox.information(self, "In Sviluppo", "La modifica manuale dei saldi sarà disponibile a breve.")
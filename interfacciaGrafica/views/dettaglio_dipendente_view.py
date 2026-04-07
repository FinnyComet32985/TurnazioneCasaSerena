from path_util import resource_path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QStackedWidget, QMessageBox, QDialog, QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QSize
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor, QPen, QPainterPath

# Import della nuova vista per le assenze
from .assenze_view import AssenzeView
from .banca_ore_view import BancaOreView

class EditAnagraficaDialog(QDialog):
    def __init__(self, nome_attuale, cognome_attuale, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modifica Dati Anagrafici")
        self.setFixedWidth(300)
        
        layout = QFormLayout(self)
        
        self.input_cognome = QLineEdit(cognome_attuale)
        self.input_nome = QLineEdit(nome_attuale)
        
        for inp in [self.input_nome, self.input_cognome]:
            inp.setStyleSheet("background-color: white; color: #0f172a; border: 1px solid #cbd5e1; padding: 5px; border-radius: 4px;")

        layout.addRow("Cognome:", self.input_cognome)
        layout.addRow("Nome:", self.input_nome)
        
        btn_layout = QHBoxLayout()
        btn_salva = QPushButton("Salva")
        btn_annulla = QPushButton("Annulla")
        btn_salva.clicked.connect(self.accept)
        btn_annulla.clicked.connect(self.reject)
        btn_layout.addWidget(btn_salva)
        btn_layout.addWidget(btn_annulla)
        
        layout.addRow(btn_layout)
    
    def get_data(self):
        return self.input_cognome.text().strip(), self.input_nome.text().strip()

class BadgeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(580) # Larghezza minima (espandibile) per nomi lunghi
        # L'altezza si adatterà automaticamente al contenuto grazie al layout

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        lanyard_h = 50 # Spazio per il laccio sopra la card
        width = self.width()
        height = self.height()
        
        # Rettangolo del corpo del badge (parte bianca)
        card_rect = QRectF(1, lanyard_h, width-2, height - lanyard_h - 1)
        
        # --- Coordinate e Penne ---
        center_x = width / 2
        hole_w = 60
        hole_h = 8
        hole_y = lanyard_h + 16
        hole_rect = QRectF(center_x - hole_w/2, hole_y, hole_w, hole_h)
        
        back_strap_pen = QPen(QColor("#1e293b"), 8, cap=Qt.PenCapStyle.RoundCap) # Scuro
        front_strap_pen = QPen(QColor("#475569"), 8, cap=Qt.PenCapStyle.RoundCap) # Chiaro

        # --- 1. Laccio Posteriore (SCURO) ---
        # Disegnato per primo, così sta dietro a tutto.
        painter.setPen(back_strap_pen)
        painter.drawLine(int(center_x + 15), 0, int(center_x), int(hole_y + 4))

        # --- 2. Corpo della Card (Sfondo) ---
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("white"))
        painter.drawRoundedRect(card_rect, 14, 14)

        # --- 3. Accento Superiore (Striscia Blu) ---
        painter.save()
        path = QPainterPath()
        path.addRoundedRect(card_rect, 14, 14)
        painter.setClipPath(path)
        painter.setBrush(QColor("#3b82f6"))
        painter.drawRect(0, int(lanyard_h), int(width), 8)
        painter.restore()

        # --- 4. Bordo Card ---
        border_pen = QPen(QColor("#cbd5e1"), 1)
        painter.setPen(border_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(card_rect, 14, 14)
        
        # --- 5. Laccio Anteriore (CHIARO) ---
        painter.setPen(front_strap_pen)
        painter.drawLine(int(center_x - 15), 0, int(center_x), int(hole_y + 4))

        # --- 6. Buco del Badge ---
        painter.setBrush(QColor("#f1f5f9"))
        painter.setPen(QPen(QColor("#e2e8f0"), 1))
        painter.drawRoundedRect(hole_rect, 4, 4)

class DettaglioDipendenteView(QWidget):
    back_requested = pyqtSignal()
    navigazioneTurni = pyqtSignal(object) # Propaga la data verso PersonaleView

    def __init__(self, interfaccia):
        super().__init__()
        self.interfaccia = interfaccia
        self.current_dip_id = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(25)

        # --- Header with Back Button ---
        header_layout = QHBoxLayout()
        btn_back = QPushButton("  Torna alla lista")
        btn_back.setIcon(QIcon(resource_path("interfacciaGrafica/assets/arrow-back.svg")))
        btn_back.setObjectName("back_button")
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton#back_button {
                background-color: transparent;
                border: none;
                color: #64748b;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton#back_button:hover {
                color: #3b82f6;
            }
        """)
        btn_back.clicked.connect(self.back_requested.emit)
        header_layout.addWidget(btn_back)
        header_layout.addStretch()

        # --- ID Card Widget ---
        id_card = BadgeWidget()
        id_card.setObjectName("id_card")
        
        # Main vertical layout for the card to include the "hole"
        card_main_v_layout = QVBoxLayout(id_card)
        # Margine superiore aumentato (90) per non sovrapporre il contenuto al laccio/buco
        # Margine inferiore ridotto (24) per adattarsi al contenuto
        card_main_v_layout.setContentsMargins(24, 90, 24, 24)
        card_main_v_layout.setSpacing(12)

        # Layout for the main content (avatar, info, status)
        id_card_content_layout = QHBoxLayout()
        id_card_content_layout.setSpacing(24)

        self.lbl_avatar = QLabel()
        self.lbl_avatar.setFixedSize(84, 84)
        self.lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Left side info ---
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        lbl_header = QLabel("CASA SERENA • STAFF")
        lbl_header.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        
        self.lbl_nome_cognome = QLabel()
        self.lbl_nome_cognome.setStyleSheet("font-size: 26px; font-weight: 800; color: #0f172a;")
        
        self.lbl_matricola = QLabel()
        self.lbl_matricola.setStyleSheet("color: #64748b; font-size: 14px; font-family: monospace; margin-bottom: 6px;")
        
        info_layout.addWidget(lbl_header)
        info_layout.addWidget(self.lbl_nome_cognome)
        info_layout.addWidget(self.lbl_matricola)
        info_layout.addStretch() # Pushes content up

        # --- Right side status ---
        self.status_container_right = QWidget()
        self.status_container_right.setObjectName("status_container_right")
        self.status_container_right.setFixedSize(220, 84)
        self.status_container_right.setStyleSheet("""
            #status_container_right {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        status_right_layout = QVBoxLayout(self.status_container_right)
        status_right_layout.setContentsMargins(15, 15, 15, 15)
        status_right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_stato_title = QLabel("STATO ATTUALE")
        lbl_stato_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_stato_title.setStyleSheet("color: #64748b; font-size: 11px; font-weight: bold; letter-spacing: 1px; border: none; background: transparent;")

        self.lbl_stato_value = QLabel() # Value set in load_dipendente
        self.lbl_stato_value.setAlignment(Qt.AlignmentFlag.AlignCenter)

        status_right_layout.addWidget(lbl_stato_title)
        status_right_layout.addWidget(self.lbl_stato_value)

        # Assemble the card content
        id_card_content_layout.addWidget(self.lbl_avatar)
        id_card_content_layout.addLayout(info_layout)
        id_card_content_layout.addStretch()
        id_card_content_layout.addWidget(self.status_container_right)

        # Add hole and content to the main card layout
        card_main_v_layout.addLayout(id_card_content_layout)

        # --- Top Section (Card + Actions) ---
        top_container = QWidget()
        top_layout = QHBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(60) # Spazio tra card e bottoni aumentato

        # Actions Column
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(15)
        actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        actions_layout.setContentsMargins(0, 50, 0, 0) # Offset verticale per allineare al corpo card (escluso laccio)

        self.btn_modifica = QPushButton("  Modifica Dati") # Aggiunti spazi per distanziare l'icona
        self.btn_modifica.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_modifica.setIcon(QIcon(resource_path("interfacciaGrafica/assets/pencil.svg")))
        self.btn_modifica.setIconSize(QSize(20, 20))
        self.btn_modifica.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 15px;
                min-width: 200px;
                text-align: left; padding-left: 20px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.btn_modifica.clicked.connect(self.cmd_modifica)

        self.btn_licenzia = QPushButton("  Licenzia Dipendente") # Aggiunti spazi per distanziare l'icona
        self.btn_licenzia.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_licenzia.setIcon(QIcon(resource_path("interfacciaGrafica/assets/person-remove.svg")))
        self.btn_licenzia.setIconSize(QSize(20, 20))
        self.btn_licenzia.setStyleSheet("""
            QPushButton {
                background-color: #fee2e2;
                color: #dc2626;
                border: 1px solid #fecaca;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 15px;
                min-width: 200px;
                text-align: left; padding-left: 20px;
            }
            QPushButton:hover {
                background-color: #fecaca;
            }
        """)
        # Il connect viene gestito dinamicamente in load_dipendente

        actions_layout.addWidget(self.btn_modifica)
        actions_layout.addWidget(self.btn_licenzia)

        top_layout.addWidget(id_card)
        top_layout.addLayout(actions_layout)
        top_layout.addStretch()

        # --- Tab Bar ---
        tab_bar = QWidget()
        tab_layout = QHBoxLayout(tab_bar)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(30)
        
        self.btn_assenze = QPushButton("Assenze")
        self.btn_banca_ore = QPushButton("Banca Ore")
        
        self.tab_buttons = [self.btn_assenze, self.btn_banca_ore]
        
        for i, btn in enumerate(self.tab_buttons):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setObjectName("tab_button")
            btn.clicked.connect(lambda checked, index=i: self.switch_tab(index))
            tab_layout.addWidget(btn)
            
        tab_layout.addStretch()
        
        underline = QWidget()
        underline.setFixedHeight(1)
        underline.setStyleSheet("background-color: #e2e8f0;")

        # --- Tab Content (Stacked Widget) ---
        self.tab_content = QStackedWidget()
        
        self.page_assenze = AssenzeView(self.interfaccia)
        self.page_assenze.navigazioneTurni.connect(self.navigazioneTurni.emit)
        self.page_banca_ore = BancaOreView(self.interfaccia)
        
        self.tab_content.addWidget(self.page_assenze)
        self.tab_content.addWidget(self.page_banca_ore)

        # Add all widgets to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(top_container) # Contenitore Card + Bottoni
        main_layout.addWidget(tab_bar)
        main_layout.addWidget(underline)
        main_layout.addWidget(self.tab_content, stretch=1)

        self.switch_tab(0) # Set initial tab

    def switch_tab(self, index):
        self.tab_content.setCurrentIndex(index)
        for i, btn in enumerate(self.tab_buttons):
            if i == index:
                btn.setStyleSheet("background-color: transparent; border: none; padding: 10px 0px; font-size: 16px; font-weight: bold; color: #3b82f6; border-bottom: 3px solid #3b82f6;")
            else:
                btn.setStyleSheet("background-color: transparent; border: none; padding: 10px 0px; font-size: 16px; font-weight: 500; color: #64748b; border-bottom: 3px solid transparent;")

    def load_dipendente(self, id_dipendente):
        self.current_dip_id = id_dipendente
        dip = self.interfaccia.sistema_dipendenti.get_dipendente(id_dipendente)
        if not dip:
            self.back_requested.emit()
            return
        
        initials = (dip.nome[0] + dip.cognome[0]).upper()
        self.lbl_avatar.setText(initials)
        self.lbl_avatar.setStyleSheet("background-color: #eff6ff; color: #2563eb; border-radius: 12px; font-size: 32px; font-weight: bold; border: 1px solid #dbeafe;")
        
        self.lbl_nome_cognome.setText(f"{dip.cognome} {dip.nome}")
        self.lbl_matricola.setText(f"ID: {str(dip.id_dipendente).zfill(5)}")
        
        # Update the status on the right side
        dip_stato = dip.stato.name
        self.lbl_stato_value.setText(dip_stato)
        if dip_stato == "ASSUNTO":
            self.lbl_stato_value.setStyleSheet("color: #16a34a; font-size: 18px; font-weight: bold; border: none; background: transparent;")
            
            # Configurazione bottoni per dipendente ATTIVO
            self.btn_modifica.setVisible(True)
            
            self.btn_licenzia.setText("  Licenzia Dipendente")
            self.btn_licenzia.setIcon(QIcon(resource_path("interfacciaGrafica/assets/person-remove.svg")))
            self.btn_licenzia.setStyleSheet("""
                QPushButton {
                    background-color: #fee2e2;
                    color: #dc2626;
                    border: 1px solid #fecaca;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: bold;
                    font-size: 15px;
                    min-width: 200px;
                    text-align: left; padding-left: 20px;
                }
                QPushButton:hover { background-color: #fecaca; }
            """)
            try: self.btn_licenzia.clicked.disconnect() 
            except TypeError: pass
            self.btn_licenzia.clicked.connect(self.cmd_licenzia)
            
        else: # LICENZIATO
            self.lbl_stato_value.setStyleSheet("color: #64748b; font-size: 18px; font-weight: bold; border: none; background: transparent;")
            
            # Configurazione bottoni per dipendente LICENZIATO
            self.btn_modifica.setVisible(False)
            
            self.btn_licenzia.setText("  Assumi Nuovamente")
            
            # Ricolora l'icona in verde per matchare il testo
            pix_add = QPixmap(resource_path("interfacciaGrafica/assets/person-add.svg"))
            if not pix_add.isNull():
                painter = QPainter(pix_add)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                painter.fillRect(pix_add.rect(), QColor("#166534"))
                painter.end()
                self.btn_licenzia.setIcon(QIcon(pix_add))

            self.btn_licenzia.setStyleSheet("""
                QPushButton {
                    background-color: #dcfce7;
                    color: #166534;
                    border: 1px solid #bbf7d0;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-weight: bold;
                    font-size: 15px;
                    min-width: 200px;
                    text-align: left; padding-left: 20px;
                }
                QPushButton:hover { background-color: #bbf7d0; }
            """)
            try: self.btn_licenzia.clicked.disconnect() 
            except TypeError: pass
            self.btn_licenzia.clicked.connect(self.cmd_riassumi)
        
        # Carica i dati nella tab delle assenze
        self.page_assenze.load_data(self.current_dip_id)
        self.page_banca_ore.load_data(self.current_dip_id)
        
        self.switch_tab(0)
        
    def cmd_modifica(self):
        if not self.current_dip_id: return
        
        dip = self.interfaccia.sistema_dipendenti.get_dipendente(self.current_dip_id)
        if not dip: return

        dialog = EditAnagraficaDialog(dip.nome, dip.cognome, self)
        if dialog.exec():
            new_cognome, new_nome = dialog.get_data()
            if new_nome and new_cognome:
                # Manteniamo i valori attuali per i campi che non stiamo modificando qui
                success = self.interfaccia.sistema_dipendenti.modifica_dipendente(
                    id_dipendente=dip.id_dipendente,
                    nome=new_nome,
                    cognome=new_cognome,
                    ferie=dip.ferie_rimanenti,
                    rol=dip.rol_rimanenti,
                    banca_ore=dip.banca_ore
                )
                if success:
                    self.load_dipendente(self.current_dip_id)
                else:
                    QMessageBox.critical(self, "Errore", "Impossibile modificare i dati.")

    def cmd_riassumi(self):
        if not self.current_dip_id: return
        
        confirm = QMessageBox.question(self, "Conferma Riassunzione", "Sei sicuro di voler assumere nuovamente questo dipendente?")
        if confirm == QMessageBox.StandardButton.Yes:
            success = self.interfaccia.sistema_dipendenti.riassumi_dipendente(self.current_dip_id)
            if success:
                self.load_dipendente(self.current_dip_id) # Ricarica la UI aggiornando stato e bottoni
            else:
                QMessageBox.critical(self, "Errore", "Impossibile riassumere il dipendente.")

    def cmd_licenzia(self):
        if not self.current_dip_id: return
        
        confirm = QMessageBox.question(self, "Conferma Licenziamento", "Sei sicuro di voler licenziare questo dipendente?")
        if confirm == QMessageBox.StandardButton.Yes:
            success = self.interfaccia.sistema_dipendenti.rimuovi_dipendente(self.current_dip_id)
            if success:
                self.back_requested.emit() # Torna alla lista
            else:
                QMessageBox.critical(self, "Errore", "Impossibile rimuovere il dipendente.")
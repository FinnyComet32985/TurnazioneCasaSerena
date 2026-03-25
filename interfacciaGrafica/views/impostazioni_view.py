from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, 
    QPushButton, QFormLayout, QScrollArea, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from sistemaTurnazione.fasciaOraria import TipoFascia

class ImpostazioniView(QWidget):
    def __init__(self, interfaccia):
        super().__init__()
        self.interfaccia = interfaccia
        # Riferimento rapido alla logica di turnazione
        self.t = self.interfaccia.turnazione 
        self.init_ui()
        
    def init_ui(self):
        # Sfondo esplicito per tutta la vista per evitare bug del tema scuro
        self.setStyleSheet("background-color: #f8fafb;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # --- HEADER (Titolo, Sottotitolo e Bottone a destra) ---
        header_layout = QHBoxLayout()
        
        header_text_layout = QVBoxLayout()
        title = QLabel("Impostazioni")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #0f172a; background-color: transparent;")
        subtitle = QLabel("Configura i parametri di generazione e i limiti legali per il personale.")
        subtitle.setStyleSheet("font-size: 15px; color: #64748b; margin-top: 5px; background-color: transparent;")
        header_text_layout.addWidget(title)
        header_text_layout.addWidget(subtitle)
        
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()

        self.btn_save = QPushButton("  Salva Configurazioni")
        self.btn_save.setIcon(QIcon("./interfacciaGrafica/assets/save.svg"))
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setFixedWidth(220)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.btn_save.clicked.connect(self.save_settings)
        header_layout.addWidget(self.btn_save, alignment=Qt.AlignmentFlag.AlignVCenter)
        
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(10)

        # Scroll Area per gestire schermi piccoli
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(30)
        container_layout.setContentsMargins(0, 0, 20, 0)

        # --- SEZIONE 1: LIMITI OPERATORI PER FASCIA ---
        fascia_card = self.create_setting_card("Personale per Turno", "Specifica quanti dipendenti devono essere presenti in ogni fascia oraria.")
        fascia_form = QFormLayout()
        fascia_form.setSpacing(15)
        fascia_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.spin_mattina = self.create_styled_spin(1, 20, self.t.limiti_fascia.get(TipoFascia.MATTINA, 7))
        self.spin_pomeriggio = self.create_styled_spin(1, 20, self.t.limiti_fascia.get(TipoFascia.POMERIGGIO, 6))
        self.spin_notte = self.create_styled_spin(1, 10, self.t.limiti_fascia.get(TipoFascia.NOTTE, 1))

        fascia_form.addRow("Operatori Mattina:", self.spin_mattina)
        fascia_form.addRow("Operatori Pomeriggio:", self.spin_pomeriggio)
        fascia_form.addRow("Operatori Notte:", self.spin_notte)
        fascia_card.layout().addLayout(fascia_form)
        container_layout.addWidget(fascia_card)

        # --- SEZIONE 2: VINCOLI DI SISTEMA E PIANI ---
        sys_card = self.create_setting_card("Parametri di Sistema", "Configura i jolly e i limiti di affollamento per piano.")
        sys_form = QFormLayout()
        sys_form.setSpacing(15)
        
        self.spin_jolly = self.create_styled_spin(0, 5, self.t.max_jolly_per_turno)
        self.spin_piano = self.create_styled_spin(1, 10, self.t.max_dipendenti_per_piano)

        sys_form.addRow("Max Jolly per turno:", self.spin_jolly)
        sys_form.addRow("Max Dipendenti per piano (Default):", self.spin_piano)
        sys_card.layout().addLayout(sys_form)
        container_layout.addWidget(sys_card)

        container_layout.addStretch()
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def create_setting_card(self, title, description):
        card = QFrame()
        card.setObjectName("card_container")
        card.setStyleSheet("""
            #card_container {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
            QLabel { color: #334155; font-weight: 500; font-size: 14px; }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(10)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f172a;")
        
        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet("color: #64748b; font-size: 13px; margin-bottom: 10px;")
        desc_lbl.setWordWrap(True)

        layout.addWidget(title_lbl)
        layout.addWidget(desc_lbl)
        return card

    def create_styled_spin(self, min_v, max_v, current_v):
        spin = QSpinBox()
        spin.setRange(min_v, max_v)
        spin.setValue(current_v)
        spin.setFixedWidth(100)
        spin.setStyleSheet("""
            QSpinBox {
                background-color: white;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
        """)
        return spin

    def save_settings(self):
        try:
            # Salvataggio Limiti Fascia
            self.t.set_config_limite_fascia(TipoFascia.MATTINA, self.spin_mattina.value())
            self.t.set_config_limite_fascia(TipoFascia.POMERIGGIO, self.spin_pomeriggio.value())
            self.t.set_config_limite_fascia(TipoFascia.NOTTE, self.spin_notte.value())

            # Salvataggio Parametri Sistema
            self.t.set_config_max_jolly(self.spin_jolly.value())
            self.t.set_config_max_piano(self.spin_piano.value())

            QMessageBox.information(self, "Successo", "Configurazioni salvate correttamente nel database.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Impossibile salvare le impostazioni: {e}")

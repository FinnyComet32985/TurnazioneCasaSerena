from path_util import resource_path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, 
    QPushButton, QFormLayout, QScrollArea, QMessageBox, QFrame, QGridLayout
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
        self.btn_save.setIcon(QIcon(resource_path("interfacciaGrafica/assets/save.svg")))
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
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(0, 0, 20, 0)

        # --- CARD 1: PIANO DI GENERAZIONE AUTOMATICA ---
        gen_card = self.create_setting_card("Obiettivi Generazione (I.A.)", "Specifica quanti dipendenti l'algoritmo deve inserire per ogni piano. Per i turni diurni, questi valori fungono anche da limite per l'inserimento manuale.")
        gen_grid = QGridLayout()
        gen_grid.setSpacing(30)
        gen_grid.setContentsMargins(10, 15, 10, 10)

        # --- COLONNA 1: MATTINA ---
        m_box = QVBoxLayout()
        m_title = QLabel("MATTINA")
        m_title.setStyleSheet("font-weight: bold; color: #3b82f6; font-size: 14px; margin-bottom: 5px;")
        m_form = QFormLayout()
        self.m_pt = self.create_styled_spin(0, 10, self.t.limiti_piani_fascia[TipoFascia.MATTINA][0])
        self.m_p1 = self.create_styled_spin(0, 10, self.t.limiti_piani_fascia[TipoFascia.MATTINA][1])
        self.m_p2 = self.create_styled_spin(0, 10, self.t.limiti_piani_fascia[TipoFascia.MATTINA][2])
        self.m_jolly = self.create_styled_spin(0, 5, self.t.limiti_piani_fascia[TipoFascia.MATTINA]['jolly'])
        m_form.addRow("Piano Terra", self.m_pt)
        m_form.addRow("1° Piano", self.m_p1)
        m_form.addRow("2° Piano", self.m_p2)
        m_form.addRow("Jolly", self.m_jolly)
        m_box.addWidget(m_title)
        m_box.addLayout(m_form)
        gen_grid.addLayout(m_box, 0, 0)

        # --- COLONNA 2: POMERIGGIO ---
        p_box = QVBoxLayout()
        p_title = QLabel("POMERIGGIO")
        p_title.setStyleSheet("font-weight: bold; color: #ea580c; font-size: 14px; margin-bottom: 5px;")
        p_form = QFormLayout()
        self.p_pt = self.create_styled_spin(0, 10, self.t.limiti_piani_fascia[TipoFascia.POMERIGGIO][0])
        self.p_p1 = self.create_styled_spin(0, 10, self.t.limiti_piani_fascia[TipoFascia.POMERIGGIO][1])
        self.p_p2 = self.create_styled_spin(0, 10, self.t.limiti_piani_fascia[TipoFascia.POMERIGGIO][2])
        self.p_jolly = self.create_styled_spin(0, 5, self.t.limiti_piani_fascia[TipoFascia.POMERIGGIO]['jolly'])
        p_form.addRow("Piano Terra", self.p_pt)
        p_form.addRow("1° Piano", self.p_p1)
        p_form.addRow("2° Piano", self.p_p2)
        p_form.addRow("Jolly", self.p_jolly)
        p_box.addWidget(p_title)
        p_box.addLayout(p_form)
        gen_grid.addLayout(p_box, 0, 1)

        # --- COLONNA 3: NOTTE ---
        n_box = QVBoxLayout()
        n_title = QLabel("TURNO NOTTE")
        n_title.setStyleSheet("font-weight: bold; color: #6366f1; font-size: 14px; margin-bottom: 5px;")
        n_form = QFormLayout()
        self.n_tot = self.create_styled_spin(1, 5, self.t.limiti_piani_fascia[TipoFascia.NOTTE][0])
        n_form.addRow("Genera (A.I.)", self.n_tot)
        n_box.addWidget(n_title)
        n_box.addLayout(n_form)
        n_box.addStretch()
        gen_grid.addLayout(n_box, 0, 2)

        gen_card.layout().addLayout(gen_grid)
        container_layout.addWidget(gen_card)

        # --- CARD 2: VINCOLI MANUALI E SICUREZZA ---
        sys_card = self.create_setting_card("Parametri Manuali", "Imposta i limiti invalicabili per l'inserimento manuale dei turni da parte dell'utente.")
        sys_form = QFormLayout()
        sys_form.setSpacing(15)
        sys_form.setContentsMargins(10, 10, 10, 0)

        self.spin_jolly_globale = self.create_styled_spin(0, 5, self.t.max_jolly_per_turno)
        self.n_manual = self.create_styled_spin(1, 10, self.t.limiti_piani_fascia[TipoFascia.NOTTE].get('manual_limit', 2))
        
        lbl_jolly = QLabel("Limite Jolly per fascia:")
        lbl_jolly.setToolTip("Blocca l'inserimento manuale se si supera questo numero di Jolly in un singolo turno.")
        sys_form.addRow(lbl_jolly, self.spin_jolly_globale)

        lbl_n_manual = QLabel("Capienza massima Notte:")
        lbl_n_manual.setToolTip("Permette l'inserimento manuale di operatori extra di notte (es. per emergenze) fino a questo limite.")
        sys_form.addRow(lbl_n_manual, self.n_manual)

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
            # Mattina
            self.t.set_config_limite_piano_fascia(TipoFascia.MATTINA, 0, self.m_pt.value())
            self.t.set_config_limite_piano_fascia(TipoFascia.MATTINA, 1, self.m_p1.value())
            self.t.set_config_limite_piano_fascia(TipoFascia.MATTINA, 2, self.m_p2.value())
            self.t.set_config_limite_piano_fascia(TipoFascia.MATTINA, 'jolly', self.m_jolly.value())
            
            # Pomeriggio
            self.t.set_config_limite_piano_fascia(TipoFascia.POMERIGGIO, 0, self.p_pt.value())
            self.t.set_config_limite_piano_fascia(TipoFascia.POMERIGGIO, 1, self.p_p1.value())
            self.t.set_config_limite_piano_fascia(TipoFascia.POMERIGGIO, 2, self.p_p2.value())
            self.t.set_config_limite_piano_fascia(TipoFascia.POMERIGGIO, 'jolly', self.p_jolly.value())
            
            # Notte
            self.t.set_config_limite_piano_fascia(TipoFascia.NOTTE, 0, self.n_tot.value())
            self.t.set_config_limite_piano_fascia(TipoFascia.NOTTE, 'manual_limit', self.n_manual.value())

            # Parametri Sistema ripristinati
            self.t.set_config_max_jolly(self.spin_jolly_globale.value())

            QMessageBox.information(self, "Successo", "Configurazioni salvate correttamente nel database.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Impossibile salvare le impostazioni: {e}")

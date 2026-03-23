from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon

class DettaglioDipendenteView(QWidget):
    back_requested = pyqtSignal()

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
        btn_back.setIcon(QIcon("./interfacciaGrafica/assets/arrow-back.svg"))
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
        id_card = QWidget()
        id_card.setObjectName("card_container")
        id_card.setStyleSheet("#card_container { padding: 20px; }")
        id_card_layout = QHBoxLayout(id_card)
        id_card_layout.setSpacing(20)

        self.lbl_avatar = QLabel()
        self.lbl_avatar.setFixedSize(80, 80)
        self.lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        self.lbl_nome_cognome = QLabel()
        self.lbl_nome_cognome.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a;")
        
        self.status_pill_container = QWidget() # Container for the pill
        pill_layout = QHBoxLayout(self.status_pill_container)
        pill_layout.setContentsMargins(0,0,0,0)
        pill_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        info_layout.addWidget(self.lbl_nome_cognome)
        info_layout.addWidget(self.status_pill_container)
        info_layout.addStretch()

        id_card_layout.addWidget(self.lbl_avatar)
        id_card_layout.addLayout(info_layout)
        id_card_layout.addStretch()

        # --- Tab Bar ---
        tab_bar = QWidget()
        tab_layout = QHBoxLayout(tab_bar)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(30)
        
        self.btn_assenze = QPushButton("Assenze")
        self.btn_banca_ore = QPushButton("Banca Ore")
        self.btn_contratto = QPushButton("Contratto e Licenziamento")
        
        self.tab_buttons = [self.btn_assenze, self.btn_banca_ore, self.btn_contratto]
        
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
        
        page_assenze = QWidget()
        page_assenze.setLayout(QVBoxLayout())
        page_assenze.layout().addWidget(QLabel("Contenuto Assenze (da implementare)"))
        
        page_banca_ore = QWidget()
        page_banca_ore.setLayout(QVBoxLayout())
        page_banca_ore.layout().addWidget(QLabel("Contenuto Banca Ore (da implementare)"))
        
        page_contratto = QWidget()
        page_contratto.setLayout(QVBoxLayout())
        page_contratto.layout().addWidget(QLabel("Contenuto Contratto e Licenziamento (da implementare)"))
        
        self.tab_content.addWidget(page_assenze)
        self.tab_content.addWidget(page_banca_ore)
        self.tab_content.addWidget(page_contratto)

        # Add all widgets to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(id_card)
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
        self.lbl_avatar.setStyleSheet("background-color: #e0e7ff; color: #4338ca; border-radius: 12px; font-size: 32px; font-weight: bold;")
        
        self.lbl_nome_cognome.setText(f"{dip.nome} {dip.cognome}")
        
        while self.status_pill_container.layout().count():
            child = self.status_pill_container.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        pill = self.create_status_pill(dip.stato.name)
        self.status_pill_container.layout().addWidget(pill)
        
        self.switch_tab(0)
        
    def create_status_pill(self, stato):
        widget = QWidget()
        widget.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        dot = QLabel()
        dot.setFixedSize(10, 10)
        
        lbl = QLabel(stato)
        lbl.setStyleSheet("color: #0f172a; font-weight: 600; font-size: 14px;")
        
        if stato == "ASSUNTO":
            dot.setStyleSheet("background-color: #16a34a; border-radius: 5px;")
        else:
            dot.setStyleSheet("background-color: #dc2626; border-radius: 5px;")
        
        layout.addWidget(dot)
        layout.addWidget(lbl)
        return widget
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QStackedWidget
)
from PyQt6.QtCore import Qt

# Importiamo le viste
from interfacciaGrafica.views.turni_view import TurniView
from interfacciaGrafica.views.personale_view import PersonaleView
from interfacciaGrafica.views.impostazioni_view import ImpostazioniView


class MainWindow(QMainWindow):
    def __init__(self, interfaccia):
        super().__init__()
        
        # Salviamo l'istanza del backend
        self.interfaccia = interfaccia
        
        self.setWindowTitle("Turnazione Casa Serena")
        self.resize(1024, 768)
        
        self.init_ui()
        self.apply_styles()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- SIDEBAR (Scura) ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(250)
            
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        logo_container = QWidget()
        logo_container.setObjectName("logo_container")
        logo_layout = QVBoxLayout(logo_container)
        
        logo_label = QLabel("Casa Serena")
        logo_label.setObjectName("logo_text")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)
        
        sidebar_layout.addWidget(logo_container)
        
        # Voce Menu 1 - Turnazione
        self.btn_turni = QPushButton("📅 Turnazione")
        self.btn_turni.setObjectName("sidebar_btn_active")
        self.btn_turni.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_turni.clicked.connect(lambda: self.switch_page(0))
        
        # Voce Menu 2 - Personale
        self.btn_personale = QPushButton("👥 Gestione Personale")
        self.btn_personale.setObjectName("sidebar_btn")
        self.btn_personale.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_personale.clicked.connect(lambda: self.switch_page(1))

        # Voce Menu 3 - Impostazioni
        self.btn_impostazioni = QPushButton("⚙️ Impostazioni")
        self.btn_impostazioni.setObjectName("sidebar_btn")
        self.btn_impostazioni.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_impostazioni.clicked.connect(lambda: self.switch_page(2))

        sidebar_layout.addWidget(self.btn_turni)
        sidebar_layout.addWidget(self.btn_personale)
        sidebar_layout.addWidget(self.btn_impostazioni)
        sidebar_layout.addStretch() 
        
        # --- CONTENUTO PRINCIPALE ---
        self.main_content = QStackedWidget()
        self.main_content.setObjectName("main_content")
        
        # Carichiamo le viste isolate nei moduli separati
        self.page_turni = TurniView(self.interfaccia)
        self.page_personale = PersonaleView(self.interfaccia)
        self.page_impostazioni = ImpostazioniView(self.interfaccia)

        self.main_content.addWidget(self.page_turni)
        self.main_content.addWidget(self.page_personale)
        self.main_content.addWidget(self.page_impostazioni)

        # Di base partiamo dalla pagina 0 (Turni)
        self.main_content.setCurrentIndex(0)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.main_content)
        
    def switch_page(self, index):
        self.main_content.setCurrentIndex(index)
        
        self.btn_turni.setObjectName("sidebar_btn_active" if index == 0 else "sidebar_btn")
        self.btn_personale.setObjectName("sidebar_btn_active" if index == 1 else "sidebar_btn")
        self.btn_impostazioni.setObjectName("sidebar_btn_active" if index == 2 else "sidebar_btn")
        
        for btn in [self.btn_turni, self.btn_personale, self.btn_impostazioni]:
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
    def apply_styles(self):
        self.setStyleSheet("""
            * {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            #sidebar {
                background-color: #1e293b;
                border-right: 1px solid #0f172a;
            }
            #logo_container {
                background-color: #0f172a;
                min-height: 80px;
                max-height: 80px;
                border-bottom: 1px solid #334155;
            }
            #logo_text {
                color: #ffffff;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton#sidebar_btn {
                background-color: transparent;
                color: #94a3b8;
                border: none;
                text-align: left;
                padding: 15px 20px;
                font-size: 15px;
                font-weight: 500;
                border-left: 4px solid transparent;
            }
            QPushButton#sidebar_btn:hover {
                background-color: #334155;
                color: #ffffff;
            }
            QPushButton#sidebar_btn_active {
                background-color: #0f172a;
                color: #3b82f6;
                border: none;
                text-align: left;
                padding: 15px 20px;
                font-size: 15px;
                font-weight: bold;
                border-left: 4px solid #3b82f6;
            }
            #main_content {
                background-color: #f8fafc;
            }
            #page_title {
                color: #0f172a;
                font-size: 28px;
                font-weight: bold;
            }
            #page_subtitle {
                color: #64748b;
                font-size: 15px;
                margin-top: 5px;
            }
            #card_container {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)

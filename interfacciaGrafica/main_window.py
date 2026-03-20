import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QStackedWidget, QListWidget
)
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self, interfaccia):
        super().__init__()
        
        # Salviamo l'istanza del backend (simile a iniettare un Context in React o passarlo nei Props)
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
        self.btn_turni.clicked.connect(lambda: self.switch_page(0)) # Come un onClick in React
        
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
        
        # --- CONTENUTO PRINCIPALE (Il vero e proprio "Router Outlet") ---
        self.main_content = QStackedWidget()
        self.main_content.setObjectName("main_content")
        
        # --- Pagina 0: Turnazione ---
        self.page_turni = QWidget()
        self._setup_page_turni()
        
        # --- Pagina 1: Gestione Personale ---
        self.page_personale = QWidget()
        self._setup_page_personale()
        
        # --- Pagina 2: Impostazioni ---
        self.page_impostazioni = QWidget()
        temp_layout = QVBoxLayout(self.page_impostazioni)
        temp_layout.addWidget(QLabel("Pagina in costruzione..."))
        temp_layout.addStretch()

        self.main_content.addWidget(self.page_turni)
        self.main_content.addWidget(self.page_personale)
        self.main_content.addWidget(self.page_impostazioni)

        # Di base partiamo dalla pagina 0 (Turni)
        self.main_content.setCurrentIndex(0)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.main_content)
        
    def _setup_page_turni(self):
        page_turni_layout = QVBoxLayout(self.page_turni)
        page_turni_layout.setContentsMargins(40, 40, 40, 40)
        
        title_turni = QLabel("Turnazione - Settimana Corrente")
        title_turni.setObjectName("page_title")
        subtitle_turni = QLabel("Gestisci e visualizza i turni degli operatori.")
        subtitle_turni.setObjectName("page_subtitle")
        
        card_widget = QWidget()
        card_widget.setObjectName("card_container")
        card_layout = QVBoxLayout(card_widget)
        placeholder_label = QLabel("Stiamo preparando la griglia da Figma...")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(placeholder_label)

        page_turni_layout.addWidget(title_turni)
        page_turni_layout.addWidget(subtitle_turni)
        page_turni_layout.addSpacing(20)
        page_turni_layout.addWidget(card_widget)
        page_turni_layout.addStretch()

    def _setup_page_personale(self):
        page_layout = QVBoxLayout(self.page_personale)
        page_layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel("Gestione Personale")
        title.setObjectName("page_title")
        subtitle = QLabel("Visualizza e gestisci l'anagrafica dei dipendenti")
        subtitle.setObjectName("page_subtitle")
        
        card_widget = QWidget()
        card_widget.setObjectName("card_container")
        card_layout = QVBoxLayout(card_widget)
        
        # Usiamo un QListWidget per simulare una lista/tabella semplicissima.
        self.lista_ui = QListWidget()
        self.lista_ui.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
                font-size: 16px;
                color: #0f172a; /* Testo scuro */
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f1f5f9;
            }
            QListWidget::item:hover {
                background-color: #f8fafc;
            }
        """)
        
        card_layout.addWidget(self.lista_ui)
        
        self.aggiorna_lista_dipendenti()

        page_layout.addWidget(title)
        page_layout.addWidget(subtitle)
        page_layout.addSpacing(20)
        page_layout.addWidget(card_widget)

    def aggiorna_lista_dipendenti(self):
        self.lista_ui.clear() # Cancella gli elementi vecchi
        
        if self.interfaccia is None:
            self.lista_ui.addItem("Errore: Backend scollegato.")
            return
            
        dipendenti = self.interfaccia.sistema_dipendenti.get_lista_dipendenti()
        if not dipendenti:
            self.lista_ui.addItem("Nessun dipendente a sistema.")
            return
            
        for dip in dipendenti:
            # Creiamo la riga
            testo = f"👤 {dip.id_dipendente} - {dip.nome} {dip.cognome}     (Stato: {dip.stato.name})"
            self.lista_ui.addItem(testo)

    def switch_page(self, index):
        # Cambia il componente visibile
        self.main_content.setCurrentIndex(index)
        
        # Cambiamo la classe css del bottone attivo (React: className={isActive ? 'active' : ''})
        self.btn_turni.setObjectName("sidebar_btn_active" if index == 0 else "sidebar_btn")
        self.btn_personale.setObjectName("sidebar_btn_active" if index == 1 else "sidebar_btn")
        self.btn_impostazioni.setObjectName("sidebar_btn_active" if index == 2 else "sidebar_btn")
        
        # Forza il ridisegno dei bottoni per ricaricare il nome della classe dal QSS
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
                min-height: 400px;
            }
        """)

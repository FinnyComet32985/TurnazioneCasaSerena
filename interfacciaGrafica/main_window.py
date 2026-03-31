import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QStackedWidget
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, QSize
from path_util import resource_path

# Importiamo le viste
from interfacciaGrafica.views.turni_view import TurniView
from interfacciaGrafica.views.personale_view import PersonaleView
from interfacciaGrafica.views.impostazioni_view import ImpostazioniView


class MainWindow(QMainWindow):
    def __init__(self, sistema_dipendenti, turnazione):
        super().__init__()
        
        # Memorizziamo i sistemi logici
        self.sistema_dipendenti = sistema_dipendenti
        self.turnazione = turnazione
        # Manteniamo il riferimento 'interfaccia' per compatibilità con le sub-viste
        self.interfaccia = self
        
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
        logo_layout.setContentsMargins(0, 0, 0, 0)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Creiamo un QLabel per contenere l'immagine del logo
        logo_label = QLabel()
        pixmap = QPixmap(resource_path("interfacciaGrafica/assets/logo.svg"))
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(180, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)
        
        sidebar_layout.addWidget(logo_container)
        
        # Voce Menu 1 - Personale
        self.btn_personale = QPushButton("  Dipendenti")
        self.btn_personale.setObjectName("sidebar_btn")
        self.btn_personale.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_personale.setIcon(QIcon(resource_path("interfacciaGrafica/assets/people.svg")))
        self.btn_personale.setIconSize(QSize(24, 24))
        self.btn_personale.clicked.connect(lambda: self.switch_page(1))

        # Voce Menu 2 - Turnazione
        self.btn_turni = QPushButton("  Turnazione")
        self.btn_turni.setObjectName("sidebar_btn_active")
        self.btn_turni.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_turni.setIcon(QIcon(resource_path("interfacciaGrafica/assets/calendar.svg")))
        self.btn_turni.setIconSize(QSize(24, 24))
        self.btn_turni.clicked.connect(lambda: self.switch_page(0))

        # Voce Menu 3 - Impostazioni
        self.btn_impostazioni = QPushButton("  Impostazioni")
        self.btn_impostazioni.setObjectName("sidebar_btn")
        self.btn_impostazioni.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_impostazioni.setIcon(QIcon(resource_path("interfacciaGrafica/assets/settings.svg")))
        self.btn_impostazioni.setIconSize(QSize(24, 24))
        self.btn_impostazioni.clicked.connect(lambda: self.switch_page(2))

        sidebar_layout.addWidget(self.btn_turni)
        sidebar_layout.addWidget(self.btn_personale)
        sidebar_layout.addStretch() 
        sidebar_layout.addWidget(self.btn_impostazioni)
        sidebar_layout.addSpacing(20)
        
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

        # Collegamento per la navigazione automatica dalle assenze ai turni
        self.page_personale.navigazioneTurni.connect(self.gestisci_navigazione_turni)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.main_content)
        
        # Inizializza lo stato della navbar (icone e stili) attivando la prima pagina
        self.switch_page(0)
        
    def switch_page(self, index):
        self.main_content.setCurrentIndex(index)
        
        # Aggiornamento dinamico delle icone tramite Painter per feedback visivo
        self.update_navbar_icon(self.btn_turni, resource_path("interfacciaGrafica/assets/calendar.svg"), index == 0)
        self.update_navbar_icon(self.btn_personale, resource_path("interfacciaGrafica/assets/people.svg"), index == 1)
        self.update_navbar_icon(self.btn_impostazioni, resource_path("interfacciaGrafica/assets/settings.svg"), index == 2)

        self.btn_turni.setObjectName("sidebar_btn_active" if index == 0 else "sidebar_btn")
        self.btn_personale.setObjectName("sidebar_btn_active" if index == 1 else "sidebar_btn")
        self.btn_impostazioni.setObjectName("sidebar_btn_active" if index == 2 else "sidebar_btn")
        
        for btn in [self.btn_turni, self.btn_personale, self.btn_impostazioni]:
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
    def gestisci_navigazione_turni(self, data_target):
        """Cambia pagina e sposta la visualizzazione della turnazione alla data specificata."""
        self.switch_page(0)  # Passa alla pagina Turnazione (indice 0)
        self.page_turni.vai_a_data(data_target)

    def update_navbar_icon(self, button, icon_path, is_active):
        """Ricolora l'icona del pulsante usando QPainter in base allo stato attivo/inattivo"""
        color = QColor("#3b82f6") if is_active else QColor("#94a3b8")
        pixmap = QPixmap(icon_path)
        
        if not pixmap.isNull():
            painter = QPainter(pixmap)
            # CompositionMode_SourceIn applica il colore solo dove l'immagine originale non è trasparente
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), color)
            painter.end()
            
            # Imposta l'icona ricolorata e scalata per l'alta risoluzione
            button.setIcon(QIcon(pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))

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
                background-color: #f8fafb;
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

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame,
    QMessageBox, QDialog, QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

class AddDipendenteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Assumi Dipendente")
        self.setFixedWidth(350)
        
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.input_nome = QLineEdit()
        self.input_cognome = QLineEdit()
        
        self.input_nome.setStyleSheet("padding: 8px; border: 1px solid #D1D5DB; border-radius: 4px;")
        self.input_cognome.setStyleSheet("padding: 8px; border: 1px solid #D1D5DB; border-radius: 4px;")

        form_layout.addRow("Nome:", self.input_nome)
        form_layout.addRow("Cognome:", self.input_cognome)
        
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        btn_salva = QPushButton("Salva")
        btn_annulla = QPushButton("Annulla")
        
        btn_salva.setStyleSheet("background-color: #004D99; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        btn_annulla.setStyleSheet("background-color: #E5E7EB; color: #374151; padding: 8px 16px; border-radius: 4px;")

        btn_salva.clicked.connect(self.accept)
        btn_annulla.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_annulla)
        btn_layout.addWidget(btn_salva)
        
        layout.addLayout(btn_layout)
        
    def get_data(self):
        return self.input_nome.text().strip(), self.input_cognome.text().strip()

class DipendenteCard(QFrame):
    delete_clicked = pyqtSignal(int)

    def __init__(self, dipendente):
        super().__init__()
        self.id_dipendente = dipendente.id_dipendente
        self.setObjectName("dipendente_card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedHeight(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)

        # Icon placeholder or Avatar circle
        avatar = QLabel("👤")
        avatar.setFixedSize(44, 44)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet("font-size: 20px; background-color: #F3F4F6; border-radius: 22px;")
        layout.addWidget(avatar)

        info_layout = QVBoxLayout()
        name_label = QLabel(f"{dipendente.nome} {dipendente.cognome}")
        name_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #111827;")
        id_label = QLabel(f"ID: {dipendente.id_dipendente} • Stato: {dipendente.stato.name}")
        id_label.setStyleSheet("color: #6B7280; font-size: 13px;")

        info_layout.addWidget(name_label)
        info_layout.addWidget(id_label)
        info_layout.setSpacing(2)

        layout.addLayout(info_layout)
        layout.addStretch()

        btn_delete = QPushButton("🗑️")
        btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_delete.setFixedSize(36, 36)
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #FCA5A5;
                border-radius: 18px;
                color: #EF4444;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #FEE2E2;
            }
        """)
        btn_delete.clicked.connect(lambda: self.delete_clicked.emit(self.id_dipendente))
        layout.addWidget(btn_delete)

        self.setStyleSheet("""
            #dipendente_card {
                background-color: white;
                border: 1px solid #ECEEEF;
                border-radius: 12px;
            }
            #dipendente_card:hover {
                border: 1px solid #D1D5DB;
            }
        """)

class GenerazioneCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(220)
        self.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #004D99, stop:1 #1565C0);
                border-radius: 16px;
            }
            QLabel {
                color: white;
                background-color: transparent;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                font-weight: bold;
                border: none;
                text-align: left;
                padding: 0;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        icon = QLabel("✨")
        icon.setStyleSheet("font-size: 24px;")
        layout.addWidget(icon)

        title = QLabel("Generazione Automatica")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(title)

        desc = QLabel("Lascia che il sistema calcoli la migliore\nturnazione possibile basandosi sulle\ndisponibilità e le competenze del personale.")
        desc.setStyleSheet("font-size: 14px; margin-top: 5px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addStretch()

        btn = QPushButton("AVVIA GENERAZIONE  →")
        layout.addWidget(btn)

class PersonaleView(QWidget):
    def __init__(self, interfaccia):
        super().__init__()
        self.interfaccia = interfaccia
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        
        # Header Area
        header_layout = QHBoxLayout()
        title_container = QVBoxLayout()
        title = QLabel("Gestione Personale")
        title.setObjectName("page_title")
        subtitle = QLabel("Visualizza e gestisci l'anagrafica dei dipendenti della struttura.")
        subtitle.setObjectName("page_subtitle")
        title_container.addWidget(title)
        title_container.addWidget(subtitle)
        
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        btn_assumi = QPushButton("➕ Assumi Dipendente")
        btn_assumi.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_assumi.setStyleSheet("""
            QPushButton {
                background-color: #004D99;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #003366;
            }
        """)
        btn_assumi.clicked.connect(self.cmd_assumi)
        
        btn_assenze = QPushButton("📅 Visualizza Assenze")
        btn_assenze.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_assenze.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #004D99;
                padding: 12px 24px;
                border-radius: 8px;
                border: 1px solid #004D99;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F0F7FF;
            }
        """)
        btn_assenze.clicked.connect(self.cmd_assenze)

        header_layout.addWidget(btn_assenze)
        header_layout.addWidget(btn_assumi)
        
        main_layout.addLayout(header_layout)

        # Dashboard-like section
        dash_layout = QHBoxLayout()
        self.gen_card = GenerazioneCard()
        dash_layout.addWidget(self.gen_card)
        
        # Right side of dash could be stats
        self.stats_card = QFrame()
        self.stats_card.setObjectName("card_container")
        self.stats_card.setFixedWidth(300)
        stats_layout = QVBoxLayout(self.stats_card)
        stats_layout.setContentsMargins(25, 25, 25, 25)
        
        stats_title = QLabel("Riepilogo")
        stats_title.setStyleSheet("font-weight: bold; color: #6B7280; text-transform: uppercase; font-size: 12px; letter-spacing: 1px;")
        self.label_totale = QLabel("Totale: 0")
        self.label_totale.setStyleSheet("font-size: 24px; font-weight: bold; color: #111827; margin-top: 10px;")
        
        stats_layout.addWidget(stats_title)
        stats_layout.addWidget(self.label_totale)
        stats_layout.addStretch()
        
        dash_layout.addWidget(self.stats_card)
        main_layout.addLayout(dash_layout)
        
        # Cards Area (Scrollable)
        section_label = QLabel("Elenco Dipendenti")
        section_label.setStyleSheet("font-weight: bold; color: #111827; font-size: 18px;")
        main_layout.addWidget(section_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: transparent;")
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(0, 0, 10, 0)
        self.cards_layout.setSpacing(12)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)
        
        self.aggiorna_lista()

    def aggiorna_lista(self):
        # Clear existing cards
        for i in reversed(range(self.cards_layout.count())):
            widget = self.cards_layout.itemAt(i).widget()
            if isinstance(widget, DipendenteCard):
                widget.setParent(None)

        if not self.interfaccia:
            return
            
        dipendenti = self.interfaccia.sistema_dipendenti.get_lista_dipendenti()
        self.label_totale.setText(f"Totale: {len(dipendenti)}")
        for dip in dipendenti:
            card = DipendenteCard(dip)
            card.delete_clicked.connect(self.cmd_licenzia)
            self.cards_layout.addWidget(card)
            
    def cmd_assumi(self):
        dialog = AddDipendenteDialog(self)
        if dialog.exec():
            nome, cognome = dialog.get_data()
            if nome and cognome:
                self.interfaccia.sistema_dipendenti.assumi_dipendente(nome, cognome)
                self.aggiorna_lista()

    def cmd_licenzia(self, id_dip):
        confirm = QMessageBox.question(self, "Conferma Licenziamento", f"Sei sicuro di voler licenziare il dipendente #{id_dip}?")
        if confirm == QMessageBox.StandardButton.Yes:
            success = self.interfaccia.sistema_dipendenti.rimuovi_dipendente(id_dip)
            if success:
                self.aggiorna_lista()
            else:
                QMessageBox.critical(self, "Errore", "Impossibile rimuovere il dipendente.")

    def cmd_assenze(self):
        QMessageBox.information(self, "Info", "Modulo assenze in via di sviluppo.")

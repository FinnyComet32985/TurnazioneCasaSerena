from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton, 
    QMessageBox, QDialog, QLineEdit, QFormLayout
)
from PyQt6.QtCore import Qt

class AddDipendenteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Assumi Dipendente")
        self.setFixedWidth(300)
        
        layout = QFormLayout(self)
        self.input_nome = QLineEdit()
        self.input_cognome = QLineEdit()
        
        layout.addRow("Nome:", self.input_nome)
        layout.addRow("Cognome:", self.input_cognome)
        
        btn_layout = QHBoxLayout()
        btn_salva = QPushButton("Salva")
        btn_annulla = QPushButton("Annulla")
        
        btn_salva.clicked.connect(self.accept)
        btn_annulla.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_salva)
        btn_layout.addWidget(btn_annulla)
        
        layout.addRow(btn_layout)
        
    def get_data(self):
        return self.input_nome.text().strip(), self.input_cognome.text().strip()

class PersonaleView(QWidget):
    def __init__(self, interfaccia):
        super().__init__()
        self.interfaccia = interfaccia
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel("Gestione Personale")
        title.setObjectName("page_title")
        subtitle = QLabel("Visualizza e gestisci l'anagrafica dei dipendenti")
        subtitle.setObjectName("page_subtitle")
        
        # Area Principale (Lista a sinistra, Controlli a destra)
        main_area = QHBoxLayout()
        
        # --- Lista ---
        list_container = QWidget()
        list_container.setObjectName("card_container")
        list_layout = QVBoxLayout(list_container)
        
        self.lista_ui = QListWidget()
        self.lista_ui.setStyleSheet("QListWidget { border: none; background-color: transparent; font-size: 16px; color: #0f172a; } QListWidget::item { padding: 12px; border-bottom: 1px solid #f1f5f9; } QListWidget::item:hover { background-color: #f8fafc; } QListWidget::item:selected { background-color: #e2e8f0; color: #000; }")
        
        list_layout.addWidget(self.lista_ui)
        
        # --- Controlli (Pannello destro) ---
        controls_layout = QVBoxLayout()
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.btn_assumi = QPushButton("➕ Assumi Dipendente")
        self.btn_licenzia = QPushButton("🗑️ Licenzia Selezionato")
        self.btn_assenze = QPushButton("📅 Visualizza Assenze")
        
        # Stili base per i bottoni
        btn_style = "padding: 10px; font-size: 14px; background-color: #3b82f6; color: white; border-radius: 4px;"
        btn_style_danger = "padding: 10px; font-size: 14px; background-color: #ef4444; color: white; border-radius: 4px;"
        btn_style_outline = "padding: 10px; font-size: 14px; background-color: transparent; color: #3b82f6; border: 1px solid #3b82f6; border-radius: 4px;"
        
        self.btn_assumi.setStyleSheet(btn_style)
        self.btn_assenze.setStyleSheet(btn_style_outline)
        self.btn_licenzia.setStyleSheet(btn_style_danger)
        
        self.btn_assumi.clicked.connect(self.cmd_assumi)
        self.btn_licenzia.clicked.connect(self.cmd_licenzia)
        self.btn_assenze.clicked.connect(self.cmd_assenze)
        
        controls_layout.addWidget(self.btn_assumi)
        controls_layout.addWidget(self.btn_assenze)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(self.btn_licenzia)
        
        main_area.addWidget(list_container, stretch=2)
        main_area.addSpacing(20)
        main_area.addLayout(controls_layout, stretch=1)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addLayout(main_area)
        
        self.aggiorna_lista()

    def aggiorna_lista(self):
        self.lista_ui.clear()
        if not self.interfaccia:
            return
            
        dipendenti = self.interfaccia.sistema_dipendenti.get_lista_dipendenti()
        for dip in dipendenti:
            testo = f"👤 {dip.id_dipendente} - {dip.nome} {dip.cognome}     (Stato: {dip.stato.name})"
            item = QListWidgetItem(testo)
            item.setData(Qt.ItemDataRole.UserRole, dip.id_dipendente)
            self.lista_ui.addItem(item)
            
    def cmd_assumi(self):
        dialog = AddDipendenteDialog(self)
        if dialog.exec():
            nome, cognome = dialog.get_data()
            if nome and cognome:
                # Chiama direttamente il sistema ignorando l'input console di interfacciaDirigente
                self.interfaccia.sistema_dipendenti.assumi_dipendente(nome, cognome)
                self.aggiorna_lista()

    def cmd_licenzia(self):
        selezionati = self.lista_ui.selectedItems()
        if not selezionati:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima un dipendente dalla lista.")
            return
            
        id_dip = selezionati[0].data(Qt.ItemDataRole.UserRole)
        confirm = QMessageBox.question(self, "Conferma Licenziamento", f"Sei sicuro di voler licenziare il dipendente #{id_dip}?")
        if confirm == QMessageBox.StandardButton.Yes:
            success = self.interfaccia.sistema_dipendenti.rimuovi_dipendente(id_dip)
            if success:
                self.aggiorna_lista()
            else:
                QMessageBox.critical(self, "Errore", "Impossibile rimuovere il dipendente.")
                
    def cmd_assenze(self):
        QMessageBox.information(self, "Info", "Modulo assenze in via di sviluppo.")

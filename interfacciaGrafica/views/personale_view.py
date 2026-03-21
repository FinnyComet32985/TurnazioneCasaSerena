from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QPushButton, 
    QMessageBox, QDialog, QLineEdit, QFormLayout,
    QComboBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt
from sistemaDipendenti.assenzaProgrammata import TipoAssenza
from datetime import datetime

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

class ModificaDatiDialog(QDialog):
    def __init__(self, dipendente, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Modifica Dati - {dipendente.nome} {dipendente.cognome}")
        
        layout = QFormLayout(self)
        
        self.ferie_spin = QDoubleSpinBox()
        self.ferie_spin.setRange(-1000, 1000)
        self.ferie_spin.setValue(dipendente.ferie_rimanenti)
        
        self.rol_spin = QDoubleSpinBox()
        self.rol_spin.setRange(-1000, 1000)
        self.rol_spin.setValue(dipendente.rol_rimanenti)
        
        self.banca_ore_spin = QDoubleSpinBox()
        self.banca_ore_spin.setRange(-1000, 1000)
        self.banca_ore_spin.setValue(dipendente.banca_ore)
        
        layout.addRow("Ferie Rimanenti (giorni):", self.ferie_spin)
        layout.addRow("ROL Rimanenti (ore):", self.rol_spin)
        layout.addRow("Banca Ore:", self.banca_ore_spin)
        
        btn_layout = QHBoxLayout()
        btn_salva = QPushButton("Salva")
        btn_annulla = QPushButton("Annulla")
        btn_salva.clicked.connect(self.accept)
        btn_annulla.clicked.connect(self.reject)
        btn_layout.addWidget(btn_salva)
        btn_layout.addWidget(btn_annulla)
        
        layout.addRow(btn_layout)
        
    def get_data(self):
        return self.ferie_spin.value(), self.rol_spin.value(), self.banca_ore_spin.value()

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
        
        # Area Principale (Lista a sinistra, Dettagli a destra)
        main_area = QHBoxLayout()
        
        # --- Lista Dipendenti ---
        list_container = QWidget()
        list_container.setObjectName("card_container")
        list_container.setStyleSheet("background-color: white; border-radius: 8px; border: 1px solid #cbd5e1;")
        list_layout = QVBoxLayout(list_container)
        
        self.lista_ui = QListWidget()
        self.lista_ui.setStyleSheet("QListWidget { border: none; background-color: transparent; font-size: 16px; color: #0f172a; } QListWidget::item { padding: 12px; border-bottom: 1px solid #f1f5f9; } QListWidget::item:hover { background-color: #f8fafc; } QListWidget::item:selected { background-color: #e2e8f0; color: #000; }")
        self.lista_ui.currentItemChanged.connect(self.update_details_panel)
        
        btn_assumi = QPushButton("➕ Assumi Dipendente")
        btn_assumi.setStyleSheet("padding: 10px; font-size: 14px; background-color: #3b82f6; color: white; border-radius: 4px;")
        btn_assumi.clicked.connect(self.cmd_assumi)
        
        list_layout.addWidget(btn_assumi)
        list_layout.addWidget(self.lista_ui)
        
        # --- Pannello Dettagli (destra) ---
        details_container = QWidget()
        details_container.setObjectName("card_container")
        details_container.setStyleSheet("QWidget { background-color: white; border-radius: 8px; border: 1px solid #cbd5e1; color: #0f172a; }")
        details_layout = QVBoxLayout(details_container)
        
        self.details_title = QLabel("Seleziona un dipendente")
        self.details_title.setObjectName("details_title")
        self.details_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Contenitore che mostriamo/nascondiamo
        self.details_content = QWidget()
        details_content_layout = QVBoxLayout(self.details_content)
        details_content_layout.setContentsMargins(0,0,0,0)
        
        # Dati numerici
        dati_layout = QFormLayout()
        self.lbl_ferie = QLabel()
        self.lbl_rol = QLabel()
        self.lbl_banca_ore = QLabel()
        dati_layout.addRow("Ferie Rimanenti (giorni):", self.lbl_ferie)
        dati_layout.addRow("ROL Rimanenti (ore):", self.lbl_rol)
        dati_layout.addRow("Banca Ore (ore):", self.lbl_banca_ore)
        
        # Lista Assenze
        self.assenze_list_ui = QListWidget()
        self.assenze_list_ui.setStyleSheet("QListWidget { border: 1px solid #e2e8f0; border-radius: 4px; padding: 5px; color: #0f172a; background-color: white; }")
        
        # Bottoni Azioni
        actions_layout = QHBoxLayout()
        self.btn_modifica_dati = QPushButton("📝 Modifica Dati")
        self.btn_modifica_dati.setStyleSheet("background-color: #3b82f6; color: white; padding: 8px; border-radius: 4px; border: none;")
        self.btn_aggiungi_assenza = QPushButton("📅 Aggiungi Assenza")
        self.btn_aggiungi_assenza.setStyleSheet("background-color: #3b82f6; color: white; padding: 8px; border-radius: 4px; border: none;")
        self.btn_licenzia = QPushButton("🗑️ Licenzia")
        self.btn_licenzia.setStyleSheet("background-color: #ef4444; color: white; padding: 8px; border-radius: 4px; border: none;")
        
        self.btn_modifica_dati.clicked.connect(self.cmd_modifica_dati)
        self.btn_aggiungi_assenza.clicked.connect(self.cmd_aggiungi_assenza)
        self.btn_licenzia.clicked.connect(self.cmd_licenzia)
        
        actions_layout.addWidget(self.btn_modifica_dati)
        actions_layout.addWidget(self.btn_aggiungi_assenza)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_licenzia)
        
        details_content_layout.addLayout(dati_layout)
        details_content_layout.addSpacing(20)
        details_content_layout.addWidget(QLabel("Assenze Programmate:"))
        details_content_layout.addWidget(self.assenze_list_ui)
        details_content_layout.addSpacing(10)
        details_content_layout.addLayout(actions_layout)
        
        details_layout.addWidget(self.details_title)
        details_layout.addWidget(self.details_content)
        
        main_area.addWidget(list_container, stretch=1)
        main_area.addWidget(details_container, stretch=2)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addLayout(main_area)
        
        self.aggiorna_lista()
        self.update_details_panel(None, None)

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
            
    def update_details_panel(self, current_item, previous_item):
        if not current_item:
            self.details_title.setText("Seleziona un dipendente")
            self.details_content.hide()
            return
            
        id_dip = current_item.data(Qt.ItemDataRole.UserRole)
        dip = self.interfaccia.sistema_dipendenti.get_dipendente(id_dip)
        
        if not dip:
            self.details_title.setText("Dipendente non trovato")
            self.details_content.hide()
            return
            
        self.details_title.setText(f"Dettagli di {dip.nome} {dip.cognome}")
        self.details_content.show()
        
        # Aggiorna dati
        self.lbl_ferie.setText(f"{dip.ferie_rimanenti:.2f}")
        self.lbl_rol.setText(f"{dip.rol_rimanenti:.2f}")
        self.lbl_banca_ore.setText(f"{dip.banca_ore:.2f}")
        
        # Aggiorna lista assenze
        self.assenze_list_ui.clear()
        for assenza in dip.assenze_programmate:
            dt_inizio = datetime.strptime(assenza.data_inizio, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%y %H:%M")
            dt_fine = datetime.strptime(assenza.data_fine, "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%y %H:%M")
            testo = f"[{assenza.tipo}] Dal {dt_inizio} al {dt_fine}"
            self.assenze_list_ui.addItem(testo)
            
    def cmd_assumi(self):
        dialog = AddDipendenteDialog(self)
        if dialog.exec():
            nome, cognome = dialog.get_data()
            if nome and cognome:
                # Chiama direttamente il sistema ignorando l'input console di interfacciaDirigente
                self.interfaccia.sistema_dipendenti.assumi_dipendente(nome, cognome)
                self.aggiorna_lista()
    
    def get_selected_dip_id(self):
        selezionati = self.lista_ui.selectedItems()
        if not selezionati:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima un dipendente dalla lista.")
            return None
        return selezionati[0].data(Qt.ItemDataRole.UserRole)

    def cmd_licenzia(self):
        id_dip = self.get_selected_dip_id()
        if id_dip is None: return
        
        confirm = QMessageBox.question(self, "Conferma Licenziamento", f"Sei sicuro di voler licenziare il dipendente #{id_dip}?")
        if confirm == QMessageBox.StandardButton.Yes:
            success = self.interfaccia.sistema_dipendenti.rimuovi_dipendente(id_dip)
            if success:
                self.aggiorna_lista()
                self.update_details_panel(None, None)
            else:
                QMessageBox.critical(self, "Errore", "Impossibile rimuovere il dipendente.")
                
    def cmd_modifica_dati(self):
        id_dip = self.get_selected_dip_id()
        if id_dip is None: return
        
        dip = self.interfaccia.sistema_dipendenti.get_dipendente(id_dip)
        dialog = ModificaDatiDialog(dip, self)
        
        if dialog.exec():
            ferie, rol, banca_ore = dialog.get_data()
            success = self.interfaccia.sistema_dipendenti.modifica_dipendente(
                id_dip, dip.nome, dip.cognome, ferie, rol, banca_ore
            )
            if success:
                self.update_details_panel(self.lista_ui.currentItem(), None)
            else:
                QMessageBox.critical(self, "Errore", "Impossibile modificare i dati.")

    def cmd_aggiungi_assenza(self):
        id_dip = self.get_selected_dip_id()
        if id_dip is None: return
        
        dialog = AddAssenzaDialog(self)
        if dialog.exec():
            tipo, dt_inizio, dt_fine = dialog.get_data()
            if tipo and dt_inizio and dt_fine:
                str_inizio = dt_inizio.strftime("%Y-%m-%d %H:%M:%S")
                str_fine = dt_fine.strftime("%Y-%m-%d %H:%M:%S")
                
                success = self.interfaccia.sistema_dipendenti.aggiungi_assenza(
                    id_dip, tipo, str_inizio, str_fine
                )
                if success:
                    self.update_details_panel(self.lista_ui.currentItem(), None)
                else:
                    QMessageBox.critical(self, "Errore", "Impossibile aggiungere l'assenza.")
            else:
                QMessageBox.warning(self, "Dati non validi", "Il formato della data non è corretto.")

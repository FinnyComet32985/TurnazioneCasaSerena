from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QDialog, QLineEdit, QFormLayout,
    QComboBox, QDoubleSpinBox
)
from PyQt6.QtGui import QPixmap, QIcon
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
        
        title = QLabel("Gestione Dipendenti")
        title.setObjectName("page_title")
        subtitle = QLabel("Gestisci i dipendenti e monitora i rersidui di ferie e ROL")
        subtitle.setObjectName("page_subtitle")
        
        # --- HEADER CARDS ---
        stats_container = QWidget()
        stats_layout = QHBoxLayout(stats_container)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(20)

        # Creazione Card (Salviamo le label dei valori in self per aggiornarle dopo)
        card_totale, self.lbl_tot_dip = self.create_stat_card("TOTALE DIPENDENTI", "-", "#3b82f6", "./interfacciaGrafica/assets/id-card.svg")
        card_ferie, self.lbl_tot_ferie = self.create_stat_card("FERIE IN CORSO", "-", "#f59e0b", "./interfacciaGrafica/assets/earth.svg")
        card_cert, self.lbl_tot_cert = self.create_stat_card("PERSONALE IN CERTIFICATO", "-", "#ef4444", "./interfacciaGrafica/assets/fitness.svg")

        stats_layout.addWidget(card_totale)
        stats_layout.addWidget(card_ferie)
        stats_layout.addWidget(card_cert)

        # --- HEADER ACTIONS ---
        action_bar = QWidget()
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(0, 10, 0, 10)
        
        # --- Search Widget ---
        search_container = QWidget()
        search_container.setObjectName("search_container_custom") # Assegno ID univoco per evitare ereditarietà indesiderata
        search_container.setFixedWidth(300)
        search_container.setStyleSheet("""
            #search_container_custom {
                background-color: white;
                border: 1px solid #cbd5e1; 
                border-radius: 4px;
            }
        """)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(8, 0, 0, 0)
        search_layout.setSpacing(6)

        search_icon = QLabel()
        search_icon.setPixmap(QPixmap("./interfacciaGrafica/assets/search.svg").scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cerca dipendente...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 0px; 
                border: none;
                background-color: transparent;
                color: #0f172a;
            }
        """)
        self.search_input.textChanged.connect(self.aggiorna_tabella)
        
        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_input)
        
        self.btn_assumi = QPushButton(" Assumi Dipendente")
        self.btn_assumi.setIcon(QIcon("./interfacciaGrafica/assets/person-add.svg"))
        self.btn_assumi.setStyleSheet("""
            QPushButton {
                padding: 8px 16px; 
                font-size: 14px; 
                border: none;
                background-color: #3b82f6; 
                color: white; 
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        self.btn_assumi.clicked.connect(self.cmd_assumi)
        
        action_layout.addWidget(search_container)
        action_layout.addStretch()
        action_layout.addWidget(self.btn_assumi)
        
        # --- TABELLA DIPENDENTI ---
        self.table = QTableWidget()
        headers = ["Nome", "Cognome", "Ferie (gg)", "ROL (h)", "Banca Ore", "Stato", ""]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(5, 150)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(6, 60)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False) # Rimuove griglia (linee verticali)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.verticalHeader().setDefaultSectionSize(60) # Aumenta altezza righe per ospitare la pillola
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.cellClicked.connect(self.on_row_clicked)
        
        # Stile Tabella
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 15px;
                border-bottom: 1px solid #f1f5f9;
                color: #334155;
                font-size: 15px;
            }
            QTableWidget::item:selected {
                background-color: #f1f5f9;
                color: #0f172a;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                padding: 15px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                font-weight: bold;
                color: #64748b;
                text-align: left;
                font-size: 16px;
            }
        """)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addWidget(stats_container) # Aggiungo le card statistiche
        layout.addSpacing(10)
        layout.addWidget(action_bar)
        layout.addWidget(self.table)
        
        self.aggiorna_tabella()
        self.aggiorna_statistiche()

    def showEvent(self, event):
        """Metodo chiamato automaticamente quando la pagina diventa visibile"""
        super().showEvent(event)
        self.aggiorna_tabella()
        self.aggiorna_statistiche()

    def aggiorna_statistiche(self):
        tot_dip, tot_ferie, tot_cert = self.interfaccia.sistema_dipendenti.get_statistiche_oggi()
        self.lbl_tot_dip.setText(str(tot_dip))
        self.lbl_tot_ferie.setText(str(tot_ferie))
        self.lbl_tot_cert.setText(str(tot_cert))

    def create_stat_card(self, titolo, valore, colore_bordo, icon_path):
        """Crea un widget stile Card"""
        card = QWidget()
        card.setObjectName("stat_card")
        # Stile inline per la card specifica
        card.setStyleSheet(f"""
            QWidget#stat_card {{
                background-color: white;
                border-radius: 8px;
                border-left: 5px solid {colore_bordo};
                border-top: 1px solid #e2e8f0;
                border-right: 1px solid #e2e8f0;
                border-bottom: 1px solid #e2e8f0;
            }}
        """)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)
        
        lbl_icona = QLabel()
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl_icona.setPixmap(pixmap)
        lbl_icona.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        lbl_titolo = QLabel(titolo)
        lbl_titolo.setStyleSheet("color: #64748b; font-size: 16px; font-weight: 600;")
        
        lbl_valore = QLabel(valore)
        lbl_valore.setStyleSheet("color: #0f172a; font-size: 24px; font-weight: bold;")
        
        text_layout.addWidget(lbl_titolo)
        text_layout.addWidget(lbl_valore)
        
        card_layout.addLayout(text_layout)
        card_layout.addStretch()
        card_layout.addWidget(lbl_icona)
        
        return card, lbl_valore

    def aggiorna_tabella(self):
        self.table.setRowCount(0)
        dipendenti = self.interfaccia.sistema_dipendenti.get_lista_dipendenti()
        search_text = self.search_input.text().lower()
        
        row = 0
        for dip in dipendenti:
            # Filtro ricerca
            if search_text and (search_text not in dip.nome.lower() and search_text not in dip.cognome.lower()):
                continue
                
            self.table.insertRow(row)
            
            item_nome = QTableWidgetItem(dip.nome)
            item_nome.setData(Qt.ItemDataRole.UserRole, dip.id_dipendente)
            self.table.setItem(row, 0, item_nome)
            self.table.setItem(row, 1, QTableWidgetItem(dip.cognome))
            self.table.setItem(row, 2, QTableWidgetItem(f"{dip.ferie_rimanenti:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{dip.rol_rimanenti:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{dip.banca_ore:.2f}"))
            
            # Badge Stato (opzionale: colorato)
            self.table.setItem(row, 5, QTableWidgetItem("")) # Item placeholder necessario per coerenza riga
            self.table.setCellWidget(row, 5, self.create_status_pill(dip.stato.name))
            
            # Indicatore navigazione
            self.table.setItem(row, 6, QTableWidgetItem("")) # Placeholder
            self.table.setCellWidget(row, 6, self.create_arrow_icon())
            
            row += 1

    def create_status_pill(self, stato):
        widget = QWidget()
        widget.setStyleSheet("background-color: transparent;") # Sfondo trasparente per il container
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl = QLabel(stato)
        lbl.setFixedSize(120, 30) # Dimensioni ottimizzate
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if stato == "ASSUNTO":
            lbl.setStyleSheet("""
                QLabel {
                    background-color: #dcfce7; 
                    border: 1px solid #a7f3d0;
                    color: #166534; 
                    border-radius: 15px;
                    font-weight: bold;
                    font-size: 13px;
                }
            """)
        else:
            lbl.setStyleSheet("""
                QLabel {
                    background-color: #f1f5f9; 
                    border: 1px solid #e2e8f0;
                    color: #64748b; 
                    border-radius: 15px;
                    font-weight: bold;
                    font-size: 13px;
                }
            """)
        
        layout.addWidget(lbl)
        return widget

    def create_arrow_icon(self):
        widget = QWidget()
        widget.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0,0,0,0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel()
        pixmap = QPixmap("./interfacciaGrafica/assets/arrow-forward.svg")
        if not pixmap.isNull():
            icon_label.setPixmap(pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        layout.addWidget(icon_label)
        return widget

    def on_row_clicked(self, row, col):
        id_dip = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.apri_dettaglio_dipendente(id_dip)

    def cmd_assumi(self):
        dialog = AddDipendenteDialog(self)
        if dialog.exec():
            nome, cognome = dialog.get_data()
            if nome and cognome:
                # Chiama direttamente il sistema ignorando l'input console di interfacciaDirigente
                self.interfaccia.sistema_dipendenti.assumi_dipendente(nome, cognome)
                self.aggiorna_tabella()
                self.aggiorna_statistiche()
    
    def apri_dettaglio_dipendente(self, id_dipendente):
        """Apre la pagina di dettaglio del dipendente (Da implementare in futuro)"""
        QMessageBox.information(self, "In lavorazione", f"La pagina di gestione del dipendente {id_dipendente} sarà disponibile a breve.")

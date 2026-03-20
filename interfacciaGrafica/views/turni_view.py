from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, 
    QSpinBox, QHeaderView, QMessageBox, QComboBox, QDialog
)
from PyQt6.QtCore import Qt
from datetime import datetime, date

# Importiamo TipoFascia per accedere ai riferimenti dei turni
from sistemaTurnazione.fasciaOraria import TipoFascia

class AssignTurnoDialog(QDialog):
    def __init__(self, dipendenti, dt_turno, tipo_fascia, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Assegna Turno - {dt_turno} ({tipo_fascia})")
        self.setFixedWidth(350)
        self.id_scelto = None
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Seleziona il Dipendente:"))
        self.combo = QComboBox()
        self.combo.setStyleSheet("color: #0f172a; background-color: white; border: 1px solid #cbd5e1; padding: 4px;")
        for dip in dipendenti:
            # Opzionale: filtrare solo quelli 'ASSUNTI'
            if dip.stato.name == "ASSUNTO":
                self.combo.addItem(f"{dip.nome} {dip.cognome}", userData=dip.id_dipendente)
        layout.addWidget(self.combo)
        
        btn_layout = QHBoxLayout()
        btn_salva = QPushButton("Assegna")
        btn_annulla = QPushButton("Annulla")
        btn_salva.clicked.connect(self.accept)
        btn_annulla.clicked.connect(self.reject)
        btn_layout.addWidget(btn_salva)
        btn_layout.addWidget(btn_annulla)
        
        layout.addLayout(btn_layout)
        
    def accept(self):
        self.id_scelto = self.combo.currentData()
        super().accept()

class TurniView(QWidget):
    def __init__(self, interfaccia):
        super().__init__()
        self.interfaccia = interfaccia
        self.fasce_disponibili = [TipoFascia.MATTINA, TipoFascia.POMERIGGIO, TipoFascia.NOTTE, TipoFascia.RIPOSO]
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel("Turnazione Settimanale")
        title.setObjectName("page_title")
        subtitle = QLabel("Gestisci liberamente i turni compilando le celle settimanali.")
        subtitle.setObjectName("page_subtitle")
        
        # --- HEADER (Input Settimana e Anno) ---
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Anno:"))
        self.spin_anno = QSpinBox()
        self.spin_anno.setStyleSheet("color: #0f172a; background-color: white; border: 1px solid #cbd5e1; padding: 4px;")
        self.spin_anno.setRange(2020, 2050)
        self.spin_anno.setValue(datetime.now().year)
        header_layout.addWidget(self.spin_anno)
        
        header_layout.addWidget(QLabel("Settimana:"))
        self.spin_sett = QSpinBox()
        self.spin_sett.setStyleSheet("color: #0f172a; background-color: white; border: 1px solid #cbd5e1; padding: 4px;")
        self.spin_sett.setRange(1, 53)
        self.spin_sett.setValue(datetime.now().isocalendar()[1])
        header_layout.addWidget(self.spin_sett)
        
        header_layout.addStretch()
        
        # Listener per ricaricare in tempo reale
        self.spin_anno.valueChanged.connect(self.aggiorna_tabella)
        self.spin_sett.valueChanged.connect(self.aggiorna_tabella)
        
        # --- TABELLA (O Empty State) ---
        self.body_container = QWidget()
        self.body_layout = QVBoxLayout(self.body_container)
        self.body_layout.setContentsMargins(0, 20, 0, 0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.fasce_disponibili))
        self.table.setHorizontalHeaderLabels([f.value for f in self.fasce_disponibili])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.cellClicked.connect(self.on_cell_clicked)
        
        # --- EMPTY STATE CONTAINER ---
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_label = QLabel("Nessun turno trovato per questa settimana.")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_genera = QPushButton("✨ Genera Turni (A.I.)")
        btn_crea_zero = QPushButton("📝 Crea da zero (Svuota Tabella)")
        btn_genera.setFixedWidth(250)
        btn_crea_zero.setFixedWidth(250)
        
        btn_genera.setStyleSheet("padding: 10px; background-color: #6366f1; color: white; border-radius: 4px; font-weight: bold;")
        btn_crea_zero.setStyleSheet("padding: 10px; background-color: #10b981; color: white; border-radius: 4px; font-weight: bold;")
        
        btn_genera.clicked.connect(self.genera_turni_auto)
        btn_crea_zero.clicked.connect(self.crea_da_zero)
        
        btns_hlayout = QHBoxLayout()
        btns_hlayout.addStretch()
        btns_hlayout.addWidget(btn_genera)
        btns_hlayout.addWidget(btn_crea_zero)
        btns_hlayout.addStretch()
        
        empty_layout.addStretch()
        empty_layout.addWidget(empty_label)
        empty_layout.addSpacing(20)
        empty_layout.addLayout(btns_hlayout)
        empty_layout.addStretch()
        
        self.body_layout.addWidget(self.table)
        self.body_layout.addWidget(self.empty_widget)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(header_layout)
        layout.addWidget(self.body_container, stretch=1)
        
        self.aggiorna_tabella()
        
    def aggiorna_tabella(self):
        anno = self.spin_anno.value()
        settimana = self.spin_sett.value()
        
        settimana_dict = self.interfaccia.turnazione.get_turnazione_settimana((anno, settimana))
        
        # Se la settimana non ha alcun turno, mostriamo i bottoni "crea" / "genera"
        if not settimana_dict:
            self.table.hide()
            self.empty_widget.show()
        else:
            self.empty_widget.hide()
            self.table.show()
            self.renderizza_tabella(settimana_dict)
            
    def renderizza_tabella(self, settimana_dict):
        # Mettiamo i giorni in ordine
        date_ordinari = sorted(list(settimana_dict.keys()))
        self.table.setRowCount(len(date_ordinari))
        self.table.setVerticalHeaderLabels([d.strftime("%A %d/%m") for d in date_ordinari])
        
        self.date_rows = date_ordinari
        
        for row, dt_turno in enumerate(date_ordinari):
            fasce_giorno = settimana_dict[dt_turno]
            
            for col, tipo_fascia in enumerate(self.fasce_disponibili):
                if tipo_fascia in fasce_giorno:
                    fascia = fasce_giorno[tipo_fascia]
                    assegnati = ", ".join([f"{a.dipendente.nome} {a.dipendente.cognome}" for a in fascia.assegnazioni])
                    testo = assegnati if assegnati else "+ Vuoto"
                else:
                    testo = "+ Vuoto" 

                item = QTableWidgetItem(testo)
                # Stile testuale per far capire che è cliccabile
                if testo == "+ Vuoto":
                    item.setForeground(Qt.GlobalColor.gray)
                else:
                    item.setForeground(Qt.GlobalColor.black)
                    item.setBackground(Qt.GlobalColor.cyan)
                    
                item.setFlags(Qt.ItemFlag.ItemIsEnabled) 
                
                self.table.setItem(row, col, item)

    def on_cell_clicked(self, row, col):
        tipo_fascia = self.fasce_disponibili[col]
        dt_turno = self.date_rows[row]
        item = self.table.item(row, col)
        
        if item: # Rimosso il limite '+ Vuoto', ora puoi cliccare una cella piena per aggiungere dipendenti
            dipendenti = self.interfaccia.sistema_dipendenti.get_lista_dipendenti()
            dialog = AssignTurnoDialog(dipendenti, dt_turno, tipo_fascia.value, self)
            if dialog.exec() and dialog.id_scelto is not None:
                # Esegui assegnazione (per ora Piano=0, Jolly=False, Breve=False)
                try:
                    self.interfaccia.turnazione.assegna_turno(
                        self.interfaccia.sistema_dipendenti, 
                        dialog.id_scelto, 
                        dt_turno, 
                        tipo_fascia, 
                        0, False, False
                    )
                    self.aggiorna_tabella()
                except Exception as e:
                    QMessageBox.warning(self, "Errore", f"Impossibile assegnare: {str(e)}")
                    
    def crea_da_zero(self):
        anno = self.spin_anno.value()
        settimana = self.spin_sett.value()
        
        # Generiamo le 7 date per quella settimana ISO!
        giorni = [date.fromisocalendar(anno, settimana, i) for i in range(1, 8)]
        
        for giorno in giorni:
            for fascia in self.fasce_disponibili:
                # Aggiungiamo i contenitori a database per la tabella
                self.interfaccia.turnazione.add_turno(giorno, fascia)
                
        # Ricarichiamo
        self.aggiorna_tabella()
        
    def genera_turni_auto(self):
        QMessageBox.information(self, "Coming Soon", "Questa funzionalità applicherà algoritmi per generare tutti i turni.")

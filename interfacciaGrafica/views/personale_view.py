from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QLineEdit,
    QMessageBox, QDialog, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

class AddDipendenteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aggiungi Dipendente")
        self.setFixedWidth(350)
        self.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()
        self.input_nome = QLineEdit()
        self.input_cognome = QLineEdit()
        
        edit_style = "padding: 8px; border: 1px solid #D1D5DB; border-radius: 4px;"
        self.input_nome.setStyleSheet(edit_style)
        self.input_cognome.setStyleSheet(edit_style)

        form_layout.addRow("Nome:", self.input_nome)
        form_layout.addRow("Cognome:", self.input_cognome)
        
        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        btn_salva = QPushButton("Salva")
        btn_annulla = QPushButton("Annulla")
        
        btn_salva.setStyleSheet("background-color: #004D99; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;")
        btn_annulla.setStyleSheet("background-color: #F3F4F6; color: #374151; padding: 8px 16px; border-radius: 4px;")

        btn_salva.clicked.connect(self.accept)
        btn_annulla.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_annulla)
        btn_layout.addWidget(btn_salva)
        
        layout.addLayout(btn_layout)
        
    def get_data(self):
        return self.input_nome.text().strip(), self.input_cognome.text().strip()

class StatsCard(QFrame):
    def __init__(self, title, value, icon_text, accent_color="#004D99", sub_value=None):
        super().__init__()
        self.setFixedWidth(280)
        self.setFixedHeight(120)
        self.setObjectName("stats_card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        header = QHBoxLayout()
        title_lbl = QLabel(title.upper())
        title_lbl.setStyleSheet(f"color: {accent_color}; font-weight: 800; font-size: 11px; letter-spacing: 0.5px;")
        header.addWidget(title_lbl)
        header.addStretch()
        layout.addLayout(header)

        content = QHBoxLayout()
        self.val_lbl = QLabel(str(value))
        self.val_lbl.setStyleSheet("font-size: 32px; font-weight: bold; color: #111827;")
        content.addWidget(self.val_lbl)

        if sub_value:
            sub_lbl = QLabel(sub_value)
            sub_lbl.setStyleSheet("background-color: #DCFCE7; color: #15803D; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: bold;")
            content.addWidget(sub_lbl)

        content.addStretch()

        icon_lbl = QLabel(icon_text)
        icon_lbl.setStyleSheet(f"color: {accent_color}; font-size: 20px;")
        content.addWidget(icon_lbl)

        layout.addLayout(content)

        self.setStyleSheet(f"""
            #stats_card {{
                background-color: white;
                border-radius: 8px;
                border-top: 3px solid {accent_color};
            }}
        """)

class DipendenteRow(QFrame):
    menu_clicked = pyqtSignal(int)
    clicked = pyqtSignal(int)

    def __init__(self, dipendente, selected=False):
        super().__init__()
        self.id_dipendente = dipendente.id_dipendente
        self.selected = selected
        self.setObjectName("row_card")
        self.setFixedHeight(70)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(25, 0, 25, 0)

        # Columns based on mockup
        self.add_col(layout, dipendente.nome, 120, bold=True)
        self.add_col(layout, dipendente.cognome, 120, bold=True)
        self.add_col(layout, f"<span style='color: #004D99; font-weight: bold;'>{int(dipendente.ferie_rimanenti)}</span> <span style='color: #94A3B8;'>gg</span>", 140)
        self.add_col(layout, f"<span style='color: #004D99; font-weight: bold;'>{int(dipendente.rol_rimanenti)}</span> <span style='color: #94A3B8;'>h</span>", 140)

        stato_container = QWidget()
        stato_container.setFixedWidth(100)
        stato_layout = QHBoxLayout(stato_container)
        stato_layout.setContentsMargins(0,0,0,0)

        stato_lbl = QLabel(dipendente.stato.name)
        color = "#DCFCE7" if dipendente.stato.name == "ASSUNTO" else "#F3F4F6"
        text_color = "#15803D" if dipendente.stato.name == "ASSUNTO" else "#6B7280"
        stato_lbl.setStyleSheet(f"background-color: {color}; color: {text_color}; padding: 4px 12px; border-radius: 10px; font-size: 10px; font-weight: 800;")
        stato_layout.addWidget(stato_lbl)
        stato_layout.addStretch()
        layout.addWidget(stato_container)

        layout.addStretch()

        btn_menu = QPushButton("⋮")
        btn_menu.setFixedWidth(30)
        btn_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_menu.setStyleSheet("QPushButton { color: #94A3B8; font-size: 20px; border: none; background: transparent; } QPushButton:hover { color: #111827; }")
        btn_menu.clicked.connect(lambda: self.menu_clicked.emit(self.id_dipendente))
        layout.addWidget(btn_menu)

        self.update_style()

    def update_style(self):
        bg = "#F9FAFB" if self.selected else "white"
        border = "2px solid #004D99" if self.selected else "none"
        self.setStyleSheet(f"""
            #row_card {{
                background-color: {bg};
                border-bottom: 1px solid #F3F4F6;
                border-left: {border};
            }}
            #row_card:hover {{
                background-color: #F9FAFB;
            }}
        """)

    def mousePressEvent(self, event):
        self.clicked.emit(self.id_dipendente)
        super().mousePressEvent(event)

    def add_col(self, layout, text, width, bold=False):
        lbl = QLabel(text)
        lbl.setFixedWidth(width)
        style = "color: #111827; font-size: 14px;"
        if bold: style += " font-weight: 600;"
        lbl.setStyleSheet(style)
        layout.addWidget(lbl)

class PersonaleView(QWidget):
    def __init__(self, interfaccia):
        super().__init__()
        self.interfaccia = interfaccia
        self.selected_id = None
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(0)

        # Header
        top_header_layout = QHBoxLayout()
        top_header = QLabel("Gestione Dipendenti")
        top_header.setStyleSheet("color: #111827; font-size: 16px; font-weight: 600;")
        top_header_layout.addWidget(top_header)
        top_header_layout.addStretch()
        
        btn_bell = QPushButton("🔔")
        btn_profile = QPushButton("👤")
        icon_style = "QPushButton { color: #94A3B8; font-size: 18px; border: none; background: transparent; } QPushButton:hover { color: #111827; }"
        btn_bell.setStyleSheet(icon_style)
        btn_profile.setStyleSheet(icon_style)
        top_header_layout.addWidget(btn_bell)
        top_header_layout.addWidget(btn_profile)
        
        main_layout.addLayout(top_header_layout)
        main_layout.addSpacing(25)
        
        # Anagrafica Section Header
        section_layout = QHBoxLayout()
        sec_title_layout = QVBoxLayout()
        sec_title = QLabel("Anagrafica Personale")
        sec_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #111827;")
        sec_sub = QLabel("Gestisci i contratti e monitora i residui di ferie e ROL.")
        sec_sub.setStyleSheet("font-size: 13px; color: #6B7280;")
        sec_title_layout.addWidget(sec_title)
        sec_title_layout.addWidget(sec_sub)
        section_layout.addLayout(sec_title_layout)
        section_layout.addStretch()
        
        btn_licenzia = QPushButton(" 👤✖ Segna come LICENZIATO")
        btn_licenzia.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_licenzia.setStyleSheet("QPushButton { background-color: #E5E7EB; color: #111827; padding: 10px 20px; border-radius: 6px; font-weight: 600; font-size: 13px; } QPushButton:hover { background-color: #D1D5DB; }")
        btn_licenzia.clicked.connect(self.cmd_licenzia_selected)
        
        btn_assumi = QPushButton(" 👤+ Aggiungi Dipendente")
        btn_assumi.setStyleSheet("background-color: #004D99; color: white; padding: 10px 20px; border-radius: 6px; font-weight: 600; font-size: 13px;")
        btn_assumi.clicked.connect(self.cmd_assumi)

        section_layout.addWidget(btn_licenzia)
        section_layout.addSpacing(10)
        section_layout.addWidget(btn_assumi)
        main_layout.addLayout(section_layout)
        main_layout.addSpacing(25)
        
        # Stats Cards
        stats_layout = QHBoxLayout()
        self.card_totale = StatsCard("Totale Dipendenti", "0", "👥", sub_value="↗ 2")
        self.card_ferie = StatsCard("Ferie in corso", "5", "⛱", accent_color="#004D99")
        self.card_certificato = StatsCard("Personale in certificato", "3", "🏥", accent_color="#BA1A1A")
        stats_layout.addWidget(self.card_totale)
        stats_layout.addWidget(self.card_ferie)
        stats_layout.addWidget(self.card_certificato)
        stats_layout.addStretch()
        main_layout.addLayout(stats_layout)
        main_layout.addSpacing(30)
        
        # Table Container
        self.table_card = QFrame()
        self.table_card.setStyleSheet("background-color: white; border-radius: 12px; border: 1px solid #ECEEEF;")
        table_layout = QVBoxLayout(self.table_card)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        
        # Search and Filter
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(20, 20, 20, 20)
        search_input = QLineEdit()
        search_input.setPlaceholderText(" 🔍 Cerca per nome, cognome o ruolo...")
        search_input.setFixedWidth(350)
        search_input.setFixedHeight(40)
        search_input.setStyleSheet("background-color: #F2F4F5; border: none; border-radius: 6px; padding-left: 10px; color: #111827;")
        filter_layout.addWidget(search_input)
        filter_layout.addStretch()
        btn_filters = QPushButton(" ≡ Filtri Avanzati")
        btn_filters.setStyleSheet("color: #4B5563; font-weight: 600; border: none; background: transparent;")
        filter_layout.addWidget(btn_filters)
        table_layout.addLayout(filter_layout)
        
        # Header Labels
        labels_layout = QHBoxLayout()
        labels_layout.setContentsMargins(25, 10, 25, 10)
        labels_layout.setStyleSheet("background-color: #F8FAFB; border-top: 1px solid #ECEEEF; border-bottom: 1px solid #ECEEEF;")
        
        for text, width in [("NOME", 120), ("COGNOME", 120), ("GIORNI FERIE\nRIMASTI", 140), ("ORE ROL\nRIMASTE", 140), ("STATO", 100)]:
            lbl = QLabel(text)
            lbl.setFixedWidth(width)
            lbl.setStyleSheet("color: #4B5563; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
            labels_layout.addWidget(lbl)
        labels_layout.addStretch()
        table_layout.addLayout(labels_layout)
        
        # Scroll Area for rows
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.scroll_content = QWidget()
        self.rows_layout = QVBoxLayout(self.scroll_content)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)
        self.rows_layout.setSpacing(0)
        self.rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        table_layout.addWidget(self.scroll_area)
        
        # Footer / Pagination
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(20, 15, 20, 15)
        self.footer_label = QLabel("Visualizzando 1-10 di 42 dipendenti")
        self.footer_label.setStyleSheet("color: #6B7280; font-size: 13px;")
        footer_layout.addWidget(self.footer_label)
        footer_layout.addStretch()
        # Simple pagination mockup
        for p in ["<", "1", "2", "3", ">"]:
            btn = QPushButton(p)
            btn.setFixedSize(28, 28)
            if p == "1":
                btn.setStyleSheet("background-color: #004D99; color: white; border-radius: 4px; font-weight: bold;")
            else:
                btn.setStyleSheet("color: #4B5563; border: none; background: transparent;")
            footer_layout.addWidget(btn)

        table_layout.addLayout(footer_layout)

        main_layout.addWidget(self.table_card)
        main_layout.addStretch()
        
        self.aggiorna_lista()

    def aggiorna_lista(self):
        for i in reversed(range(self.rows_layout.count())):
            widget = self.rows_layout.itemAt(i).widget()
            if widget: widget.setParent(None)

        if not self.interfaccia: return
            
        dipendenti = self.interfaccia.sistema_dipendenti.get_lista_dipendenti()
        self.card_totale.val_lbl.setText(str(len(dipendenti)))
        self.footer_label.setText(f"Visualizzando 1-{len(dipendenti)} di {len(dipendenti)} dipendenti")

        for dip in dipendenti:
            row = DipendenteRow(dip, selected=(dip.id_dipendente == self.selected_id))
            row.menu_clicked.connect(self.cmd_licenzia)
            row.clicked.connect(self.on_row_clicked)
            self.rows_layout.addWidget(row)

    def on_row_clicked(self, id_dip):
        self.selected_id = id_dip
        self.aggiorna_lista()

    def cmd_assumi(self):
        dialog = AddDipendenteDialog(self)
        if dialog.exec():
            nome, cognome = dialog.get_data()
            if nome and cognome:
                self.interfaccia.sistema_dipendenti.assumi_dipendente(nome, cognome)
                self.aggiorna_lista()

    def cmd_licenzia_selected(self):
        if self.selected_id is None:
            QMessageBox.warning(self, "Attenzione", "Seleziona prima un dipendente dalla lista.")
            return
        self.cmd_licenzia(self.selected_id)

    def cmd_licenzia(self, id_dip):
        confirm = QMessageBox.question(self, "Conferma Licenziamento", f"Sei sicuro di voler licenziare il dipendente #{id_dip}?")
        if confirm == QMessageBox.StandardButton.Yes:
            success = self.interfaccia.sistema_dipendenti.rimuovi_dipendente(id_dip)
            if success:
                if self.selected_id == id_dip: self.selected_id = None
                self.aggiorna_lista()
            else:
                QMessageBox.critical(self, "Errore", "Impossibile rimuovere il dipendente.")

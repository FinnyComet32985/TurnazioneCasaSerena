from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QMessageBox,
    QGridLayout, QDialog, QDoubleSpinBox, QFormLayout, QLineEdit
)
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QColor
from PyQt6.QtCore import Qt, QSize
from path_util import resource_path
from datetime import datetime, date, timedelta
import random # Per simulare i dati storici

class RegolaBancaOreDialog(QDialog):
    def __init__(self, saldo_attuale, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Regola Banca Ore")
        self.setFixedWidth(300)
        
        layout = QFormLayout(self)
        
        self.lbl_info = QLabel("Modifica il valore totale per correggere il saldo.")
        self.lbl_info.setWordWrap(True)
        layout.addRow(self.lbl_info)
        
        self.spin_ore = QDoubleSpinBox()
        self.spin_ore.setStyleSheet("background-color: white; color: #0f172a; border: 1px solid #cbd5e1; padding: 5px; border-radius: 4px;")
        self.spin_ore.setRange(-1000, 1000)
        self.spin_ore.setDecimals(2)
        self.spin_ore.setSuffix(" ore")
        self.spin_ore.setValue(saldo_attuale)
        
        self.input_motivo = QLineEdit()
        self.input_motivo.setPlaceholderText("Es: Pagamento ore, Straordinari extra...")
        self.input_motivo.setStyleSheet("background-color: white; color: #0f172a; border: 1px solid #cbd5e1; padding: 5px; border-radius: 4px;")

        layout.addRow("Nuovo Saldo:", self.spin_ore)
        layout.addRow("Motivazione:", self.input_motivo)
        
        btn_layout = QHBoxLayout()
        btn_salva = QPushButton("Applica")
        btn_annulla = QPushButton("Annulla")
        btn_salva.clicked.connect(self.accept)
        btn_annulla.clicked.connect(self.reject)
        btn_layout.addWidget(btn_salva)
        btn_layout.addWidget(btn_annulla)
        
        layout.addRow(btn_layout)
    
    def get_data(self):
        return self.spin_ore.value(), self.input_motivo.text().strip()

class BancaOreView(QWidget):
    def __init__(self, interfaccia):
        super().__init__()
        self.interfaccia = interfaccia
        self.current_dip_id = None
        self.is_large_layout = None # Stato attuale del layout
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 20, 0, 0)
        main_layout.setSpacing(20)

        # --- Header ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Gestione Banca Ore")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f172a;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # --- Body ---
        body_layout = QHBoxLayout()
        body_layout.setSpacing(30)

        # Colonna Sinistra
        left_column = QWidget()
        self.left_layout = QVBoxLayout(left_column) # Salviamo il riferimento
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(20)

        self.saldo_card = self.create_saldo_card()
        self.left_layout.addWidget(self.saldo_card)

        self.left_layout.addStretch() # Spinge il saldo in alto
        body_layout.addWidget(left_column, alignment=Qt.AlignmentFlag.AlignTop)

        # Colonna Destra: Storico (Lista)
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        lbl_storico = QLabel("Storico Movimenti")
        lbl_storico.setStyleSheet("color: #64748b; font-weight: bold; font-size: 14px;")
        right_layout.addWidget(lbl_storico)

        # Container Overlay (Lista + Card Info in basso)
        overlay_container = QWidget()
        self.overlay_layout = QGridLayout(overlay_container) # Salviamo il riferimento
        self.overlay_layout.setContentsMargins(0, 0, 0, 0)
        self.overlay_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        scroll_content.setStyleSheet("background-color: transparent;")
        
        self.lista_movimenti_layout = QVBoxLayout(scroll_content)
        self.lista_movimenti_layout.setSpacing(15)
        self.lista_movimenti_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Margine inferiore extra per permettere di scrollare tutto il contenuto sopra la card fissa
        self.lista_movimenti_layout.setContentsMargins(0, 0, 0, 100) 
        
        scroll_area.setWidget(scroll_content)
        
        # self.info_card = self.create_info_card() # NASCOSTO TEMPORANEAMENTE
        self.overlay_layout.addWidget(scroll_area, 0, 0)
        # info_card posizionata dinamicamente (Disabilitato)

        right_layout.addWidget(overlay_container)

        body_layout.addWidget(right_column, stretch=1)

        main_layout.addLayout(header_layout)
        main_layout.addLayout(body_layout)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Se l'altezza è sufficiente (> 550px), sposta a sinistra. Altrimenti overlay.
        is_large = self.height() > 550
        
        if is_large != self.is_large_layout:
            self.is_large_layout = is_large
            self.update_info_card_position()
            
    def update_info_card_position(self):
        if not hasattr(self, 'info_card'): return

        # Rimuove dal layout precedente (senza eliminare l'oggetto)
        self.info_card.setParent(None)
        
        if self.is_large_layout:
            # --- POSIZIONE: Colonna Sinistra (Statico) ---
            # Inserisce in posizione 1 (dopo la saldo_card, prima dello stretch)
            self.left_layout.insertWidget(1, self.info_card)
            
            # Stile "Badge" (Solido, Bordo completo)
            self.info_card.setStyleSheet("""
                #info_card {
                    background-color: #eff6ff;
                    border: 1px solid #dbeafe;
                    border-radius: 8px;
                }
            """)
            self.info_card.layout().setContentsMargins(15, 15, 15, 15)
            
        else:
            # --- POSIZIONE: Overlay Destra (Sticky Bottom) ---
            self.overlay_layout.addWidget(self.info_card, 0, 0, Qt.AlignmentFlag.AlignBottom)
            
            # Stile "Overlay" (Sfumato in alto, Bordo parziale)
            self.info_card.setStyleSheet("""
                #info_card {
                    background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 rgba(239, 246, 255, 0), stop:0.3 #eff6ff, stop:1 #eff6ff);
                    border: 1px solid #dbeafe;
                    border-top: none; 
                    border-bottom-left-radius: 8px;
                    border-bottom-right-radius: 8px;
                    border-top-left-radius: 0px;
                    border-top-right-radius: 0px;
                }
            """)
            # Padding superiore maggiore per la sfumatura
            self.info_card.layout().setContentsMargins(20, 40, 20, 20)

    def create_saldo_card(self):
        card = QWidget()
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setObjectName("saldo_card")
        card.setFixedWidth(350)
        card.setMinimumHeight(240)
        # Sfondo scuro (Oro/Ambra scuro)
        card.setStyleSheet("""
            #saldo_card {
                background-color: #ea580c; 
                border-radius: 12px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(5)

        # Header: Titolo + Icona
        header = QHBoxLayout()
        lbl_title = QLabel("SALDO ATTUALE")
        lbl_title.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px; font-weight: bold; letter-spacing: 1px;")
        
        icon_label = QLabel()
        pix = QPixmap(resource_path("interfacciaGrafica/assets/hourglass.svg"))
        if not pix.isNull():
            # Ricoloro l'icona in Oro chiaro
            painter = QPainter(pix)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pix.rect(), QColor("#fcd34d")) 
            painter.end()
            icon_label.setPixmap(pix.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        header.addWidget(lbl_title)
        header.addStretch()
        header.addWidget(icon_label)
        layout.addLayout(header)

        layout.addSpacing(10)

        # Valore
        val_layout = QHBoxLayout()
        val_layout.setSpacing(10)
        val_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

        self.lbl_saldo = QLabel("0.00")
        self.lbl_saldo.setStyleSheet("color: #ffffff; font-size: 48px; font-weight: 800;")
        
        lbl_ore = QLabel("ore")
        lbl_ore.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 18px; font-weight: bold; margin-bottom: 8px;")

        val_layout.addWidget(self.lbl_saldo)
        val_layout.addWidget(lbl_ore)
        layout.addLayout(val_layout)

        layout.addSpacing(20)

        # Bottone Regola
        self.btn_regola = QPushButton("  Regola saldo ore")
        self.btn_regola.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_regola.setIcon(QIcon(resource_path("interfacciaGrafica/assets/options.svg")))
        self.btn_regola.setIconSize(QSize(20, 20))
        self.btn_regola.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.3);
            }
        """)
        self.btn_regola.clicked.connect(self.cmd_regola_saldo)
        layout.addWidget(self.btn_regola)

        return card

    def create_info_card(self):
        info_card = QWidget()
        info_card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        info_card.setObjectName("info_card")
        # Lo stile viene applicato dinamicamente in update_info_card_position
        info_layout = QHBoxLayout(info_card)
        info_layout.setSpacing(5) 

        info_icon = QLabel()
        pixmap = QPixmap(resource_path("interfacciaGrafica/assets/information-circle.svg"))
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor("#1e3a8a"))
        painter.end()
        info_icon.setPixmap(pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        info_text = QLabel("Parte delle ore accumulate dovranno essere recuperate o pagate entro il 31/12.")
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #1e3a8a; font-size: 13px; border: none; background: transparent;")

        info_layout.addWidget(info_icon, alignment=Qt.AlignmentFlag.AlignTop)
        info_layout.addWidget(info_text)

        return info_card

    def create_transaction_card(self, key, descrizione, ore, positivo):
        card = QWidget()
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setObjectName("trans_card")
        card.setStyleSheet("""
            #trans_card {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        is_manual = key.startswith("DIR_")
        display_title = descrizione
        display_subtitle = ""
        
        if is_manual:
            display_title = "Regolazione Manuale"
            display_subtitle = descrizione
        elif key.startswith("SETT_"):
            # Parsa la key SETT_2025_2 per ottenere le date
            try:
                parti = key.split("_")
                y, w = int(parti[1]), int(parti[2])
                d1 = date.fromisocalendar(y, w, 1)
                d2 = d1 + timedelta(days=6)
                mesi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
                display_title = f"{d1.day} {mesi[d1.month-1]} - {d2.day} {mesi[d2.month-1]} {d2.year}"
            except:
                pass

        # Configurazione Stile in base al segno
        if positivo:
            bg_icon = "#f0fdf4" # Verde chiaro
            color_icon = "#16a34a" # Verde scuro
            icon_name = "trending-up.svg"
            segno = "+"
            color_text = "#15803d"
        else:
            bg_icon = "#fef2f2" # Rosso chiaro
            color_icon = "#dc2626" # Rosso scuro
            icon_name = "trending-down.svg"
            segno = "-"
            color_text = "#b91c1c"

        # Icona
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(40, 40)
        icon_lbl.setStyleSheet(f"background-color: {bg_icon}; border-radius: 20px;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        pix = QPixmap(resource_path(f"interfacciaGrafica/assets/{icon_name}"))
        if not pix.isNull():
            painter = QPainter(pix)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pix.rect(), QColor(color_icon))
            painter.end()
            icon_lbl.setPixmap(pix.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

        # Dettagli
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        if not is_manual:
            info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_desc = QLabel(display_title)
        lbl_desc.setStyleSheet("color: #0f172a; font-weight: bold; font-size: 14px;")
        
        info_layout.addWidget(lbl_desc)
        
        if display_subtitle:
            lbl_sub = QLabel(display_subtitle)
            lbl_sub.setStyleSheet("color: #64748b; font-size: 12px;")
            info_layout.addWidget(lbl_sub)

        # Valore Ore
        lbl_valore = QLabel(f"{segno} {abs(ore)}h")
        lbl_valore.setStyleSheet(f"color: {color_text}; font-weight: bold; font-size: 16px;")

        layout.addWidget(icon_lbl)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(lbl_valore)

        return card

    def load_data(self, id_dipendente):
        self.current_dip_id = id_dipendente
        dip = self.interfaccia.sistema_dipendenti.get_dipendente(id_dipendente)
        if not dip: return

        # Aggiorna Saldo
        if dip.stato.name == "LICENZIATO":
            self.btn_regola.setVisible(False)
        else:
            self.btn_regola.setVisible(True)

        self.lbl_saldo.setText(f"{dip.banca_ore:+.2f}")

        # --- Caricamento Storico Reale ---
        while self.lista_movimenti_layout.count():
            child = self.lista_movimenti_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        movimenti = self.interfaccia.sistema_dipendenti.get_movimenti_banca_ore(id_dipendente)
        
        if not movimenti:
            lbl_empty = QLabel("Nessun movimento registrato.")
            lbl_empty.setStyleSheet("color: #94a3b8; font-style: italic; margin-top: 10px;")
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lista_movimenti_layout.addWidget(lbl_empty)
        else:
            for mov in movimenti:
                is_positivo = mov.valore >= 0
                card = self.create_transaction_card(mov.key, mov.descrizione, mov.valore, is_positivo)
                self.lista_movimenti_layout.addWidget(card)

    def cmd_regola_saldo(self):
        if not self.current_dip_id: return
        
        # Recuperiamo il dipendente per conoscere il saldo di partenza
        dip = self.interfaccia.sistema_dipendenti.get_dipendente(self.current_dip_id)
        if not dip: return

        dialog = RegolaBancaOreDialog(dip.banca_ore, self)
        if dialog.exec():
            nuovo_saldo, motivo = dialog.get_data()
            # Calcoliamo il delta (Nuovo - Vecchio) per il backend
            delta_ore = nuovo_saldo - dip.banca_ore
            
            if delta_ore != 0:
                # Usiamo DIR_ + timestamp per garantire univocità della chiave
                key = f"DIR_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                descrizione = motivo if motivo else "Rettifica manuale del dirigente"
                
                success = self.interfaccia.sistema_dipendenti.aggiungi_variazione_banca_ore(self.current_dip_id, delta_ore, key, descrizione)
                if success:
                    self.load_data(self.current_dip_id)
                else:
                    QMessageBox.critical(self, "Errore", "Impossibile aggiornare la banca ore.")

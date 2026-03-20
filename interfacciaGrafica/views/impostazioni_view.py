from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class ImpostazioniView(QWidget):
    def __init__(self, interfaccia):
        super().__init__()
        self.interfaccia = interfaccia
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel("Impostazioni")
        title.setObjectName("page_title")
        subtitle = QLabel("Configurazioni dell'applicazione (in arrivo)")
        subtitle.setObjectName("page_subtitle")
        
        card = QWidget()
        card.setObjectName("card_container")
        card_layout = QVBoxLayout(card)
        
        label = QLabel("La pagina impostazioni verrà implementata in futuro.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(label)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(20)
        layout.addWidget(card)
        layout.addStretch()

from PyQt6.QtWidgets import QSplashScreen, QApplication
from PyQt6.QtGui import QPixmap, QColor, QFont, QPainter
from PyQt6.QtCore import Qt
from path_util import resource_path

class LoadingScreen(QSplashScreen):
    def __init__(self):
        # Creiamo un'area di caricamento elegante coerente con lo stile della sidebar
        width, height = 500, 300
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor("#1e293b")) # Blu scuro ardesia come la sidebar
        
        painter = QPainter(pixmap)
        # Proviamo a caricare il logo aziendale
        logo_pix = QPixmap(resource_path("interfacciaGrafica/assets/logo.svg"))
        if not logo_pix.isNull():
            # Scaliamo il logo per adattarlo bene al centro
            logo_pix = logo_pix.scaled(250, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            x = (width - logo_pix.width()) // 2
            y = (height - logo_pix.height()) // 2 - 20
            painter.drawPixmap(x, y, logo_pix)
        
        # Aggiungiamo un bordo decorativo blu acceso
        painter.setPen(QColor("#3b82f6"))
        painter.drawRect(0, 0, width - 1, height - 1)
        painter.end()
        
        super().__init__(pixmap)
        # Assicuriamoci che sia sempre sopra le altre finestre durante l'avvio
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setFont(QFont('Segoe UI', 11, QFont.Weight.Bold))
        
    def show_message(self, message):
        """Aggiorna il testo informativo sulla finestra di caricamento"""
        # Torniamo all'allineamento in basso (AlignBottom)
        self.showMessage(
            message.upper(), 
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, 
            QColor("#ffffff")
        )
        # Necessario per mantenere la UI reattiva durante il caricamento
        QApplication.processEvents()

    def drawContents(self, painter):
        """Override per aggiungere un margine di 50px dal fondo al testo di showMessage"""
        painter.save()
        # Trasliamo il sistema di coordinate verso l'alto di 50px
        # Questo sposta il testo (allineato in basso) verso l'alto del valore desiderato
        painter.translate(0, -50)
        super().drawContents(painter)
        painter.restore()
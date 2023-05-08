from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QMouseEvent
from PyQt6.QtWidgets import QComboBox, QLabel, QWidget


class MyComboBox(QComboBox):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        QComboBox.showPopup(self)


class MyWidget(QWidget):
    on_close = pyqtSignal()

    def __init__(self, parent=None, flags=Qt.WindowType.Window):
        super().__init__(parent, flags)

    def closeEvent(self, event: QCloseEvent):
        self.on_close.emit()


class TransWindow(QWidget):

    def __init__(self, parent=None, flags=Qt.WindowType.Widget):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        super().__init__(parent, flags)


class MyLabel(QLabel):

    def __init__(self,
                 text: str = "",
                 parent: QWidget | None = None,
                 flags: Qt.WindowType = Qt.WindowType.Widget):
        super().__init__(text, parent, flags)

        self.old_pos = None
        self.is_drag = False

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            self.is_drag = True
            self.old_pos = event.globalPosition().toPoint()
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.is_drag:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.parent().move(self.parent().x() + delta.x(),
                               self.parent().y() + delta.y())
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.is_drag:
            self.is_drag = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

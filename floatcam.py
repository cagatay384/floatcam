#!/usr/bin/env python3
"""
FloatCam — floating webcam bubble, always on top.

Platform-independent: runs the same way on macOS, Windows, and Linux.
Xcode/Swift'e bağlı olmadan çalışır. Gereken paketler: PyQt5, opencv-python.
    pip3 install PyQt5 opencv-python

Çalıştırma:
    python3 floatcam.py

Kontroller:
    - Sol tık + sürükle: baloncuğu taşı
    - Fare tekerleği (baloncuğun üzerinde): boyut değiştir
    - Sağ tık: Size / Shape / Border Color / Quit menüsü
    - Cmd+Q / Ctrl+Q: çıkış
"""

import math
import sys

import cv2
from PyQt5.QtCore import QPointF, QSettings, Qt, QTimer
from PyQt5.QtGui import (
    QColor,
    QIcon,
    QImage,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QApplication,
    QColorDialog,
    QMenu,
    QShortcut,
    QWidget,
)

DEFAULT_SIZE = 200
MIN_SIZE = 100
MAX_SIZE = 480
SIZE_STEP = 10
FPS_MS = 30  # ~33 fps
BORDER_WIDTH = 3

SHAPES = ["Circle", "Square", "Rounded Square", "Hexagon"]
SIZE_PRESETS = [
    ("Small", 140),
    ("Medium", 200),
    ("Large", 280),
    ("Extra Large", 360),
]
COLOR_PRESETS = [
    ("White", "#ffffff"),
    ("Black", "#000000"),
    ("Red", "#ff3b30"),
    ("Green", "#34c759"),
    ("Blue", "#007aff"),
    ("Yellow", "#ffcc00"),
]


def shape_path(shape: str, size: int) -> QPainterPath:
    path = QPainterPath()
    inset = BORDER_WIDTH / 2
    rect_size = size - BORDER_WIDTH

    if shape == "Circle":
        path.addEllipse(inset, inset, rect_size, rect_size)
    elif shape == "Square":
        path.addRect(inset, inset, rect_size, rect_size)
    elif shape == "Rounded Square":
        radius = rect_size * 0.22
        path.addRoundedRect(inset, inset, rect_size, rect_size, radius, radius)
    elif shape == "Hexagon":
        cx, cy, r = size / 2, size / 2, rect_size / 2
        points = []
        for i in range(6):
            angle = math.radians(60 * i - 90)
            points.append(QPointF(cx + r * math.cos(angle), cy + r * math.sin(angle)))
        polygon = QPolygonF(points)
        path.addPolygon(polygon)
        path.closeSubpath()
    else:
        path.addEllipse(inset, inset, rect_size, rect_size)
    return path


class FloatCam(QWidget):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("FloatCam", "FloatCam")
        self.shape = self.settings.value("shape", "Circle")
        self.border_color = QColor(self.settings.value("border_color", "#ffffff"))
        self.bubble_size = int(self.settings.value("size", DEFAULT_SIZE))
        self.bubble_size = max(MIN_SIZE, min(MAX_SIZE, self.bubble_size))
        if self.shape not in SHAPES:
            self.shape = "Circle"

        self.setWindowTitle("FloatCam")
        self.setFixedSize(self.bubble_size, self.bubble_size)

        # Borderless, always-on-top, transparent background.
        # Note: Qt.Tool renders as an NSPanel on macOS, which auto-hides
        # when the app loses focus — avoid it so the bubble stays visible
        # while clicking other apps.
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._center_on_screen()

        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, MAX_SIZE * 2)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, MAX_SIZE * 2)

        self._frame_pixmap = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_frame)
        self.timer.start(FPS_MS)

        self._drag_offset = None

        quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        quit_shortcut.activated.connect(self._quit)

    def _center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.bubble_size) // 2
        y = (screen.height() - self.bubble_size) // 2
        self.move(x, y)

    def _update_frame(self):
        ok, frame = self.capture.read()
        if not ok:
            return

        size = self.bubble_size
        h, w = frame.shape[:2]
        side = min(h, w)
        top = (h - side) // 2
        left = (w - side) // 2
        frame = frame[top:top + side, left:left + side]
        frame = cv2.resize(frame, (size, size))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.flip(frame, 1)  # mirror, like the Swift version

        image = QImage(frame.data, size, size, 3 * size, QImage.Format_RGB888)
        self._frame_pixmap = QPixmap.fromImage(image.copy())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = shape_path(self.shape, self.bubble_size)
        painter.setClipPath(path)

        if self._frame_pixmap is not None:
            painter.drawPixmap(0, 0, self._frame_pixmap)
        else:
            painter.fillPath(path, QColor(30, 30, 30))

        painter.setClipping(False)
        pen = QPen(self.border_color, BORDER_WIDTH)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPos() - self.frameGeometry().topLeft()
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPos())

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_offset)

    def mouseReleaseEvent(self, event):
        self._drag_offset = None

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta == 0:
            return
        step = SIZE_STEP if delta > 0 else -SIZE_STEP
        self._set_size(self.bubble_size + step)

    def _show_context_menu(self, global_pos):
        menu = QMenu(self)

        size_menu = menu.addMenu("Size")
        size_group = QActionGroup(self)
        size_group.setExclusive(True)
        for name, value in SIZE_PRESETS:
            action = QAction(f"{name} ({value}px)", self, checkable=True)
            action.setChecked(value == self.bubble_size)
            action.triggered.connect(lambda checked, v=value: self._set_size(v))
            size_group.addAction(action)
            size_menu.addAction(action)
        size_menu.addSeparator()
        size_menu.addAction("Scroll on bubble to resize").setEnabled(False)

        shape_menu = menu.addMenu("Shape")
        shape_group = QActionGroup(self)
        shape_group.setExclusive(True)
        for name in SHAPES:
            action = QAction(name, self, checkable=True)
            action.setChecked(name == self.shape)
            action.triggered.connect(lambda checked, n=name: self._set_shape(n))
            shape_group.addAction(action)
            shape_menu.addAction(action)

        color_menu = menu.addMenu("Border Color")
        color_group = QActionGroup(self)
        color_group.setExclusive(True)
        for name, hex_code in COLOR_PRESETS:
            action = QAction(name, self, checkable=True)
            action.setChecked(QColor(hex_code) == self.border_color)
            swatch = QPixmap(16, 16)
            swatch.fill(QColor(hex_code))
            action.setIcon(QIcon(swatch))
            action.triggered.connect(lambda checked, c=hex_code: self._set_border_color(QColor(c)))
            color_group.addAction(action)
            color_menu.addAction(action)
        color_menu.addSeparator()
        custom_action = QAction("Custom...", self)
        custom_action.triggered.connect(self._pick_custom_color)
        color_menu.addAction(custom_action)

        menu.addSeparator()
        quit_action = QAction("Quit FloatCam", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(quit_action)

        menu.exec_(global_pos)

    def _set_size(self, new_size):
        new_size = max(MIN_SIZE, min(MAX_SIZE, new_size))
        if new_size == self.bubble_size:
            return
        center = self.geometry().center()
        self.bubble_size = new_size
        self.setFixedSize(new_size, new_size)
        self.move(center.x() - new_size // 2, center.y() - new_size // 2)
        self.settings.setValue("size", new_size)
        self.update()

    def _set_shape(self, name):
        self.shape = name
        self.settings.setValue("shape", name)
        self.update()

    def _set_border_color(self, color: QColor):
        self.border_color = color
        self.settings.setValue("border_color", color.name())
        self.update()

    def _pick_custom_color(self):
        color = QColorDialog.getColor(self.border_color, self, "Choose Border Color")
        if color.isValid():
            self._set_border_color(color)

    def _quit(self):
        self.capture.release()
        QApplication.instance().quit()

    def closeEvent(self, event):
        self.capture.release()
        event.accept()


def main():
    app = QApplication(sys.argv)
    bubble = FloatCam()
    bubble.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

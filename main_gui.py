
import sys
import numpy as np
import cv2
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread

from gui.SDUI import App


if __name__=="__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())
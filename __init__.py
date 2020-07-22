import sys
import time

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow

from assets.Colors import Colors
from assets.Fonts import Fonts

from gui.MainGui import MainGui

from meta.Debug import Debug as dbg

WIDTH = 900                                 # Starting width
HEIGHT = 500                                # Starting height

STYLES = "./assets/styles.qss"              # Master stylesheet

application_start = time.time()

class App(QMainWindow):

  def __init__(self):

    super().__init__()

    self.title = "szurubooru_uploader"

    # Initialize Fonts by adding fonts to database before everything else
    # We only need to do this once
    Fonts.init()

    # Initialize main window
    self.setWindowTitle(self.title)
    self.setGeometry(0, 0, WIDTH, HEIGHT)
    self.setStyleSheet(f"background-color: {Colors.bg}")

    print("Started QMainWindow.")

    # Create instance of main tab layout
    self.tab_widget = MainGui(self)
    self.setCentralWidget(self.tab_widget)

    print(f"Finished initializing application in {(time.time() - application_start) * 1000}ms.")

    self.show()

if __name__ == '__main__':
  # This block launches the actual app

  try:
    # We put all of this in a try/except to catch KeyboardInterrupts
    
    # Initialize app and get the stylesheet
    app = QApplication(sys.argv)
    app.setStyleSheet(open(STYLES, 'r').read())

    # Initialize our overriden app class
    ex = App()

    # Start a QTimer as a Python event that runs every 100ms
    # We do this so Python can throw KeyboardInterrupts
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)

    # Start it
    sys.exit(app.exec_())

  except KeyboardInterrupt:

    sys.exit(1)

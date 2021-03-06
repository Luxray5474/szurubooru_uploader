from PyQt5.QtCore     import Qt
from PyQt5.QtGui      import QPixmap
from PyQt5.QtWidgets  import QLabel

class ThumbnailItem(QLabel):

  def __init__(self):

    super(ThumbnailItem, self).__init__()

    # Tells FlowLayout whether or not to start a newline before or after this widget
    self.newline_before = False
    self.newline_after = False

    self.thumb = QPixmap()

  def loadFromData(self, data):
    # Abbreviates the process of inserting a QPixmap into this QLabel

    self.thumb.loadFromData(data) # Load the bytearray into the QPixmap
    self.setPixmap(self.thumb) # Attach the QPixmap to this QLabel
    self.setFixedWidth(self.sizeHint().width()) # Make sure of the width
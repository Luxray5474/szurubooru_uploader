from PyQt5.QtCore     import Qt
from PyQt5.QtWidgets  import QLabel, QVBoxLayout, QWidget

from Fonts         import Fonts
from Colors        import Colors

class DatesectionItem(QWidget):

  def __init__(self):

    super(DatesectionItem, self).__init__()

    self.left_space = 0 # How much space to put on the left side to seperate sections
    self.normal_width = 150 # Width of normal date section
    self.unknown_width = 250 # Width of "Unknown Date" date section

    self.layout = QVBoxLayout()
    self.label = QLabel()

    self.label.setAlignment(Qt.AlignCenter)
    self.label.setObjectName("dateSectionLabel")
    self.label.setContentsMargins(10, 20, 10, 20)
    self.label.setFont(Fonts.NotoSansDisplay("ExtraLight", 20))

    self.layout.addWidget(self.label)
    self.layout.setContentsMargins(self.left_space, 0, 0, 0)

    self.setLayout(self.layout)
    # self.setObjectName("dateSection")
    self.setStyleSheet("background: #00010A") # Why can't I set this in the master stylesheet????

  def setDate(self, year, month, day):
    # Set date text for inner QLabel

    # Pad month and day
    month = str(month).zfill(2)
    day = str(day).zfill(2)

    # Final string
    final_string = f"{year}\n{month}/{day}"

    self.label.setText(final_string)
    self.label.setFixedWidth(self.normal_width)

  def setText(self, text):
    # Set text and width of inner QLabel

    self.label.setText(text)
    self.label.setFixedWidth(self.unknown_width)
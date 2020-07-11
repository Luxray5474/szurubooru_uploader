import calendar

from PyQt5.QtCore     import Qt
from PyQt5.QtWidgets  import QLabel, QVBoxLayout, QWidget

from Fonts         import Fonts
from Colors        import Colors

class DatesectionItem(QWidget):

  def __init__(self):

    super(DatesectionItem, self).__init__()

    # Tells FlowLayout whether or not to start a newline before or after this widget
    self.newline_before = True 
    self.newline_after = True

    self.height = 30 # This widget needs a different height than normal

    self.layout = QVBoxLayout()
    self.label = QLabel()

    self.label.setObjectName("dateSectionLabel")
    self.label.setContentsMargins(10, 0, 10, 0)
    self.label.setFont(Fonts.NotoSansDisplay("Bold", 13))

    self.layout.addWidget(self.label)

    self.setLayout(self.layout)
    self.setStyleSheet(f"background: {Colors.bg}") # Why can't I set this in the master stylesheet????

  def setDate(self, year, month, day):
    # Set date text for inner QLabel

    # Pad month and day
    month = int(str(month).zfill(2))
    day = str(day).zfill(2)

    # Final string
    final_string = f"{calendar.month_name[month + 1]} {day}, {year}"

    self.label.setText(final_string)

  def setText(self, text):
    # Set text and width of inner QLabel

    self.label.setText(text)
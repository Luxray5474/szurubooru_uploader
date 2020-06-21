import sys
import os
import time
import cv2

# PyQt Imports TODO: make this look better
from PyQt5.QtCore       import Qt, pyqtSignal, QSize, QVariant
from PyQt5.QtGui        import QPixmap, QIcon, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets    import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar, QTableView, QFileDialog, QAbstractItemView, QScrollArea, QLayout

from FileExts           import FileExts     # File extension lists
from Debug              import Debug as dbg # Debug variables
from Fonts              import Fonts        # Fonts Class
from Colors             import Colors       # Colors Class

from ImportFiles        import ImportFiles  # ImporttFiles QThread
from FlowLayout         import FlowLayout   # Flow layout

WIDTH = 900                                 # Starting width
HEIGHT = 500                                # Starting height

FILE_IMPORT = "./assets/file-import.svg"    # File import icon

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
    self.tab_widget = MainGUI(self)
    self.setCentralWidget(self.tab_widget)

    print(f"Finished initializing application in {(time.time() - application_start) * 1000}ms.")

    self.show()

class MainGUI(QWidget):

  def __init__(self, parent):

    super(MainGUI, self).__init__(parent)

    self.cell_width = 175
    self.cell_height = 175
    self.thumb_grid_column_count = 7 # Will be gone soon

    self.layout = QVBoxLayout(self)

    # This is needed to keep it looking clean and centered
    self.layout.setContentsMargins(0, 0, 0, 0)
    self.layout.setAlignment(Qt.AlignCenter)

    # Create self.home_title
    self.home_title = QLabel("szurubooru_uploader")

    self.home_title.setObjectName("homeTitle")
    self.home_title.setFont(Fonts.NotoSansDisplay("ExtraLight", 40))
    self.home_title.setAlignment(Qt.AlignCenter)

    # Create self.home_desc
    self.home_desc = QLabel("Uploading and Tagging helper for szurubooru")

    self.home_desc.setObjectName("homeDesc")
    self.home_desc.setFont(Fonts.NotoSansDisplay("Light Italic", 15))
    self.home_desc.setAlignment(Qt.AlignCenter)

    # Create open_folder
    self.open_folder = QPushButton(" Import folder")

    self.open_folder.clicked.connect(self.pick_folder)
    self.open_folder.setObjectName("openFolder")
    self.open_folder.setFont(Fonts.NotoSansDisplay("Italic", 12))
    self.open_folder.setIcon(QIcon(QPixmap(FILE_IMPORT)))
    self.open_folder.setIconSize(QSize(14, 14))

    # Create main thumbnail layout, wrapper, and scroll area (but don't insert)
    # The QScrollArea is the parent of a QWidget which is the wrapper and parent of a QLayout
    # Why? I have no idea
    self.thumb_layout_scroll_area = QScrollArea()
    self.thumb_layout_wrapper = QWidget(self.thumb_layout_scroll_area)
    self.thumb_layout = FlowLayout(self.thumb_layout_wrapper, -1, 5, 5)

    # Create progressbar (but don't insert!)
    self.loading_progressbar = QProgressBar()

    self.loading_progressbar.setFont(Fonts.NotoSansDisplay("Regular", 5))
    self.loading_progressbar.setAlignment(Qt.AlignCenter)
    self.loading_progressbar.setFixedHeight(10)

    # Assemble initial UI
    self.layout.addStretch(1)
    self.layout.addWidget(self.home_title)
    self.layout.addWidget(self.home_desc)
    self.layout.addStretch(1)
    self.layout.addWidget(self.open_folder)
    self.layout.addStretch(1)

    self.setLayout(self.layout)

  def resizeEvent(self, event):
    # Override the resizeEvent of the main window to update thumb_layout_wrapper's size
    # This is important since the size of the layout is fully dependent on the size of the wrapper
    # And obviously, the wrapper's size won't automatically change

    self.thumb_layout_wrapper.setFixedSize(self.thumb_layout_scroll_area.size())

  def count_files(self, folder_path):

    self.file_count = 0

    for root, dirs, files in os.walk(folder_path):

      for name in files:

        ext = name.split('.')[-1]
        if ext in FileExts.image_exts or ext in FileExts.video_exts or ext in FileExts.misc_exts:

          self.file_count += 1

  def pick_folder(self):

    print("Picking folder...")

    # Launch file picker if debug is diabled
    if dbg.ENABLED:

      folder_path = dbg.PATH

    else:

      folder_path = QFileDialog.getExistingDirectory(self, "Select folder", "./", QFileDialog.ShowDirsOnly)

    # If we get a file then move on
    if folder_path != '':

      self.count_files(folder_path)

      print(f"Selected \"{folder_path}\", contains {self.file_count} files.")

      self.layout.removeWidget(self.open_folder)
      self.open_folder.close()

      self.start_import_files_thread(folder_path)

  def reorganize_ui(self):

    # Remove widgets in preperation for repositioning
    self.layout.removeWidget(self.home_title)
    self.layout.removeWidget(self.home_desc)
    self.layout.removeWidget(self.open_folder)
    self.home_desc.close()

    # Renovate home_title
    self.home_title.setFont(Fonts.NotoSansDisplay("Light Italic", 14))
    self.home_title.setAlignment(Qt.AlignLeft)
    self.home_title.setContentsMargins(15, 5, 0, 0)

    # Re-add widgets and layouts
    self.layout.addWidget(self.thumb_layout_scroll_area)
    self.layout.addWidget(self.loading_progressbar)
    self.layout.insertWidget(0, self.home_title)

    # Re-adjust stretches
    self.layout.setStretch(2, 0)
    self.layout.setStretchFactor(self.thumb_layout_scroll_area, 150)


  def start_import_files_thread(self, folder_path):

    print("Starting thread...")

    self.reorganize_ui()

    # Prepare progressbar
    self.loading_progressbar.setMaximum(self.file_count)
    self.loading_progressbar.setFormat("%v/%m files inported...")

    # Begin thread
    self.import_files_thread = ImportFiles(folder_path, self.cell_width, self.cell_height)

    self.import_files_thread.finished.connect(self.post_load)
    self.import_files_thread.add_thumbnail_to_grid.connect(self.add_thumbnail_to_grid)

    # Start timing loading process
    self.load_start = time.time()

    self.import_files_thread.start()

  # SIGNALS

  def add_thumbnail_to_grid(self, thumbnail):

    # Increment progressbar value
    self.loading_progressbar.setValue(self.loading_progressbar.value() + 1)

    # Set the size of the wrapper for thumb_layout to the size of the QScrollArea it's in
    # For some reason you can only do this 
    self.thumb_layout_wrapper.setFixedSize(self.thumb_layout_scroll_area.size())

    # Create item to add to our layout, and pixmap
    self.item = QLabel()
    self.thumb_data = QPixmap()
    
    # Load bytearray into the pixmap
    self.thumb_data.loadFromData(thumbnail)

    # Attach the pixmap to the label
    self.item.setPixmap(self.thumb_data)

    # Add the item to the layout
    self.item.setFixedWidth(self.item.sizeHint().width())
    self.thumb_layout.addWidget(self.item)
    self.thumb_layout_scroll_area.setWidget(self.thumb_layout_wrapper)

  def post_load(self):

    # Remove progressbar
    self.loading_progressbar.setVisible(False)
    self.layout.removeWidget(self.loading_progressbar)
    self.loading_progressbar.close()


    print(f"Loading finished in {(time.time() - self.load_start) * 1000}ms.")

if __name__ == '__main__':

  # Initialize app
  app = QApplication(sys.argv)
  app.setStyleSheet(open(STYLES, 'r').read())
  ex = App()
  sys.exit(app.exec_())

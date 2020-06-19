import sys
import os
import time
import cv2

# PyQt Imports TODO: make this look better
from PyQt5.QtCore       import Qt, QThread, pyqtSignal, QSize, QVariant
from PyQt5.QtGui        import QPixmap, QIcon, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets    import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QTableView, QFileDialog, QAbstractItemView

from FileExts           import FileExts     # File extension lists
from Debug              import Debug as dbg # Debug variables
from Fonts              import Fonts        # Fonts Class
from Colors             import Colors       # Colors Class

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

    # Create main photos grid (but don't insert!)
    self.thumb_grid_model = QStandardItemModel()
    self.thumb_grid_view = QTableView()

    self.thumb_grid_view.horizontalHeader().hide()
    self.thumb_grid_view.verticalHeader().hide()

    self.thumb_grid_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
    self.thumb_grid_view.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)

    self.thumb_grid_view.setFont(Fonts.NotoSansDisplay("Regular", 10))

    # Create progressbar (but don't insert!)
    self.loading_progressbar = QProgressBar()

    self.loading_progressbar.setFont(Fonts.NotoSansDisplay("Regular", 5))
    self.loading_progressbar.setAlignment(Qt.AlignCenter)
    self.loading_progressbar.setFixedHeight(10)

    self.layout.addStretch(1)
    self.layout.addWidget(self.home_title)
    self.layout.addWidget(self.home_desc)
    self.layout.addStretch(1)
    self.layout.addWidget(self.open_folder)
    self.layout.addStretch(1)

    self.setLayout(self.layout)

  def count_files(self, folder_path):
    self.file_count = 0

    for root, dirs, files in os.walk(folder_path):
      for name in files:
        ext = name.split('.')[-1]
        if ext in FileExts.image_exts or ext in FileExts.video_exts or ext in FileExts.misc_exts:
          self.file_count += 1

  def pick_folder(self):
    print("Picking folder...")
    
    if dbg.ENABLED:
      folder_path = dbg.PATH
    else:
      folder_path = QFileDialog.getExistingDirectory(self, "Select folder", "./", QFileDialog.ShowDirsOnly)

    if folder_path != '':
      self.count_files(folder_path)

      print(f"Selected \"{folder_path}\", contains {self.file_count} files.")

      self.layout.removeWidget(self.open_folder)
      self.open_folder.close()

      self.start_import_files_thread(folder_path)

  def reorganize_ui(self):
    self.layout.removeWidget(self.home_title)
    self.layout.removeWidget(self.home_desc)
    self.layout.removeWidget(self.open_folder)

    self.home_title.setFont(Fonts.NotoSansDisplay("Light Italic", 14))
    self.home_title.setAlignment(Qt.AlignLeft)
    self.home_title.setContentsMargins(15, 5, 0, 0)

    self.layout.addWidget(self.thumb_grid_view)
    self.layout.addWidget(self.loading_progressbar)
    self.layout.insertWidget(0, self.home_title)

    self.home_desc.close()

    #self.layout.setStretch(0, 0)
    self.layout.setStretch(2, 0)
    #self.layout.setStretch(5, 0)

    self.layout.setStretchFactor(self.thumb_grid_view, 150)

  def start_import_files_thread(self, folder_path):
    print("Starting thread...")

    self.thumb_grid_column_count = 7
    self.thumb_grid_column_idx = 0
    self.thumb_grid_row_idx = 0

    self.reorganize_ui()

    self.loading_progressbar.setMaximum(self.file_count)
    self.loading_progressbar.setFormat("%v/%m files inported...")

    # Begin thread
    self.import_files_thread = ImportFilesThreadClass(folder_path, self.cell_width, self.cell_height)

    self.import_files_thread.finished.connect(self.post_load)
    self.import_files_thread.add_thumbnail_to_grid.connect(self.add_thumbnail_to_grid)

    self.load_start = time.time() # Start timing loading

    self.import_files_thread.start()

  # SIGNALS

  def add_thumbnail_to_grid(self, thumbnail):
    self.loading_progressbar.setValue(self.loading_progressbar.value() + 1)

    # Put icon thumbnails in cells
    item_thumbnail = QPixmap()
    item = QStandardItem()

    item_thumbnail.loadFromData(thumbnail)

    item.setData(QVariant(item_thumbnail), Qt.DecorationRole)

    self.thumb_grid_model.setItem(self.thumb_grid_row_idx, self.thumb_grid_column_idx, item)

    self.thumb_grid_view.setModel(self.thumb_grid_model)

    # Set column widths for the first row only
    if self.thumb_grid_row_idx == 0:
      self.thumb_grid_view.setColumnWidth(self.thumb_grid_column_idx, self.cell_width)

    # Move to next item
    if self.thumb_grid_column_idx < self.thumb_grid_column_count:
      if self.thumb_grid_column_idx == 0:

        # Set row height if starting new row
        self.thumb_grid_view.setRowHeight(self.thumb_grid_row_idx, self.cell_height)
      self.thumb_grid_column_idx += 1
    else:
      self.thumb_grid_row_idx += 1
      self.thumb_grid_column_idx = 0

  def post_load(self):

    self.loading_progressbar.setVisible(False)
    self.layout.removeWidget(self.loading_progressbar)
    self.loading_progressbar.close()

    print(f"Loading finished in {(time.time() - self.load_start) * 1000}ms.")

class ImportFilesThreadClass(QThread):

  finished = pyqtSignal()
  add_thumbnail_to_grid = pyqtSignal(bytes)

  def __init__(self, folder_path, thumb_width, thumb_height):
    super(ImportFilesThreadClass, self).__init__()

    self.folder_path = folder_path
    self.thumb_width = thumb_width - 5 # Subtract one because of weird cell things
    self.thumb_height = thumb_height
    self.files = os.scandir(self.folder_path)

  def run(self):

    print("Loading images...")

    for file in self.files:

      print(f"Processing \"{file.name}\"")

      if file.is_file(): # Only process files, not directories

        file_ext = file.name.split('.')[-1]

        if file_ext in FileExts.image_exts: # For image files...

          # Read image from file
          im = cv2.imread(file.path)

          # Resize image
          im = self.proper_resize(im)

          # Encode image into bytearrray
          img_byte_array = bytes(cv2.imencode(".png", im)[1])

          # Send bytearray to the thumbnail adding function
          self.add_thumbnail_to_grid.emit(img_byte_array)

          # Cleanup
          im = None
          img_byte_array = None

        elif file_ext in FileExts.video_exts: # For video files...
          
          # Read video file
          frames = cv2.VideoCapture(file.path)

          # Resize frame | !!! .read()'s result is a tuple, the second value is the ndarray we need.
          first_frame = self.proper_resize(frames.read()[1])

          # Encode first frame into bytearray
          img_byte_array = bytes(cv2.imencode(".png", first_frame)[1])

          # Send bytearray
          self.add_thumbnail_to_grid.emit(img_byte_array)

          # Cleanup
          frames.release()
          cv2.destroyAllWindows()
            
    self.finished.emit()

  def proper_resize(self, img_data):

    width = img_data.shape[1]
    height = img_data.shape[0]

    if(width >= height):

      new_side_length = int(height * (self.thumb_width / (width)))
      img_data = cv2.resize(img_data, (self.thumb_width, new_side_length))

    elif (width <= height):

      new_side_length = int(width * (self.thumb_height / (height)))
      img_data = cv2.resize(img_data, (new_side_length, self.thumb_width))
    
    return img_data
    
if __name__ == '__main__':
  app = QApplication(sys.argv)
  app.setStyleSheet(open(STYLES, 'r').read())
  ex = App()
  sys.exit(app.exec_())

import os
import time

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QProgressBar, QFileDialog

from assets.Colors import Colors
from assets.FileExts import FileExts
from assets.Fonts import Fonts

from gui.FlowLayout import FlowLayout

from items.DatesectionItem import DatesectionItem
from items.ThumbnailItem import ThumbnailItem

from loading.ImportFiles import ImportFiles

from meta.Debug import Debug as dbg

FILE_IMPORT_ICON = "../assets/file-import.svg"

class MainGui(QWidget):

  def __init__(self, parent):

    super(MainGui, self).__init__(parent)

    # The height of each thumbnail
    self.thumb_height = 200

    # A list of thumbnails, no markers, each entry is a dict:
    # {"idx": int, "date": str, "time": str, "safety": str, "tags": list)
    # "idx" being the thumbnail's location in the layout
    self.thumb_list = []

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
    self.open_folder.setIcon(QIcon(QPixmap(FILE_IMPORT_ICON)))
    self.open_folder.setIconSize(QSize(14, 14))

    # Create main thumbnail layout, wrapper, and scroll area (but don't insert)
    # The QScrollArea is the parent of a QWidget which is the wrapper and parent of a QLayout
    # Why? I have no idea
    self.thumb_layout_scroll_area = QScrollArea()
    self.thumb_layout_wrapper = QWidget(self.thumb_layout_scroll_area)
    self.thumb_layout = FlowLayout(self.thumb_layout_wrapper, -1, 5, 5)

    self.thumb_layout.update_wrapper_height.connect(self.update_thumb_layout_wrapper_height)
    
    self.thumb_layout_wrapper.setVisible(False)

    # Create progressbar (but don't insert!)
    self.loading_progressbar = QProgressBar()

    self.loading_progressbar.setFont(Fonts.NotoSansDisplay("Regular", 6))
    self.loading_progressbar.setAlignment(Qt.AlignLeft)
    self.loading_progressbar.setFixedHeight(12)

    # Assemble initial UI
    self.layout.addStretch(1)
    self.layout.addWidget(self.home_title)
    self.layout.addWidget(self.home_desc)
    self.layout.addStretch(1)
    self.layout.addWidget(self.open_folder)
    self.layout.addStretch(1)

    self.setLayout(self.layout)

  def resizeEvent(self, event):
    # Override the resizeEvent of the main window to to automatically update the wrapper's width
    # to what is needed, since it doesn't update by itself.

    self.thumb_layout_wrapper.setFixedWidth(self.thumb_layout_scroll_area.size().width())

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

    self.loading_progressbar.setVisible(True)

    # Begin thread
    self.import_files_thread = ImportFiles(folder_path, self.thumb_height)

    self.import_files_thread.send_thumbnails_signal.connect(self.add_thumbnails_to_grid)    
    self.import_files_thread.format_progressbar.connect(self.format_progressbar)
    self.import_files_thread.max_progressbar.connect(self.max_progressbar)
    self.import_files_thread.increment_progressbar.connect(self.increment_progressbar)

    # Start timing loading process
    self.load_start = time.time()

    self.import_files_thread.start()

  # SIGNALS

  def format_progressbar(self, fmt):
    # Allows the loading thread to change the format of the progressbar

    # Reset the progressbar first because we only call this at the start of a new operation
    self.loading_progressbar.reset()

    # We add a space before the text because setContentsMargins doesn't work on QProgressbars fsr
    self.loading_progressbar.setFormat(f" {fmt}")

  def max_progressbar(self, val):
    # Allows the loading thread to set the maximum value of the progressbar

    self.loading_progressbar.setMaximum(val)

  def increment_progressbar(self):
    # Allows the loading thread to increment the progressbar

    self.loading_progressbar.setValue(self.loading_progressbar.value() + 1)

  def show_thumb_layout(self):
    # Allows the loading thread to show the thumb layout only right before the thumbnail insertion

    self.thumb_layout_wrapper.setVisible(True)

  def add_thumbnails_to_grid(self, thumbs_list):
    # Adds each thumbnail from the given list to the thumb layout

    print(f"Adding {len(thumbs_list)} total elements to the layout...")

    for idx, (data, path, creation_date, creation_time) in enumerate(thumbs_list):

      # If the previous date isn't the current date or if we are at the start, add a datesection
      if not thumbs_list[idx - 1] or thumbs_list[idx - 1][1] != creation_date:

        # Initialize custom Datesection item
        datesection = DatesectionItem()

        # Set text of Datesection item to "Unknown Date" if no date found
        if creation_date[0] == "0000": 

          datesection.setText("Unknown Date")
        
        else:
          
          # Otherwise make it the date
          datesection.setDate(creation_date[0], creation_date[1], creation_date[2])

        self.thumb_layout.addWidget(datesection)

      # Create item to add to our layout, and load the bytearray into it
      item = ThumbnailItem()
      item.loadFromData(data)

      # Add the item to the layout
      self.thumb_layout.addWidget(item)
      self.thumb_layout_scroll_area.setWidget(self.thumb_layout_wrapper)

      # Add an entry to our thumbs list
      current_thumb_dict = {
        "path": path,
        "ext": path.split('.')[-1]
        "date": creation_date,
        "time": creation_time,
        "widget": item,
        "tags": []
        "selected": False,
        "safety": ''}

      self.thumb_list.append(current_thumb_dict.copy())

      # Increment progressbar
      self.increment_progressbar()
    
    # Finally, cleanup and perform post-load actions
    thumbs_list = None
    self.post_load()

  def update_thumb_layout_wrapper_height(self, height):
    # Allows the FlowLayout to set the height it needs *when it's ready*
    # Before, the height was set after all the thumbnail-adding was complete, leading to a race
    # condition problem. To sovle that, this is run everytime the layout is updated to avoid that.

    self.thumb_layout_wrapper.setFixedHeight(height) 

  def post_load(self):

    # Remove progressbar
    self.loading_progressbar.setVisible(False)
    self.layout.removeWidget(self.loading_progressbar)
    self.loading_progressbar.close()

    # Set the size of the wrapper for thumb_layout to the size of the QScrollArea it's in
    self.thumb_layout_wrapper.setFixedWidth(self.thumb_layout_scroll_area.size().width())

    print(f"Loading finished in {(time.time() - self.load_start) * 1000}ms.")

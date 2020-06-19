import os
import cv2

from PyQt5.QtCore import QThread, pyqtSignal

from FileExts     import FileExts

class ImportFiles(QThread):

  finished = pyqtSignal()
  add_thumbnail_to_grid = pyqtSignal(bytes)

  def __init__(self, folder_path, thumb_width, thumb_height):

    super(ImportFiles, self).__init__()

    self.folder_path = folder_path
    self.thumb_width = thumb_width - 5 # Subtract one because of weird cell things
    self.thumb_height = thumb_height
    self.files = os.scandir(self.folder_path)

  def run(self):

    print("Loading images...")

    # Go through each file
    for file in self.files:

      print(f"Processing \"{file.name}\"")

      # Only process files, not directories
      if file.is_file():

        file_ext = file.name.split('.')[-1]

        if file_ext in FileExts.image_exts: # For image files...

          # Read image from file
          try:

            im = cv2.imread(file.path)

          except cv2.error().code as e: # TODO: Add separate function to show why loading failed in grid

            print(f"Error while loading {file.name} with error {e}")

          else:

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
          try:

            frames = cv2.VideoCapture(file.path)

          except cv2.error().code as e: # TODO: same as the images

            print(f"Error while loading {file.name} with error {e}")

          else:

            # Resize frame | !!! .read() result is a tuple, the 2nd value is the ndarray we need.
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

    # Calculates the proportion of the length of the longest side of the image to the desired
    # longth of said side, then decreases the size of the other side by the proportion.
    if(width >= height):

      new_side_length = int(height * (self.thumb_width / (width)))
      img_data = cv2.resize(img_data, (self.thumb_width, new_side_length))

    elif (width <= height):

      new_side_length = int(width * (self.thumb_height / (height)))
      img_data = cv2.resize(img_data, (new_side_length, self.thumb_width))
    
    return img_data

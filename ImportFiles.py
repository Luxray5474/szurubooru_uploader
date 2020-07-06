import os
import subprocess
import cv2
import re

from PIL          import Image

from PyQt5.QtCore import QThread, pyqtSignal

from FileExts     import FileExts

class ImportFiles(QThread):

  # Emmitted when we are ready to send the whole list of thumbnails to the main thread
  # This also acts as a finished signal.
  send_thumbnails_signal = pyqtSignal(list)

  # Emmitted in order to format and modify the progressbar
  format_progressbar = pyqtSignal(str)
  max_progressbar = pyqtSignal(int)
  increment_progressbar = pyqtSignal()

  def __init__(self, folder_path, thumb_height):

    super(ImportFiles, self).__init__()

    self.folder_path = folder_path
    self.thumb_height = thumb_height
    self.files = os.scandir(self.folder_path)

    self.file_count = 0

    for root, dirs, files in os.walk(folder_path):

      for name in files:

        # Make sure these are lowercased, some extensions are all caps  
        ext = name.split('.')[-1].lower()

        if ext in FileExts.image_exts or ext in FileExts.video_exts or ext in FileExts.misc_exts:

          self.file_count += 1

  def run(self):
    # Main function that gets moved to the separate thread

    print("Processing files...")

    # First, generate thumbnails and put it that and metadata into a list
    thumbnails = self.generate_thumbnails(self.files)

    # Then, sort those thumbnails by date and time created
    thumbnails.sort(reverse=True, key=lambda tup: (tup[1], tup[2]))

    # Finally, send the thumbnails and section markers over to the main thread
    self.send_thumbnails(thumbnails)

  def generate_thumbnails(self, raw_files):
    # Generates thumbnails from files found in the selected directory
    # Returns an array of tuples which contain (img_byte_array, creation_date, creation_time)
    # Each tuple corresponds to a thumbnail of an image or video, or if it's an SWF, a placeholder

    # The array we will add each thumbnail's tuple to
    thumbs = []

    # Format progressbar to display current action
    self.format_progressbar.emit("Generating thumbnails - %v/%m")
    self.max_progressbar.emit(self.file_count)

    for file in raw_files:

      print(f"Processing \"{file.name}\"")

      # Only process files, not directories
      if file.is_file():

        file_ext = file.name.split('.')[-1].lower()

        if file_ext in FileExts.image_exts: # For image files...

          # Read image from file
          try:

            im = cv2.imread(file.path)

          except cv2.error().code as e: # TODO: Add separate function to show why loading failed in grid

            print(f"Error while loading {file.name} with error {e}")

          else:

            # Resize image
            im = self.proper_resize(im, self.thumb_height)

            # Encode image into bytearrray
            img_byte_array = bytes(cv2.imencode(".png", im)[1])

            # Open image with PIL (i die) and get creation date metadata which is under "306"
            pil_image = Image.open(file.path)

            exif_data = None

            # We use try block because some images do not contain EXIF metadata.
            try:

              exif_data = pil_image._getexif()

              # Get the creation date and time
              creation_date = exif_data[306].split(' ')[0]
              creation_time = exif_data[306].split(' ')[1]

            except: # Triggered when a key isn't in the image EXIF

              print(f"Could not find creation_date or creation_time in {file.name}")
              
              # Setting date and time to zeroes makes the image last in the list
              creation_date = "0000-00-00"
              creation_time = "00:00:00"

            # Cleanup
            im = None

        elif file_ext in FileExts.video_exts: # For video files...
            
          # Get video metadata
          metadata = self.get_video_metadata(file.path)

          # Only attempt to load the video if ffmpeg is able to get metadata
          # This prevents ffmpeg inside cv2 from printing an unhandleable error
          if metadata == False:

            print(f"Error: Loading {file.name} failed, moov atom not found. Skipping...")

          else:

            creation_date = metadata[0]
            creation_time = metadata[1]

            # Read video file
            try:

              frames = cv2.VideoCapture(file.path)
              first_frame = frames.read()[1]

            except cv2.error().code as e: # TODO: same as the images

              print(f"Error while loading {file.name} with error {e}")
              exit(1)

            else:

              # Resize frame | !!! .read() result is a tuple, the 2nd value is the ndarray we need.
              resized_first_frame = self.proper_resize(first_frame, self.thumb_height)

              # Encode first frame into bytearray
              img_byte_array = bytes(cv2.imencode(".png", resized_first_frame)[1])

              # Free up memory
              frames.release()
              cv2.destroyAllWindows()

      # Split dates/times by any non-number character into tuple for consistency
      creation_date = tuple(re.split("[^0-9]", creation_date))
      creation_time = tuple(re.split("[^0-9]", creation_time))

      # Add the bytearray and info to the list
      thumbs.append((img_byte_array, creation_date, creation_time))

      # Increment progressbar after every cycle
      self.increment_progressbar.emit()

    return thumbs

  def send_thumbnails(self, thumbs):
    # Sends the whole list of thumbnails to the main thread using pyqtSignals
    # This used to have a for loop sending each tuple in the list one by one.
    # However, this created a premature finish problem, because the thread would emit the next
    # signal regardless of whether it was finished or not. Then, it would emit the finished signal
    # before all the thumbnails have been added. 

    print("Sending thumbnails...")

    # Format the progressbar
    self.format_progressbar.emit("Inserting thumbnails - %v/%m")
    self.max_progressbar.emit(len(thumbs))

    # Send the list
    self.send_thumbnails_signal.emit(thumbs) 

    # We don't need this list anymore after that
    thumbs = None

  def get_video_metadata(self, path):
    # Gets metadata for video files, separate function because it's quite long
    # Returns a tuple of (creation_date, creation_time)

    # We use try block because we need to catch an exception
    try:

      # Use subprocess to run a command, and collect its output
      # For some reason, when FFMPEG errors, it outputs *all* output into atderr, so we have
      # to pipe it to stdout.
      process = subprocess.check_output(["ffmpeg", "-i", path], stderr=subprocess.STDOUT)

    except subprocess.CalledProcessError as err:

      # We deliberately "ignore" the error ffmpeg emits when no output is selected, since
      # we don't need an output, only the metadata and information. We then take the output of
      # the command and decode it since it comes in bytes
      output = err.output.decode("ascii")

    except FileNotFoundError:

      # Of course, if ffmpeg isn't even there, we warn the user and can't move on.
      print("FATAL: ffmpeg not found, that most likely means you don't have it installed.")
      exit(1)

    # Skip if ffmpeg returns a moov atom not found error
    if re.search(r"moov", output):

      return False

    else:

      # Attempt to find the creation date in metadata
      try:

        # If it's stupid but works, it ain't stupid.
        # 1. get whatever is after the first "creation_time"
        # 2. get whatever is before the 'Z'
        # 3. get whatever is after the ": "
        # 4. split by 'T'
        creation = output.split("creation_time")[1].split('Z')[0].split(": ")[1].split('T')

      except IndexError:

        # If we cannot split the output by "creation_time", assume it doesn't exist
        creation_date = "0000-00-00"
        creation_time = "00:00:00"

      else:

        creation_date = creation[0]
        creation_time = creation[1].split('.')[0]

      # Return a tuple of the collected information
      return (creation_date, creation_time)

  def proper_resize(self, img_data, desired_height):
    # Calculates the proportion of the desired height to the original height, then resizes the
    # length of the image by the proportion, and the height of the image to the desired height.
    # We only care about the height because the thumbs need to be a uniform height.

    width = img_data.shape[1]
    height = img_data.shape[0]

    new_length = int(width * (desired_height / (height)))
    img_data = cv2.resize(img_data, (new_length, desired_height))

    return img_data

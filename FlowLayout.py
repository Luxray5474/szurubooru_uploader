from PyQt5.QtCore     import Qt, QRect, QSize, QPoint, pyqtSignal
from PyQt5.QtWidgets  import QLayout, QSizePolicy, QStyle

class FlowLayout(QLayout):

  # This signal is used to update the wrapper's height every layout update.
  update_wrapper_height = pyqtSignal(int)

  def __init__(self, parent=None, margin=-1, hspacing=-1, vspacing=-1):

    super(FlowLayout, self).__init__(parent)

    self.h_spacing = hspacing
    self.v_spacing = vspacing

    self.items = []

    self.total_height = 0

    self.setContentsMargins(margin, margin, margin, margin)

  def __del__(self):
    # Destroy the layout

    del self.items[:]

  def addItem(self, item):
    # When we add an item, e.g. using addWidget(), just append it to a list

    self.items.append(item)

  def horizontalSpacing(self):
    # This gets the horizontal spacing between widgets

    if self.h_spacing >= 0:

      # If an h_spacing value is provided, use it
      return self.h_spacing

    else:

      # If not, calculate it
      return self.smartSpacing(QStyle.PM_LayoutHorizontalSpacing)

  def verticalSpacing(self):
    # This gets the vertical spacing between widgets

    if self.v_spacing >= 0:
      
      # If a v_spacing value is provided, use it
      return self.v_spacing

    else:
      
      # If not, calculate it
      return self.smartSpacing(QStyle.PM_LayoutVerticalSpacing)

  def count(self):
    # why.....?

    return len(self.items)

  def itemAt(self, index):
    # Get an item at a given index

    # If index is in the list, return the item at the index    
    if 0 <= index < len(self.items):

      return self.items[index]

  def takeAt(self, index):
    # Remove an item at a given index

    # If index is in the list, remove the item at the index and return it
    if 0 <= index < len(self.items):

      return self.items.pop(index)

  def expandingDirections(self):
    # This gives us the Qt Orientations available to the layout

    return Qt.Orientations(0)

  def hasHeightForWidth(self):
    # why.
    
    return True

  def heightForWidth(self, width):
    # This adjusts to widgets whose height depends on width

    return self.doLayout(QRect(0, 0, width, 0), True)

  def setGeometry(self, rect):
    # This is normally used to do layout, but here it passes a rect to the actual function

    super(FlowLayout, self).setGeometry(rect)
    self.total_height = self.doLayout(rect, False)

    # Update the wrapper height
    self.update_wrapper_height.emit(self.total_height)

  def sizeHint(self):
    # Returns the minimum size of the layout

    return self.minimumSize()

  def minimumSize(self):
    # Returns the minimum size of the layout

    # Initialize a QSize object
    size = QSize()

    # For each item, expand the QSize object to each one's minimum size
    for item in self.items:

      size = size.expandedTo(item.minimumSize())

    # Get the margins
    left, top, right, bottom = self.getContentsMargins()

    # Add another QSize object to acknowledge  the margins, and return it
    size += QSize(left + right, top + bottom)
    return size

  def doLayout(self, rect, test_only):
    # This function actually does the layout management and placement
    
    # Pass the margins into these four variables respectively
    left, top, right, bottom = self.getContentsMargins()

    # This effective area is a rectangle that is adjusted to fit into the margins.
    # left and top's values are added to its left and top sides
    # right and bottom are subtracted from its right and bottom sides
    effective = rect.adjusted(+left, +top, -right, -bottom)

    # The "starting" position of the first widget (top left)
    x = effective.x()
    y = effective.y()

    line_height = 0

    # Go through each item in the list
    for item in self.items:

      widget = item.widget()

      # Use the horizontal and vertical spacing between items
      h_space = self.horizontalSpacing()
      v_space = self.verticalSpacing()

      if h_space == -1:
        # If somehow h_space is -1 we use the widget's style to space them
        
        h_space = widget.style().layoutSpacing(
          QSizePolicy.PushButton,
          QSizePolicy.PushButton,
          Qt.Horizontal)

      if v_space == -1:
        # Same with this
        
        v_space = widget.style().layoutSpacing(
          QSizePolicy.PushButton,
          QSizePolicy.PushButton,
          Qt.Vertical)

      # Add the current item width and h_spacing to the current position to get the starting
      # position for the next item
      next_x = x + item.sizeHint().width() + h_space

      if next_x - h_space > effective.right() and line_height > 0 or \
         widget.newline_before == True:
        # If the next position oversteps the right side of the effective area, "wrap around"

        # Make the starting x pos of the next item the left of the effective area
        x = effective.x() 
        next_x = x + item.sizeHint().width() + h_space

        # Make the starting y pos of the next item the line height plus vert. spacing
        y = y + line_height + v_space

        # Reset the line height
        line_height = 0

      if not test_only:
        # Place the item if we aren't simulating the positioning

        # Position the current item on the current position
        item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

      # Set line height to the tallest item
      line_height = max(line_height, item.sizeHint().height())

      if widget.newline_after == True:
        # If the widget needs a newline after, start a new line again

        # Just add to the y...
        y = y + line_height + v_space

      else:
        # Otherwise, move the x in preperation for the next item
        
        x = next_x

    # Return the height of the current line
    return y + line_height - rect.y() + bottom
  
  def smartSpacing(self, pm):
    # Gets the default spacing for top level or sublayouts

    parent = self.parent()

    if parent is None:
    
      return -1
    
    elif parent.isWidgetType():
      
      parent.style().pixelMetric(pm, None, parent)

    else:

      return parent.spacing()
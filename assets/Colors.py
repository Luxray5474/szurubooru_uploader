from PyQt5.QtGui import QColor

class Colors:

  # Colors are from Ayu Dark and Mirage

  # Common colors
  bg =           "#0A0E14"
  bg_line =      "#00010A"
  fg =           "#B3B1AD"
  fg_special =   "#FFB454"
  fg_light =     "#3D424D"

  # Regular colors
  fg_red =       "#FF3333"
  fg_green =     "#C2D94C"
  fg_blue =      "#39BAE6"
  fg_orange =    "#FE8E41"

  # Faded colors
  fg_f_red =     "#D96C75"
  fg_f_green =   "#91B362"
  fg_f_blue =    "#6994BF"
  fg_f_orange =  "#E1B56F"

  # Light colors
  fg_l_red =     "#F07178"
  fg_l_blue =    "#95E6CB"
  fg_l_yellow =  "#FCED95"

  # Mirage Common
  mirage_bg =    "#1F2430"

  def rgb(color):

    h = color.lstrip('#')
    return(tuple(int(h[i:i+2], 16) for i in (0, 2, 4)))
  
  def QCol(color):
    
    return(QColor(*Colors.rgb(color)))

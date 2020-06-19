from PyQt5.QtGui      import QFont, QFontDatabase

class Fonts:

  def init():

    styles = ["ExtraLight", "Light", "LightItalic", "Regular", "Italic", "Bold"]

    for i in styles:

      QFontDatabase.addApplicationFont(f"./assets/fonts/NotoSansDisplay/NotoSansDisplay-{i}.ttf")

  def NotoSansDisplay(style, size):

    return QFont(f"Noto Sans Display {style}", size)
import sys
import os
from pathlib import Path
APP_PATH = Path(__file__).parent
ROOT_PATH = APP_PATH.parent.parent
sys.path.extend([str(APP_PATH), str(ROOT_PATH)])

os.chdir(APP_PATH)

from guiml.core import Window
import todo
import todolist


def main():
  window = Window("root.xml")
  window.run()


if __name__ == '__main__':
  main()
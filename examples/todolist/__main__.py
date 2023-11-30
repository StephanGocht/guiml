import sys
import os
from pathlib import Path

APP_PATH = Path(__file__).parent
ROOT_PATH = APP_PATH.parent.parent
sys.path.extend([str(APP_PATH), str(ROOT_PATH)])

os.chdir(APP_PATH)

from guiml.components import component, Component
from guiml.core import run

import todo
import todolist

from resources import resources as res


@component("application", res.template_file("root.xml"))
class Application(Component):
    pass


def main():
    run(interval=1 / 32)


if __name__ == '__main__':
    main()

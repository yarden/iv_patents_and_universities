##
## Paths
##
import os
import sys
import time

import utils

MAIN_DIR = \
  os.path.join(os.path.dirname(os.path.join(os.path.realpath(__file__))),
               "..")

DATA_DIR = os.path.realpath(os.path.join(MAIN_DIR, "data"))

PLOTS_DIR = os.path.join(MAIN_DIR, "plots")
utils.make_dir(PLOTS_DIR)

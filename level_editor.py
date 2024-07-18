import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *
    
import random

from scripts.config.SETTINGS import SIZE, FPS
from scripts.utils.CORE_FUNCS import vec

pygame.Rect = pygame.FRect

    ##############################################################################################

class Editor:
    def __init__(self):
        pass
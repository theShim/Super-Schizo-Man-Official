import contextlib
from typing import Any
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import random
import math

from scripts.utils.CORE_FUNCS import vec
from scripts.config.SETTINGS import Z_LAYERS, WIDTH, HEIGHT

    ##############################################################################################

ENVIRONMENT_SETTINGS: dict[str, bool | int] = {
    "rain" : False,
    "snow" : False,
    "cherry_blossom" : False,
    "wind" : -2
}

class Environment_Manager:
    def __init__(self, game, stage):
        self.game = game
        self.stage = stage

        self.weather = {
            "rain" : False,
            "snow" : False,
        }

        self.wind = -2

        self.light = 100

    def update(self):
        keys = pygame.key.get_pressed()

        #light
        if keys[pygame.K_COMMA]:
            self.light = max(0, self.light - (self.game.dt * 100))
        if keys[pygame.K_PERIOD]:
            self.light = min(255, self.light + (self.game.dt * 100))

        #weather
        if self.weather["rain"]:
            for i in range(random.randint(1, 6)):
                self.game.state_loader.current_state.particle_manager.add_particle('rain', pos=[random.uniform(self.game.offset.x - WIDTH * 0.1, WIDTH * 1.1 + self.game.offset.x), self.game.offset.y - 20])
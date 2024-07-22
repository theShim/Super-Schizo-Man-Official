import contextlib
from typing import Any
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import random
import math

from scripts.particles.fire import Fire_Particle

from scripts.utils.CORE_FUNCS import vec
from scripts.config.SETTINGS import Z_LAYERS, WIDTH, HEIGHT, ENVIRONMENT_SETTINGS

    ##############################################################################################

class Particle_Manager:
    def __init__(self, game, stage):
        self.game = game
        self.stage = stage

        self.particles = pygame.sprite.Group()

        self.start = True

    def sprites(self):
        return self.particles.sprites()

    def add_particle(self, particle_type, **kwargs):
        particle = {
            "fire" : Fire_Particle
        }[particle_type]

        particle(self.game, [self.game.all_sprites, self.particles], *kwargs.values())

    def update(self):
        if self.start: self.start = False
import contextlib
from typing import Any
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import random
import math

from scripts.particles.fire import Fire_Particle
from scripts.particles.floating_lights import Floating_Light
from scripts.particles.bord import Bord_After_Image, Bord_Particle
from scripts.particles.black_flame import Black_Fire
from scripts.particles.sparks import Spark
from scripts.particles.water_splash import Water_Splash, Water_Splosh
from scripts.particles.lightning import Lightning

from scripts.weather.rain import Rain_Particle

from scripts.utils.CORE_FUNCS import vec
from scripts.config.SETTINGS import WIDTH, HEIGHT

    ##############################################################################################

class Particle_Manager:
    def __init__(self, game, stage):
        self.game = game
        self.stage = stage

        self.particles = pygame.sprite.Group()

        self.start = True

    def sprites(self):
        return list(filter(lambda spr: pygame.Rect(0, 0, WIDTH, HEIGHT).collidepoint(vec(spr.pos) - self.game.offset), self.particles.sprites()))

    def add_particle(self, particle_type, **kwargs):
        particle = {
            "fire" : Fire_Particle,
            "float light" : Floating_Light,
            "bord after image" : Bord_After_Image,
            "bord particle" : Bord_Particle,
            "black flame" : Black_Fire,
            'rain' : Rain_Particle,
            "spark" : Spark,
            "lightning spinner" : Lightning.Spinner,
            "water splash" : Water_Splash,
            "water splosh" : Water_Splosh
        }[particle_type]

        particle(self.game, [self.game.all_sprites, self.particles], *kwargs.values())

    def update(self):
        if self.start: 
            for i in range(10):
                self.add_particle("float light", pos=vec(random.uniform(0, WIDTH), random.uniform(0, HEIGHT)))

            self.start = False
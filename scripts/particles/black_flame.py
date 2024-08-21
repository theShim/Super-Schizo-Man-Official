import contextlib
from typing import Any
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import random
import math

from scripts.utils.CORE_FUNCS import vec
from scripts.config.SETTINGS import Z_LAYERS

    ##############################################################################################

class Black_Fire(pygame.sprite.Sprite):
    def __init__(self, game, groups, pos):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen 
        self.z = Z_LAYERS["foreground particle"]

        self.children = pygame.sprite.Group()
        self.pos = vec(pos)
        self.col = pygame.Color(20, 18, 25)
        self.col2 = (67, 0, 98)
        self.base = self.col
        self.t = 0

    def update(self):
        self.t += math.radians(1)
        interp = (math.sin(self.t) ** 2)
        self.col = self.base.lerp(self.col2, interp)

        for i in range(5):
            Black_Particle(self.game, [self.children], self.pos, self.col, 20)

        self.draw()

    def draw(self):
        self.children.update(None)
        self.children.update(False)
        self.children.update(True)

class Black_Particle(pygame.sprite.Sprite):
    def __init__(self, game, groups, pos, col, radius = 20):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen

        self.pos = vec(pos)
        self.radius = radius
        self.decay = max(0.5, random.random())
        self.vel = vec(0, 0)
        self.col = col

    def update(self, draw_flag):
        if draw_flag != None:
            return self.draw(draw_flag)
        

        self.radius -= self.decay
        if self.radius <= 1:
            return self.kill()
        
        self.pos += self.vel
        self.vel = vec(random.uniform(-self.radius / 10, self.radius / 10) * 2, random.uniform(-self.radius / 10, self.radius / 10) * 2)#-random.uniform(3, 4))

    def draw(self, draw_flag):
        if draw_flag in ["bg", False]:
            pygame.draw.circle(self.screen, (255, 255, 255), self.pos - self.game.offset, self.radius)
        elif draw_flag in ["fg", True]:
            pygame.draw.circle(self.screen, self.col, self.pos - self.game.offset, self.radius * 0.9)
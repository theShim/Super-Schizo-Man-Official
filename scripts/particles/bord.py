import contextlib
from typing import Any
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import random
import math

from scripts.utils.CORE_FUNCS import vec
from scripts.config.SETTINGS import Z_LAYERS, WIDTH, HEIGHT

    ################################################################################################

class Bord_After_Image(pygame.sprite.Sprite):
    def __init__(self, game, groups, image, pos):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen
        self.z = Z_LAYERS["background particle"]

        self.image = image.copy()
        self.image.set_colorkey((1, 0, 0))
        self.pos = pos
        self.alpha = 255

    def update(self):
        self.alpha -= 30
        if self.alpha <= 0:
            return self.kill()
        
        self.draw()

    def draw(self):
        self.image.set_alpha(self.alpha)
        self.screen.blit(self.image, self.pos - self.game.offset)


class Bord_Particle(pygame.sprite.Sprite):
    def __init__(self, game, groups, pos, col=(255, 0, 0)):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen
        self.z = Z_LAYERS["background particle"]

        self.pos = vec(pos)
        self.angle = math.radians(random.uniform(0, 360))
        self.angle_mod = math.radians(random.uniform(2, 30))
        self.rot_direction = random.choice([-1, 1])
        self.radius = random.uniform(3, 3.2)
        self.decay = random.uniform(0.2, 0.8) / 4
        self.col = col

    def update(self):
        self.radius -= self.decay
        if self.radius <= 0:
            return self.kill()
        self.angle += self.angle_mod * self.rot_direction * (self.game.dt * 80)
        
        self.draw()

    def draw(self):
        surf = pygame.Surface((self.radius*3, self.radius*3), pygame.SRCALPHA)
        points = [
            vec(surf.get_size())/2 + vec(math.cos(self.angle), math.sin(self.angle)) * self.radius,
            vec(surf.get_size())/2 + vec(math.cos(self.angle + math.pi / 2), math.sin(self.angle + math.pi / 2)) * self.radius,
            vec(surf.get_size())/2 + vec(math.cos(self.angle + math.pi), math.sin(self.angle + math.pi)) * self.radius,
            vec(surf.get_size())/2 + vec(math.cos(self.angle + (3 * math.pi) / 2), math.sin(self.angle + (3 * math.pi) / 2)) * self.radius,
        ]
        pygame.draw.polygon(surf, self.col + (128,), points)
        self.screen.blit(surf, surf.get_rect(center=self.pos-self.game.offset))
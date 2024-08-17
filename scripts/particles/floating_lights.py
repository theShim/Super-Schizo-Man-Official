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

class Floating_Light(pygame.sprite.Sprite):
    def __init__(self, game, groups, pos):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen
        self.z = Z_LAYERS["foreground particle"]

        self.pos = vec(pos)
        self.angle = math.radians(random.uniform(0, 360))
        self.rot_direction = random.choice([-1, 1])
        self.radius = random.uniform(3, 3.2) / 2
        self.col = random.choice([(187, 173, 182), (199, 204, 225), (208, 212, 234)])
        self.vel = vec(random.uniform(4, 5), random.uniform(-4, 0)) / 4

        alpha_layers = 5
        self.light = pygame.Surface((self.radius * alpha_layers ** 2, self.radius * alpha_layers ** 2), pygame.SRCALPHA)
        for i in range(alpha_layers):
            pygame.draw.circle(self.light, (255, 255, 255, 64 * ((i) / alpha_layers)), vec(self.light.get_size())/2, self.radius**(alpha_layers - (i-0.1)))

    def update(self):
        self.vel.y -= random.uniform(-1, 1.25) / 10
        self.angle += (self.vel.magnitude() / 100) * self.rot_direction * (self.game.dt * 80)
        self.pos += (self.vel / 2) * (self.game.dt * 80)

        if self.pos.y < 0 or self.pos.x > WIDTH:
            self.pos.x = 0
            self.pos.y = random.uniform(HEIGHT/6, HEIGHT)
            self.vel = vec(random.uniform(4, 6), random.uniform(0, 0))


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
        self.screen.blit(surf, surf.get_rect(center=self.pos))
        self.screen.blit(self.light, self.light.get_rect(center=self.pos))

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

class Spark(pygame.sprite.Sprite):
    def __init__(self, game, groups, pos, scale, angle, speed=None, colour=(255, 255, 255), spin=False, grav=False):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen
        self.z = Z_LAYERS["background particle"]

        self.pos = vec(pos)
        self.scale = scale
        self.angle = angle
        self.speed = random.uniform(1, 3)
        self.colour = (255, 255, 255)

        self.spin = False
        self.grav = False

        for i in range(int(self.scale*2)+1):
            self.move()


    def move(self):
        self.pos += vec(math.cos(self.angle), math.sin(self.angle)) * self.speed

    def apply_gravity(self, friction, force, terminal_velocity):
        movement = vec(math.cos(self.angle), math.sin(self.angle)) * self.speed
        movement[1] = min(terminal_velocity, movement[1] + force)
        movement[0] *= friction
        self.angle = math.atan2(movement[1], movement[0])


    def update(self):
        self.speed -= 0.1
        if self.speed < 0:
            return self.kill()
        
        if self.spin:
            self.angle += 0.1
        if self.grav:
            self.apply_gravity(0.975, 0.2, 8)
        self.move()
        
        self.draw()

    def draw(self):
        points = [
            vec(math.cos(self.angle), math.sin(self.angle)) * self.scale * self.speed,
            vec(math.cos(self.angle - math.pi/2), math.sin(self.angle - math.pi/2)) * 0.3 * self.scale * self.speed,
            vec(math.cos(self.angle - math.pi), math.sin(self.angle - math.pi)) * 3 * self.scale * self.speed + vec(random.random(), random.random())*self.speed,
            vec(math.cos(self.angle + math.pi/2), math.sin(self.angle + math.pi/2))  * 0.3 * self.scale * self.speed,
        ]
        points = list(map(lambda x: x+self.pos-self.game.offset, points))
        pygame.draw.polygon(self.screen, self.colour, points)
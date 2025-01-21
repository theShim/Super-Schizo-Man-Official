import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import os
import numpy as np
import random
import math

from scripts.config.SETTINGS import WIDTH, HEIGHT, Z_LAYERS, FRIC, GRAV, CONTROLS, DEBUG, FPS
from scripts.utils.CORE_FUNCS import vec, lerp
from scripts.utils.sprite_animator import SpriteAnimator

    ##############################################################################################

class Chain(pygame.sprite.Sprite):
    def __init__(self, game, groups, anchor_pos, lengths=[30, 30], end_goal=None):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen

        self.anchor_pos = vec(anchor_pos)
        self.lengths = lengths
        self.points = [self.anchor_pos.copy()]

        i = 0
        for length in self.lengths:
            last_point = self.points[-1]
            self.points.append(last_point + (last_point.normalize().rotate(-i) * length))
            i += 20
        self.end_goal = end_goal or self.points[-1].copy()

        self.fabrik_stepper = self.fabrik()

    def fabrik(self):
        while True:
            previous_copy = self.end_goal
            new_points = [self.end_goal]

            for i in range(1, len(self.points)):
                try: unit = (self.points[-(i+1)] - previous_copy).normalize()
                except ValueError: unit = vec(0, 0)
                next_copy = previous_copy + unit * self.lengths[-i]
                new_points.append(next_copy)
                previous_copy = next_copy

            new_points.reverse()
            self.points = new_points
            yield


            #forward
            previous_copy = self.anchor_pos
            new_points = [self.anchor_pos]

            for i in range(1, len(self.points)):
                direction = (self.points[i] - previous_copy).normalize()
                next_copy = previous_copy + direction * self.lengths[i - 1]

                new_points.append(next_copy)
                previous_copy = next_copy

            self.points = new_points
            yield

    def update(self):
        next(self.fabrik_stepper)
        next(self.fabrik_stepper)

        self.draw()

    def draw(self):
        for i, p in enumerate(self.points):
            pygame.draw.line(self.screen, (200, 200, 200), p - self.game.offset, self.points[i+1] - self.game.offset, 2) if i+1 < len(self.points) else ...
            pygame.draw.circle(self.screen, (255, 255, 255), p - self.game.offset, 5, 2)
            pygame.draw.circle(self.screen, (30, 30, 30), p - self.game.offset, 3)
            
            if pygame.key.get_pressed()[pygame.K_k]:
                if i == len(self.points) - 1:
                    continue


                parts = 36
                for j in range(0, parts, 2):
                    t1 = math.radians(360 * (j / parts))
                    t2 = math.radians(360 * ((j+1) / parts))

                    pos1 = p + vec(math.cos(t1), math.sin(t1)) * self.lengths[i] - self.game.offset
                    pos2 = p + vec(math.cos(t2), math.sin(t2)) * self.lengths[i] - self.game.offset

                    pygame.draw.line(self.screen, (180, 180, 180), pos1, pos2)

        pygame.draw.circle(self.screen, (220, 30, 20), self.anchor_pos - self.game.offset, 5, 2)
        pygame.draw.circle(self.screen, (20, 30, 220), self.end_goal - self.game.offset, 5, 2)
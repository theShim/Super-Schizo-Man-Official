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

class Lightning:
    class Spinner(pygame.sprite.Sprite):
        def __init__(self, game, groups, points: list, speed=2, colours=[(230, 230, 230)], line_width=2):
            super().__init__(groups)
            self.game = game
            self.screen = self.game.screen
            self.z = Z_LAYERS["foreground particle"]

            self.segments = []
            self.points = points
            self.interp = 0
            self.speed = lambda: random.uniform(speed*0.8, speed*1.2)

            self.offset = 4
            self.generations = 3
            self.colours = colours
            self.line_width = line_width
            self.last_point = 0

        def gen_bolts(self, y_scroll):
            t = math.floor(self.interp) % len(self.points)
            if t != self.last_point:
                random.shuffle(self.points)
                self.last_point = t

            interp = (self.interp % len(self.points)) - t

            start = vec(self.points[t]).lerp(vec(self.points[t+1 if t < len(self.points)-1 else 0]), interp)
            start.y += y_scroll
            end = vec(self.points[t]).lerp(vec(self.points[t+1 if t < len(self.points)-1 else 0]), min(1, interp+self.speed()))
            end.y += y_scroll

            self.segments = []
            self.segments.append([start, end])
            offset = self.offset

            for gen in range(self.generations):
                for segment in list(self.segments):
                    self.segments.remove(segment)

                    midpoint = segment[0].lerp(segment[1], 0.5)
                    normal = (segment[1]-segment[0]).normalize()
                    offset_vec = vec(-normal.y, normal.x)
                    offset_vec *= random.uniform(-offset, offset)
                    midpoint += offset_vec

                    self.segments.append([segment[0], midpoint])
                    self.segments.append([midpoint, segment[1]])
                    
                offset //= 2

        def update(self):
            self.interp += math.radians(self.speed())
            self.gen_bolts(0)

            self.draw()

        def draw(self):
            i = 0
            for segment in self.segments:
                col = [max(0, c-i) for c in random.choice(self.colours)]
                pygame.draw.line(
                    self.screen, 
                    col, 
                    segment[0] - self.game.offset, 
                    segment[1] - self.game.offset, 
                    self.line_width
                )
                i += 0.5 if i < 128 else 0
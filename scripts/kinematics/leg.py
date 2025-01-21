import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import os
import numpy as np
import random
import math

from scripts.kinematics.chain import Chain

from scripts.config.SETTINGS import WIDTH, HEIGHT, Z_LAYERS, FRIC, GRAV, CONTROLS, DEBUG, FPS
from scripts.utils.CORE_FUNCS import vec, lerp
from scripts.utils.sprite_animator import SpriteAnimator

    ##############################################################################################

class Leg(Chain):
    def __init__(self, game, groups, anchor_pos, initial_end_goal = None, parent=None):
        super().__init__(game, groups, anchor_pos, lengths=[18, 24, 20], end_goal=vec(anchor_pos) + vec(0, 45))

        self.parent = parent

        self.end_goal = vec(initial_end_goal) or self.end_goal #actual position
        self.target_pos: vec = self.end_goal.copy() #possible/currently aiming at
        self.step_threshold = 85
        self.take_step = False
        self.still = False

    def walk(self):
        if self.take_step == False:
            if (self.end_goal.distance_to(self.target_pos)) > self.step_threshold:
                self.take_step = self.target_pos.copy()
        # if self.still:
        #     self.take_step = self.target_pos.copy()

        if self.take_step:
            self.end_goal = self.end_goal.lerp(self.take_step, (random.random() - .5) / 100 + (0.75 if not self.still else 0.25))
            if self.end_goal.distance_to(self.take_step) < 1:
                self.take_step = False

    def box_constraints(self): #prevents the leg colliding with the box/body
        min_dist = 10

        if self.target_pos.x > self.parent.rect.x - min_dist:
            self.target_pos.x = self.parent.rect.x - min_dist

        if self.target_pos.x < self.parent.rect.right + min_dist:
            self.target_pos.x = self.parent.rect.right + min_dist

        if self.target_pos.y < self.parent.rect.bottom:
            self.target_pos.y = self.parent.rect.bottom

    def is_on_ground(self):
        collision_tolerance = 10
        for rect in self.game.state_loader.tilemap.nearby_physics_rects(self.target_pos):
            # pygame.draw.rect(self.screen, (255, 0 ,0), [rect.x - self.game.offset.x, rect.y - self.game.offset.y, *rect.size], 1)
            if rect.collidepoint(self.target_pos):
                if abs(self.target_pos.y - rect.top) < collision_tolerance:
                    return rect.top
        return False

    def update(self):
        self.walk()

        self.box_constraints()
        super().update()

    def draw(self):
        super().draw()
        pygame.draw.line(self.screen, (20, 110, 110), self.end_goal - self.game.offset, self.target_pos - self.game.offset, 3)
        pygame.draw.circle(self.screen, (20, 220, 30), self.target_pos - self.game.offset, 3)
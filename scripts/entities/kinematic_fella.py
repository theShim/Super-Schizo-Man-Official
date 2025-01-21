import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import os
import numpy as np
import random
import math

from scripts.kinematics.leg import Leg

from scripts.config.SETTINGS import WIDTH, HEIGHT, Z_LAYERS, FRIC, GRAV, CONTROLS, DEBUG, FPS
from scripts.utils.CORE_FUNCS import vec, lerp
from scripts.utils.sprite_animator import SpriteAnimator

    ##############################################################################################

class RedBox(pygame.sprite.Sprite):
    def __init__(self, game, groups, pos=(4.5 * WIDTH, 200)):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen
        self.z = Z_LAYERS["entities"]

        self.size = (50, 30)
        self.rect = pygame.Rect(*pos, *self.size)

        self.vel = vec()
        self.acc = vec(0, GRAV)
        self.flag = False
        self.speed = 30
        self.on_ground = False

        self.legs = pygame.sprite.Group()
        self.left_leg = Leg(self.game, [self.legs], self.rect.bottomleft, initial_end_goal=[self.rect.left, 255], parent=self)
        self.right_leg = Leg(self.game, [self.legs], self.rect.bottomright, initial_end_goal=[self.rect.right, 255], parent=self)

    def key_inputs(self):
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_LEFT]:
            self.acc.x = -1
        elif keys[pygame.K_RIGHT]:
            self.acc.x = 1

        if self.flag == False:
            if keys[pygame.K_o]:
                self.flag = True
            return
        
    def apply_forces(self):
        self.vel += self.acc * self.speed * self.game.dt

        if self.on_ground:
            self.vel.y = 0

        self.vel.x *= FRIC
        if -0.5 < self.vel.x < 0.5:
            self.vel.x = 0

        self.rect.topleft += self.vel

    def apply_gravity(self):
        pass

    def move(self):
        self.acc = vec(0, 0 if self.on_ground else GRAV / 20)
        self.key_inputs()
        self.apply_forces()
    
    def leg_update(self):
        self.left_leg.anchor_pos = vec(self.rect.bottomleft)
        self.left_leg.target_pos = vec(self.rect.left, self.left_leg.end_goal.y)
        self.left_leg.still = not abs(self.acc.x + self.acc.y) > 0
        
        self.right_leg.anchor_pos = vec(self.rect.bottomright)
        self.right_leg.target_pos = vec(self.rect.right, self.right_leg.end_goal.y)
        self.right_leg.still = not abs(self.acc.x + self.acc.y) > 0

        self.legs.update()

    def collisions(self):
        self.on_ground = False
        collision_tolerance = 10
        for rect in self.game.state_loader.tilemap.nearby_physics_rects(self.rect.center):
            # pygame.draw.rect(self.screen, (255, 0 ,0), [rect.x - self.game.offset.x, rect.y - self.game.offset.y, *rect.size], 1)
            if self.rect.colliderect(rect):
                if abs(self.rect.bottom - rect.top) < collision_tolerance + 10 and self.vel.y > 0:
                    self.on_ground = True
                    self.rect.bottom = rect.top + 1
                    break

    def update(self):
        self.leg_update()

        for leg in self.legs.sprites():
            leg: Leg
            if (tile_y := leg.is_on_ground()):
                self.on_ground = True
                self.rect.y = tile_y - self.rect.height * 2
                self.vel.y = 0
                break
        else:
            self.on_ground = False

        self.move()
        self.collisions()

        self.draw()

    def draw(self):
        pygame.draw.rect(self.screen, (209, 0, 0), pygame.Rect(self.rect.x - self.game.offset.x, self.rect.y - self.game.offset.y, self.rect.width, self.rect.height))
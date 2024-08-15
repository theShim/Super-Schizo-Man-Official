import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import os
# import cv2
import numpy as np
import random
import math

from scripts.config.SETTINGS import WIDTH, HEIGHT, Z_LAYERS, FRIC, GRAV, CONTROLS, DEBUG, FPS
from scripts.utils.CORE_FUNCS import vec, lerp, add_loaded_sprite_number, Timer
from scripts.utils.sprite_animator import SpriteAnimator

    ##############################################################################################

class FireFly_Cluster(pygame.sprite.Sprite):
    def __init__(self, game, groups, pos, cluster_number = 5):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen
        self.z = Z_LAYERS["entities"]

        self.pos = vec(pos)
        self.fly_radius_lim = 36
        self.flies = pygame.sprite.Group()
        [FireFly(self.game, [self.flies], self.pos, self.fly_radius_lim) for i in range(cluster_number)]

    def update(self):
        screen_pos = self.pos - self.game.offset
        if 0 <= screen_pos.x <= WIDTH:
            if 0 <= screen_pos.y <= HEIGHT:
                self.flies.update()

        # if DEBUG:
        #     pygame.draw.circle(self.screen, (255, 0, 0), screen_pos, 3)
        #     pygame.draw.circle(self.screen, (105, 105, 105), screen_pos, self.fly_radius_lim, 1)

class FireFly(pygame.sprite.Sprite):
    def __init__(self, game, groups, pos, fly_lim):
        super().__init__(groups)
        self.game = game
        self.screen: pygame.Surface = self.game.screen

        self.pixel_size = 2
        self.fly_lim = fly_lim

        self.anchor_pos = vec(pos)
        self.head_pos = self.anchor_pos + vec(random.randint(-3, 3), random.randint(-3, 3))
        self.tail_pos = self.head_pos + vec(random.randint(-1, 1), random.randint(-1, 1)) * self.pixel_size
        
        self.speed = random.randint(1, 1)
        self.direction = math.radians(random.randint(0, 360))
        self.direction_target = math.radians(random.randint(0, 360))

        self.move_timer = Timer(3, 1)
        self.flasher = {"timer" : Timer(random.randint(4, 8) * 4, 1), "switch" : False}

    def move(self):
        self.direction = lerp(self.direction, self.direction_target, 0.5)
        if abs(self.direction_target - self.direction) < 0.01:
            self.direction_target = math.radians(random.randint(0, 360))

        self.vel = vec(math.cos(self.direction), math.sin(self.direction)) * self.speed * self.pixel_size

        self.head_pos += self.vel
        # self.tail_pos += self.vel
        self.tail_pos = self.head_pos + vec(random.randint(-1, 1), random.randint(-1, 1)) * self.pixel_size

        delta = self.anchor_pos - self.head_pos
        if delta.magnitude() > self.fly_lim:
            self.direction_target = math.atan2(delta.y, delta.x)

    def update(self):
        self.move_timer.update()
        if self.move_timer.finished:
            self.move()
            self.move_timer.reset()

        self.flasher["timer"].update()
        if self.flasher["timer"].finished:
            self.flasher["timer"].reset()
            self.flasher["timer"].change_duration(random.randint(4, 12) * 4)
            self.flasher["switch"] = not self.flasher["switch"]

        self.draw()

    def draw(self):
        pygame.draw.rect(self.screen, (236, 223, 214), [self.head_pos.x - self.game.offset.x, self.head_pos.y - self.game.offset.y, self.pixel_size, self.pixel_size])

        if self.flasher["switch"]:
            pygame.draw.rect(self.screen, (236, 223, 214), [self.tail_pos.x - self.game.offset.x, self.tail_pos.y - self.game.offset.y, self.pixel_size, self.pixel_size])
            self.game.state_loader.current_state.light_manager.add_glow((self.head_pos + self.tail_pos) / 2, self.pixel_size * 15, (229, 215, 69))
        else:
            pygame.draw.rect(self.screen, (53, 46, 41), [self.tail_pos.x - self.game.offset.x, self.tail_pos.y - self.game.offset.y, self.pixel_size, self.pixel_size])
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
    def __init__(self, game, groups, pos, vel, col=(255, 0, 0)):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen
        self.z = Z_LAYERS["background particle"]

        self.pos = vec(pos) - vel
        self.tail = self.pos - vel * (random.randint(10, 15) / 20)
        self.t = 0
        self.decay = random.uniform(0.0125, 0.015) / 5
        self.vel: vec = vel / 2
        self.col = col
        self.rot_direction = random.choice([-1, 1]) * 4
        self.alpha = 255

    def update(self):
        if self.pos.y - self.game.offset.y < -50:
            return self.kill()
        
        self.t += self.decay
        if self.t >= 0.5:
            return self.kill()
        
        self.alpha -= random.randint(1, 3)
        if self.alpha <= 0:
            return self.kill()
        
        self.pos += self.vel
        self.vel.rotate_ip(self.t * self.rot_direction * self.vel.magnitude())
        self.tail = self.tail.lerp(self.pos, min(1, self.t))
        self.draw()

    def draw(self):
        pygame.draw.line(self.screen, self.col, self.pos - self.game.offset, self.tail - self.game.offset, 2)

    def draw(self):
        # Calculate the bounding box for the line
        min_x = min(self.pos[0], self.tail[0])
        min_y = min(self.pos[1], self.tail[1])
        max_x = max(self.pos[0], self.tail[0])
        max_y = max(self.pos[1], self.tail[1])
        
        width = max_x - min_x
        height = max_y - min_y
        
        # Create a smaller surface to fit the line
        temp_surface = pygame.Surface((width + 1, height + 1), pygame.SRCALPHA)
        
        # Adjusted start and end positions relative to the temp_surface
        start_pos = (self.pos[0] - min_x, self.pos[1] - min_y)
        end_pos = (self.tail[0] - min_x, self.tail[1] - min_y)
        
        # Draw the line on the smaller surface
        line_color = self.col + (self.alpha,)
        pygame.draw.line(temp_surface, line_color, start_pos, end_pos, 2)
        
        # Blit the smaller surface onto the main screen
        self.screen.blit(temp_surface, (min_x - self.game.offset[0], min_y - self.game.offset[1]))
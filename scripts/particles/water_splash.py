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

class Water_Splash(pygame.sprite.Sprite):
    def __init__(self, game, groups, pos, angle, col=None):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen
        self.z = Z_LAYERS["foreground particle"]

        self.pos = vec(pos)
        self.angle = angle
        self.rotation = random.uniform(0, 90)
        
        self.col = col or (255, 255, 255)
        col_offset = random.randint(-30, 30)
        self.col = [sorted([0, 255, self.col[i] + col_offset])[1] for i in range(len(self.col))]

        self.radius = random.uniform(2, 3.2)
        self.speed = random.uniform(1, 2.2)
        self.decay = random.uniform(0.05, 0.2)


    def move(self):
        self.pos += vec(math.cos(self.angle), math.sin(self.angle)) * self.speed

    def apply_gravity(self, friction, force, terminal_velocity):
        movement = vec(math.cos(self.angle), math.sin(self.angle)) * self.speed
        movement[1] = min(terminal_velocity, movement[1] + force)
        movement[0] *= friction
        self.angle = math.atan2(movement[1], movement[0])

        
    def update(self):
        self.apply_gravity(0.975, 0.2, 8)
        self.move()

        self.rotation += self.angle % (2*math.pi)
        self.radius -= self.decay

        if self.radius <= 0:
            return self.kill()

        self.draw()

    def draw(self):
        surf = pygame.Surface((self.radius*3, self.radius*3), pygame.SRCALPHA)
        points = [
            vec(surf.get_size())/2 + vec(math.cos(self.rotation), math.sin(self.rotation)) * self.radius,
            vec(surf.get_size())/2 + vec(math.cos(self.rotation + math.pi / 2), math.sin(self.rotation + math.pi / 2)) * self.radius,
            vec(surf.get_size())/2 + vec(math.cos(self.rotation + math.pi), math.sin(self.rotation + math.pi)) * self.radius,
            vec(surf.get_size())/2 + vec(math.cos(self.rotation + (3 * math.pi) / 2), math.sin(self.rotation + (3 * math.pi) / 2)) * self.radius,
        ]
        pygame.draw.polygon(surf, self.col, points)
        self.screen.blit(surf, surf.get_rect(center=self.pos - self.game.offset))

        self.game.state_loader.current_state.light_manager.add_glow(self.pos, self.radius * 3, self.col)





class Water_Splosh(pygame.sprite.Sprite):
    def __init__(self, game, groups, pos, vel, col=(255, 0, 0)):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen
        self.z = Z_LAYERS["foreground particle"]

        self.pos = vec(pos) + vel * (random.randint(10, 15) / 2) / 2
        self.tail = self.pos
        self.t = 0
        self.decay = random.uniform(0.0125, 0.015) * 1.2
        self.vel: vec = vel / 2
        self.col = col
        self.rot_direction = (self.vel.x / abs(self.vel.x)) * 10
        self.alpha = 255
        self.glow_col = [min(255, i+30) for i in self.col]

    def update(self):
        if self.pos.y - self.game.offset.y < -50:
            return self.kill()
        
        self.t += self.decay
        if self.t >= 0.5:
            return self.kill()
        
        self.alpha = (1 - self.t) * 255
        
        self.pos += self.vel
        self.vel.rotate_ip(self.t * self.rot_direction * self.vel.magnitude())
        self.vel.y += 0.05
        self.tail = self.tail.lerp(self.pos, min(1, self.t))
        self.draw()

    def draw(self):
        pygame.draw.line(self.screen, self.col, self.pos - self.game.offset, self.tail - self.game.offset, 2)

    def draw(self):
        min_x = min(self.pos[0], self.tail[0])
        min_y = min(self.pos[1], self.tail[1])
        max_x = max(self.pos[0], self.tail[0])
        max_y = max(self.pos[1], self.tail[1])
        
        width = max_x - min_x
        height = max_y - min_y
        
        temp_surface = pygame.Surface((width + 1, height + 1), pygame.SRCALPHA)
        
        start_pos = (self.pos[0] - min_x, self.pos[1] - min_y)
        end_pos = (self.tail[0] - min_x, self.tail[1] - min_y)
        pygame.draw.line(temp_surface, self.col, start_pos, end_pos, 2)
        
        self.screen.blit(temp_surface, (min_x - self.game.offset[0], min_y - self.game.offset[1]))

        self.game.state_loader.current_state.light_manager.add_glow(self.pos, (self.pos - self.tail).magnitude() * 3, self.glow_col)
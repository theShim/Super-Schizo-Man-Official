import contextlib
from typing import Any
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import random
import math

from scripts.utils.CORE_FUNCS import vec
from scripts.config.SETTINGS import Z_LAYERS

    ################################################################################################

class Fire_Particle(pygame.sprite.Sprite):

    alpha_layer_qty = 2
    alpha_glow_constant = 2
    switch = True

    def __init__(self, game, groups, pos, radius, master_pos=None):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen
        self.z = Z_LAYERS["foreground particle"]

        self.pos = vec(pos)
        self.oPos = self.pos.copy()
        self.master_pos = master_pos or self.pos.copy()

        self.alpha_layers = Fire_Particle.alpha_layer_qty
        self.alpha_glow = Fire_Particle.alpha_glow_constant
        self.burn_rate = 0.01 * random.uniform(1, 4)

        self.radius = radius
        self.yellow = 0
        self.max_size = 2 * self.radius * self.alpha_glow * self.alpha_layers ** 2

    def burn(self):
        self.radius -= self.burn_rate * (self.game.dt * 100)
        if self.radius < 0:
            self.kill()

            Fire_Particle(
                self.game, 
                [self.game.all_sprites], 
                (self.master_pos + vec(random.uniform(-1, 1), random.uniform(-1, 1))), 
                random.uniform(1, 3), 
                self.master_pos
            )

            return True
        
        self.pos.x += (self.game.dt * 100) * random.uniform(-self.radius, self.radius) / 2
        self.pos.y -= (self.game.dt * 100) * (random.uniform(5, 8) - self.radius) / 16

        self.yellow += 2
        if self.yellow > 255:
            self.yellow = 255

    def update(self):
        dead = self.burn()
        if dead: return
         
        self.draw()

    def draw(self):
        # pygame.draw.circle(self.screen, (255, self.yellow, 0), self.pos - self.game.offset, self.radius * 2)
        
        # for i in range(self.alpha_layers):
        #     surf = pygame.Surface((self.max_size, self.max_size), pygame.SRCALPHA)
        #     pygame.draw.circle(surf, (255 / (i + 3), self.yellow / (i + 3), 0), vec(surf.get_size())/2, self.radius * (i + 3))
        #     self.screen.blit(surf, surf.get_rect(center=self.pos-self.game.offset), special_flags=pygame.BLEND_RGB_ADD)

        surf = pygame.Surface((self.max_size, self.max_size), pygame.SRCALPHA)

        for i in range(self.alpha_layers, -1, -1):
            alpha = 255 - i * (255 // self.alpha_layers - 5)
            if alpha < 0: alpha = 0

            radius = self.radius * self.alpha_glow * i**2
            pygame.draw.circle(surf, (255, self.yellow, 0, alpha), list(map(lambda x: x/2, surf.get_size())), radius)
            
        self.screen.blit(surf, surf.get_rect(center=self.pos-self.game.offset))

        self.game.state_loader.current_state.light_manager.add_glow(self.pos, 1 * self.radius * self.alpha_glow * (self.alpha_layers)**2, (255, self.yellow, 0))
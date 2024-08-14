import contextlib
from typing import Any
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import random
import math

from scripts.utils.CORE_FUNCS import vec
from scripts.config.SETTINGS import Z_LAYERS, SIZE

    ################################################################################################

class Light_Manager:
    def __init__(self, game):
        self.game = game
        self.screen = self.game.screen
        self.z = Z_LAYERS["light and shadow"]

        self.light_layer = pygame.Surface(SIZE, pygame.SRCALPHA)
        self.light_layer.set_colorkey((0, 0, 0))
        self.shadow_layer = pygame.Surface(SIZE, pygame.SRCALPHA)
        self.shadow_layer.set_colorkey((0, 0, 0))

        glow_surf = pygame.Surface((glow_size := 512, glow_size), flags = pygame.SRCALPHA)
        for i in range(glow_size // 2):
            circle_surf = pygame.Surface((glow_size, glow_size), flags = pygame.SRCALPHA)
            pygame.draw.circle(circle_surf, (1, 1, 1, 1), (s := glow_size / 2, s), i)
            glow_surf.blit(circle_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        self.glow_cache = {"base" : glow_surf}
        self.shadow_cache = {}
        
        
    def reset(self):
        self.light_layer.fill((150, 150, 150))

        ###################################################################################

    def add_glow(self, pos, size, colour):
        size = vec(s := int(size), s)
        
        cache_string = f"{size};{colour}"
        if not (glow_surf := self.glow_cache.get(cache_string)):
            glow_surf = pygame.transform.scale(self.glow_cache['base'], size)
            glow_surf.fill(colour, special_flags = pygame.BLEND_RGBA_MULT)
            self.glow_cache[cache_string] = glow_surf
        
        self.light_layer.blit(glow_surf, pos - self.game.offset - size / 2, special_flags = pygame.BLEND_RGBA_ADD)

    # def add_shadow(self, pos, size, intensity):
    #     #intensity = alpha (0 <= x <= 255)
    #     size = vec(s := int(size), s)
        
    #     cache_string = f"{size};{intensity}"
    #     if not (shadow_surf := self.shadow_cache.get(cache_string)):
    #         shadow_surf = pygame.transform.scale(self.glow_cache['base'], size)
    #         shadow_surf.fill((0, 0, 0, intensity), special_flags=pygame.BLEND_RGBA_MULT)
    #         self.shadow_cache[cache_string] = shadow_surf

    #     self.shadow_layer.blit(shadow_surf, pos - self.game.offset - size / 2, special_flags=pygame.BLEND_RGBA_MULT)

        ###################################################################################

    def add_tile_highlight(self, normal, pos):
        self.light_layer.blit(normal, pos - self.game.offset, special_flags=pygame.BLEND_RGBA_ADD)

        ###################################################################################

    def update(self):
        self.draw()
        self.reset()

    def draw(self):
        self.screen.blit(self.light_layer, (0, 0), special_flags = pygame.BLEND_RGBA_MULT)
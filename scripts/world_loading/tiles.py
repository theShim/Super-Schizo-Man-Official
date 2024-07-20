import contextlib
with contextlib.redirect_stdout(None):
    import pygame; pygame.init()
    from pygame.locals import *
    
import os
import json
import random

from scripts.config.SETTINGS import TILE_SIZE, WIDTH, HEIGHT, Z_LAYERS
from scripts.utils.CORE_FUNCS import add_loaded_sprite_number
from scripts.utils.spritesheets import Spritesheet

    ##############################################################################################

class Tile(pygame.sprite.Sprite):

    AUTO_TILE_TYPES = {'grass', 'stone'}
    AUTO_TILE_MAP = {
        "grass" : {
            tuple(sorted([(1, 0), (0, 1)])): 0,                                #top-left
            tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,                       #top
            tuple(sorted([(-1, 0), (0, 1)])): 2,                               #top-right
            tuple(sorted([(1, 0), (0, -1), (0, 1)])): 3,                       #left
            tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): {"choices" : [4, 9, 10, 11], "weights" : [100, 1, 1, 1]}, #middle
            tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 5,                      #right
            tuple(sorted([(1, 0), (0, -1)])): 6,                               #bottom-left
            tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 7,                      #bottom
            tuple(sorted([(-1, 0), (0, -1)])): 8,                              #bottom-right
            # tuple(sorted([(0, -1)])): 9,                                     #lonesome top
        }
    }

    DARK = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    DARK.fill((0, 0, 0))

    @classmethod
    def cache_sprites(cls):
        cls.SPRITES = {}
        path = "assets/tiles"

        for name in os.listdir(path):
            if not name.endswith(".png"):
                imgs = Spritesheet.tile_handler(name)
                add_loaded_sprite_number(len(imgs))
                cls.SPRITES[name.lower()] = imgs

    def __init__(self, game, type_, variant, pos):
        super().__init__()
        self.game = game
        self.screen = self.game.screen

        self.type = type_ #tile type e.g. grass, the folder
        self.variant = variant #tile variant e.g. grass_8, the asset itself
        self.pos = pos
        self.z = Z_LAYERS["tiles"]

    #dictionary object used for json saving
    @property
    def dict(self) -> dict:
        return {"type":self.type, "variant":self.variant, "pos":self.pos}
    
    #actually draw it onto the screen
    def update(self, transparent=False, dim=0):
        img: pygame.Surface = Tile.SPRITES[self.type][self.variant].copy()

        if transparent:
            img.set_alpha(128)

        if dim != 0:
            dark = self.DARK.copy()
            dark.set_alpha(255 * (dim / 100))
            img.blit(dark, (0, 0))

        self.screen.blit(img, [
            (self.pos[0] * TILE_SIZE) - self.game.offset.x, 
            (self.pos[1] * TILE_SIZE) - self.game.offset.y
        ])

    ##############################################################################################

class Offgrid_Tile(pygame.sprite.Sprite):

    @classmethod
    def cache_sprites(cls):
        cls.SPRITES = {}
        path = "assets/offgrid_tiles"

        for name in os.listdir(path):
            imgs = []
            for spr in os.listdir(f"{path}/{name}"):
                img = pygame.image.load(f"{path}/{name}/{spr}").convert_alpha()
                img.set_colorkey((0, 0, 0))
                imgs.append(img)
            cls.SPRITES[name] = imgs

    def __init__(self, game, type_, variant, pos):
        super().__init__()
        self.game = game
        self.screen = self.game.screen

        self.type = type_
        self.variant = variant
        self.pos = pos
        self.z = Z_LAYERS["background offgrid"]

    @property
    def dict(self):
        return {'type':self.type, "pos":self.pos, "variant":self.variant}
    
    def update(self):
        img = Offgrid_Tile.SPRITES[self.type][self.variant]
        self.screen.blit(img, self.pos - self.game.offset)
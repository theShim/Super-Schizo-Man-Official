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
    def update(self, dim=False):
        img: pygame.Surface = Tile.SPRITES[self.type][self.variant].copy()
        if dim: img.set_alpha(128)

        self.screen.blit(img, [
            (self.pos[0] * TILE_SIZE) - self.game.offset.x, 
            (self.pos[1] * TILE_SIZE) - self.game.offset.y
        ])
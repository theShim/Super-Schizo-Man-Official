import contextlib
with contextlib.redirect_stdout(None):
    import pygame; pygame.init()
    from pygame.locals import *
    
import math

from scripts.nature.nature_tiles.grass import Grass_Manager

from scripts.config.SETTINGS import TILE_SIZE, Z_LAYERS, SIZE
from scripts.utils.CORE_FUNCS import euclidean_distance

    ##############################################################################################

class Nature_Manager:
    def __init__(self, game):
        self.game = game
        
        self.grass_manager = Grass_Manager(self.game)

    def add_tile(self, type_, pos, variant):
        if type_ == "grass":
            loc = f"{int(pos[0]//TILE_SIZE)};{int(pos[1]//TILE_SIZE)}"
            self.grass_manager.add_tile(loc, pos, variant)

    def update(self):
        self.grass_manager.t += 5
        self.grass_manager.player_force()

    def render(self):
        all_tiles = []
        
        grass_tiles = [t for t in self.grass_manager.tiles_to_render()]
        all_tiles += grass_tiles

        return all_tiles
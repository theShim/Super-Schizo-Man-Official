import contextlib
with contextlib.redirect_stdout(None):
    import pygame; pygame.init()
    from pygame.locals import *
    
import math

from scripts.nature.nature_tiles.grass import Grass_Manager
from scripts.nature.nature_tiles.water import Water, Water_Handler

from scripts.config.SETTINGS import TILE_SIZE, Z_LAYERS, SIZE
from scripts.utils.CORE_FUNCS import euclidean_distance

    ##############################################################################################

class Nature_Manager:
    def __init__(self, game):
        self.game = game
        
        self.grass_manager = Grass_Manager(self.game)
        self.water_tiles = {}

    def add_tile(self, type_, pos, variant):
        if type_ == "grass":
            loc = f"{int(pos[0]//TILE_SIZE)};{int(pos[1]//TILE_SIZE)}"
            self.grass_manager.add_tile(loc, pos, variant)

        elif type_ == "water":
            self.water_tiles[tuple(pos)] = variant

    def clump_water(self):
        groups = Water_Handler.segment_water(self.water_tiles)
        self.water_tiles = []
        for g in groups:
            positions = list(map(lambda t:t[0], g))
            xs, ys = list(zip(*positions))

            x = min(xs)
            y = min(ys)
            width = max(xs) - min(xs) + 1
            height = max(ys) - min(ys) + 1
            variant = g[0][1]
            self.water_tiles.append(Water(self.game, [x, y], [width, height], variant))

    def update(self):
        self.grass_manager.t += 5
        self.grass_manager.player_force()

    def render(self):
        all_tiles = []
        
        grass_tiles = [t for t in self.grass_manager.tiles_to_render()]
        all_tiles += grass_tiles
        
        # all_tiles += self.water_tiles
        for tile in self.water_tiles:
            if pygame.FRect(tile.pos.x - self.game.offset.x, tile.pos.y - self.game.offset.y, tile.size.x, tile.size.y).colliderect([0, 0, *SIZE]):
                tile.player_collision(self.game.player)
                all_tiles.append(tile)

        return all_tiles
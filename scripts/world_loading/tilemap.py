import contextlib
with contextlib.redirect_stdout(None):
    import pygame; pygame.init()
    from pygame.locals import * 
    
import os
import json
import random
from tkinter.filedialog import asksaveasfile, askopenfilename

from scripts.world_loading.tiles import Tile

from scripts.config.SETTINGS import TILE_SIZE, WIDTH, HEIGHT, Z_LAYERS

    ##############################################################################################

class Tilemap:
    def __init__(self, game, tile_size=TILE_SIZE, editor_flag=False):
        self.game = game

        self.tile_size = tile_size
        self.tilemap = {} #includes layers e.g. {0 : {}, 1 : {}}
        self.offgrid_tiles = []

        self.editor_flag = editor_flag

    #remember to "cull" tiles in layers behind a tile infront to reduce tiles being rendered

    def add_tile(self, layer: int, type: str, variant: str, tile_loc: str, pos: list[int, int]):
        #adding a new layer dict if it doesnt exist. this will need to be culled later to avoid 
        #tiles "behind" other tiles being blitted unnecessarily, and also cull empty dicts for file storage
        if layer not in self.tilemap.keys():
            self.tilemap[layer] = {}

        self.tilemap[layer][tile_loc] = Tile(self.game, type, variant, pos)

        ##################################################################################

    def auto_tile(self):
        for layer in self.tilemap:
            for loc in self.tilemap[layer]:
                tile = self.tilemap[layer][loc]
                neighbours = set()
                for shift in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    check_loc = str(tile.pos[0] + shift[0]) + ';' + str(tile.pos[1] + shift[1])
                    if check_loc in self.tilemap[layer]:
                        if self.tilemap[layer][check_loc].type == tile.type:
                            neighbours.add(shift)

                neighbours = tuple(sorted(neighbours))
                for tile_type in Tile.AUTO_TILE_TYPES:
                    if tile.type.startswith(tile_type):
                        if neighbours in Tile.AUTO_TILE_MAP[tile_type]:
                            variant = Tile.AUTO_TILE_MAP[tile_type][neighbours]
                            
                            if type(variant) != dict:
                                tile.variant = Tile.AUTO_TILE_MAP[tile_type][neighbours]
                            else:
                                tile.variant = random.choices(variant["choices"], variant["weights"], k=1)[0]
                        break
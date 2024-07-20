import contextlib
with contextlib.redirect_stdout(None):
    import pygame; pygame.init()
    from pygame.locals import * 
    
import os
import json
import random
from tkinter.filedialog import asksaveasfile, askopenfilename

from scripts.world_loading.tiles import Tile, Offgrid_Tile

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

    def add_tile(self, layer: int, type: str, variant: int, tile_loc: str, pos: list[int, int]):
        #adding a new layer dict if it doesnt exist. this will need to be culled later to avoid 
        #tiles "behind" other tiles being blitted unnecessarily, and also cull empty dicts for file storage
        if layer not in self.tilemap.keys():
            self.tilemap[layer] = {}

        self.tilemap[layer][tile_loc] = Tile(self.game, type, variant, pos)

    def add_offgrid_tile(self, type: str, variant: int, pos: list[int, int]):
        self.offgrid_tiles.append(Offgrid_Tile(self.game, type, variant, pos))

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

    def save(self):
        f = asksaveasfile(
            filetypes=[('JSON File', ".json")], 
            defaultextension=".json",
            initialdir="level_data"
        )
        if f:
            tilemap = {}
            for layer in self.tilemap:
                tilemap[layer] = {key:item.dict for key,item in self.tilemap[layer].items()}

            offgrid = []
            for tile in self.offgrid_tiles:
                offgrid.append(tile.dict)

            json.dump(
                {
                    'tilemap' : tilemap,
                    'offgrid' : offgrid,
                    'tile_size' : self.tile_size
                }, 
                f,
                indent=4
            )
            print("Saved to", f.name)

    def load(self, path: str=None):
        if path == None:
            f = askopenfilename(
                title="Open existing level data...",
                initialdir="level_data",
                filetypes=[('JSON File', ".json")]
            )
        else:
            f = path

        try:
            with open(f, 'r') as file:
                data = json.load(file)
        except FileNotFoundError as err:
            raise FileNotFoundError(err)
        except:
            return
        
        self.tilemap = {}
        for layer in data["tilemap"]:
            self.tilemap[int(layer)] = {}

            for dic in data["tilemap"][layer]:
                tile_data = data["tilemap"][layer][dic]

                pos = tile_data["pos"]
                self.add_tile(
                    int(layer), 
                    tile_data["type"], 
                    tile_data["variant"], 
                    f"{int(pos[0])};{int(pos[1])}", 
                    tile_data["pos"]
                )

                if self.editor_flag:
                    if int(layer) not in self.game.layers:
                        self.game.layers[int(layer)] = {}
                    self.game.layers[int(layer)][f"{int(pos[0])};{int(pos[1])}"] = {
                        "type" : tile_data["type"],
                        "variant" : tile_data["variant"],
                        "pos" : tile_data["pos"]
                    }

        for dic in data["offgrid"]:
            self.add_offgrid_tile(
                dic["type"],
                dic["variant"],
                dic["pos"]
            )
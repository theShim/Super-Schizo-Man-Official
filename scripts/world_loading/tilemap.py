import contextlib
with contextlib.redirect_stdout(None):
    import pygame; pygame.init()
    from pygame.locals import * 
    
import math
import json
import random
from tkinter.filedialog import asksaveasfile, askopenfilename

from scripts.nature.manager import Nature_Manager
from scripts.world_loading.tiles import Tile, Offgrid_Tile

from scripts.config.SETTINGS import TILE_SIZE, WIDTH, HEIGHT, Z_LAYERS
from scripts.utils.CORE_FUNCS import vec, crop

    ##############################################################################################

NEIGHBOUR_OFFSETS = [
    (-1, -1),
    (-1, 0),
    (0, -1),
    (1, -1),
    (1, 0),
    (0, 0),
    (-1, 1),
    (0, 1),
    (1, 1)
]

NATURE_TILES = {"grass", "water"}

    ##############################################################################################

class Tilemap:
    def __init__(self, game, tile_size=TILE_SIZE, editor_flag=False):
        self.game = game

        self.tile_size = tile_size
        self.tilemap = {} #includes layers e.g. {0 : {}, 1 : {}}
        self.offgrid_tiles = []

        self.back_map = None
        self.front_map = None
        self.light_map = None
        self.map = None
        self.lowest_x, self.lowest_y = 0, 0

        self.nature_manager = Nature_Manager(self.game)

        self.editor_flag = editor_flag

    #remember to "cull" tiles in layers behind a tile infront to reduce tiles being rendered

    def add_tile(self, layer: int, type: str, variant: int, tile_loc: str, pos: list[int, int], no_neighbours: list[bool, bool, bool, bool] = [False, False, False, False]):
        #adding a new layer dict if it doesnt exist. this will need to be culled later to avoid 
        #tiles "behind" other tiles being blitted unnecessarily, and also cull empty dicts for file storage
        if layer not in self.tilemap.keys():
            self.tilemap[layer] = {}

        normals_dict = {
            #[left, right, top, down]
            tuple([True, False, True, False]) : 0,
            tuple([False, False, True, False]) : 1,
            tuple([False, True, True, False]) : 2,
            tuple([True, False, False, False]) : 3,
            tuple([False, False, False, False]) : 4,
            tuple([False, True, False, False]) : 5,
            tuple([True, False, False, True]) : 6,
            tuple([False, False, False, True]) : 7,
            tuple([False, True, False, True]) : 8
        }
        normal = normals_dict.get(tuple(no_neighbours), normals_dict[tuple([False, False, False, False])])

        self.tilemap[layer][tile_loc] = Tile(self.game, type, variant, pos, normal=normal if not self.editor_flag else None)

    def add_offgrid_tile(self, type: str, variant: int, pos: list[int, int], *kwargs):
        if self.editor_flag:
            return self.offgrid_tiles.append(Offgrid_Tile(self.game, type, variant, pos, kwargs))
        
        if type in NATURE_TILES:
            self.nature_manager.add_tile(type, pos, variant)
        else:
            return self.offgrid_tiles.append(Offgrid_Tile.create_offgrid_tile(self.game, type, variant, pos, kwargs))

    def generate_map(self, size: list[int, int], lowest_buffer: list[int, int]):
        map_width = size[0] * TILE_SIZE
        map_height = size[1] * TILE_SIZE
        self.lowest_x, self.lowest_y = lowest_buffer
        self.map = pygame.Surface((map_width, map_height), pygame.SRCALPHA)
        self.back_map = pygame.Surface((map_width, map_height), pygame.SRCALPHA)
        self.front_map = pygame.Surface((map_width, map_height), pygame.SRCALPHA)

        for layer in list(sorted(self.tilemap.keys(), reverse=True)):
            for tile_loc in self.tilemap[layer]:
                tile = self.tilemap[layer][tile_loc]
                tile_pos = vec(tile.pos)

                tile_pos.x -= self.lowest_x
                tile_pos.y -= self.lowest_y

                image: pygame.Surface = Tile.SPRITES[tile.type][tile.variant].copy()

                if (dim := layer * 20) != 0:
                    dark = pygame.mask.from_surface(image).to_surface(setcolor=(0, 0, 0, 255), unsetcolor=(255, 255, 255))
                    dark.set_colorkey((255, 255, 255))
                    dark.set_alpha(255 * (dim / 100))
                    image.blit(dark, (0, 0))

                # if tile.normal != None and layer == 0:
                #     image.blit(Tile.NORMAL_LIGHT_MAPS[tile.normal], [0, 0], special_flags=pygame.BLEND_RGBA_MULT)

                self.map.blit(image, tile_pos * TILE_SIZE)

                if layer == 0:
                    self.front_map.blit(image, tile_pos * TILE_SIZE)
                else:
                    self.back_map.blit(image, tile_pos * TILE_SIZE)

        self.back_map = Map_Container(self.game, self.back_map, self.lowest_x, self.lowest_y, Z_LAYERS["background tiles"])
        self.light_map = Map_Container(self.game, self.front_map.copy(), self.lowest_x, self.lowest_y, Z_LAYERS["light and shadow"])
        self.front_map = Map_Container(self.game, self.front_map, self.lowest_x, self.lowest_y, Z_LAYERS["foreground tiles"])

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
        
        if not self.editor_flag: 
            tile_x = set()
            tile_y = set()
            lowest_x = math.inf
            lowest_y = math.inf
        
        self.tilemap = {}
        for layer in data["tilemap"]:
            self.tilemap[int(layer)] = {}

            for dic in data["tilemap"][layer]:
                tile_data = data["tilemap"][layer][dic]
                pos = tile_data["pos"]
                
                if data['tilemap'][layer][dic]['type'] == "water" and self.editor_flag == False:
                    self.nature_manager.add_tile("water", data['tilemap'][layer][dic]['pos'], data['tilemap'][layer][dic]['variant'])

                else:
                    #for the "normal maps" (improve them later)
                    no_neighbours = [f"{int(pos[0] + offset[0])};{int(pos[1] + offset[1])}" not in data["tilemap"][layer]
                                for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]]
                    
                    self.add_tile(
                        int(layer), 
                        tile_data["type"], 
                        tile_data["variant"], 
                        f"{int(pos[0])};{int(pos[1])}", 
                        tile_data["pos"],
                        no_neighbours
                    )

                if self.editor_flag:
                    if int(layer) not in self.game.layers:
                        self.game.layers[int(layer)] = {}
                    self.game.layers[int(layer)][f"{int(pos[0])};{int(pos[1])}"] = {
                        "type" : tile_data["type"],
                        "variant" : tile_data["variant"],
                        "pos" : tile_data["pos"]
                    }

                else:
                    if int(pos[0]) not in tile_x:
                        tile_x.add(int(pos[0]))
                    if int(pos[1]) not in tile_y:
                        tile_y.add(int(pos[1]))

                    if int(pos[0]) < lowest_x:
                        lowest_x = int(pos[0])
                    if int(pos[1]) < lowest_y:
                        lowest_y = int(pos[1])

        self.offgrid_tiles = []
        for dic in data["offgrid"]:
            extra: dict = dic.copy()
            del extra["type"]
            del extra["variant"]
            del extra["pos"]

            self.add_offgrid_tile(
                dic["type"],
                dic["variant"],
                dic["pos"],
                extra
            )

        if not self.editor_flag: 
            self.max_tile_x = len(tile_x)
            self.max_tile_y = len(tile_y)
            self.generate_map([self.max_tile_x, self.max_tile_y], [lowest_x, lowest_y])
            self.nature_manager.clump_water()

        ##################################################################################
        
    #list of tiles currently around the (player) pos
    def tiles_around(self, pos) -> list[Tile]:
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOUR_OFFSETS:
            check_loc = f"{str(tile_loc[0] + offset[0])};{str(tile_loc[1] + offset[1])}"
            layer = 0
            if check_loc in self.tilemap[layer]:
                tiles.append(self.tilemap[layer][check_loc])
        return tiles

    #list of tiles currently around the (player) pos that are collide-able
    def nearby_physics_rects(self, pos) -> list[pygame.Rect]:
        rects = []
        for tile in self.tiles_around(pos):
            # if tile.type in PHYSICS_TILES:
                rects.append(pygame.Rect((tile.pos[0]) * self.tile_size, (tile.pos[1]) * self.tile_size, self.tile_size, self.tile_size))
        return rects
    
    def enemy_tile_infront_to_walk(self, pos, direction:str, dist: float = 45) -> bool:

        if direction == "right":
            offset = (1, 0)
        else:
            offset = (-1, 0)
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        check_loc = f"{str(tile_loc[0] + offset[0])};{str(tile_loc[1]+offset[1])}"
        if check_loc in self.tilemap[(layer := 0)]:
            return False

        offsets = [((i+1) * (-1 if direction == "left" else 1), 1) for i in range((dist // self.tile_size) + 1)]
        can = 0

        for offset in offsets:
            tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
            check_loc = f"{str(tile_loc[0] + offset[0])};{str(tile_loc[1]+offset[1])}"
            if check_loc in self.tilemap[(layer := 0)]:
                can += 1
        
        return can == len(offsets)

        ##################################################################################

    def render(self):
        # section_map = crop(self.map, self.game.offset.x - self.lowest_x * TILE_SIZE, self.game.offset.y - self.lowest_y * TILE_SIZE, WIDTH, HEIGHT)
        # section_map.set_colorkey((0, 0, 0))
        # self.game.screen.blit(section_map, (0, 0))
        return [self.front_map, self.back_map]

    def offgrid_render(self):
        for tile in self.offgrid_tiles:
            if tile.type == "bridge":
                if (self.game.offset.x - TILE_SIZE < tile.pos[0] < self.game.offset.x + WIDTH and
                    self.game.offset.y - TILE_SIZE < tile.pos[1] < self.game.offset.y + HEIGHT):
                    yield tile
                elif (self.game.offset.x - TILE_SIZE < tile.end_pos[0] < self.game.offset.x + WIDTH and
                    self.game.offset.y - TILE_SIZE < tile.end_pos[1] < self.game.offset.y + HEIGHT):
                    yield tile

            elif (self.game.offset.x - TILE_SIZE < tile.pos[0] < self.game.offset.x + WIDTH and
                self.game.offset.y - TILE_SIZE < tile.pos[1] < self.game.offset.y + HEIGHT):
                yield tile

    def on_screen_tiles(self, offset, buffer=[0, 0]):
        start_x = int(offset.x // (self.tile_size) - buffer[0])
        end_x = int((offset.x + self.map.get_width()) // self.tile_size  + buffer[0]) + 1
        start_y = int(offset.y // (self.tile_size) - buffer[1])
        end_y = int((offset.y + self.map.get_height()) // self.tile_size + buffer[1]) + 1

        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                loc = f"{x};{y}"
                if loc in self.tilemap[0]:
                    tile: Tile = self.tilemap[0][loc]

                    # if tile.type not in INVISIBLE_TILES or self.editor_flag == True:
                    yield tile



class Map_Container:
    def __init__(self, game, map, lowest_x, lowest_y, z):
        self.game = game
        self.z = z

        self.map = map
        self.lowest_x = lowest_x
        self.lowest_y = lowest_y

    def update(self, screen=None, flags=None):
        section_map = crop(self.map, self.game.offset.x - self.lowest_x * TILE_SIZE, self.game.offset.y - self.lowest_y * TILE_SIZE, WIDTH, HEIGHT)
        section_map.set_colorkey((0, 0, 0))

        screen: pygame.Surface = screen or self.game.screen
        if flags:
            screen.blit(section_map, (0, 0), special_flags=flags)
        else:
            screen.blit(section_map, (0, 0))
import contextlib
with contextlib.redirect_stdout(None):
    import pygame; pygame.init()
    from pygame.locals import *
    
import os

from scripts.config.SETTINGS import TILE_SIZE, WIDTH, HEIGHT, Z_LAYERS
from scripts.utils.CORE_FUNCS import add_loaded_sprite_number, vec
from scripts.utils.spritesheets import Spritesheet

    ##############################################################################################

class Tile(pygame.sprite.Sprite):

    AUTO_TILE_TYPES = {'grass', 'stone', "midground"}
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
        },
        "midground" : {
            tuple(sorted([(1, 0), (0, 1)])): {"choices" : list(range(0, 12)), "weights" : [1 for i in range(12)]},                           
            tuple(sorted([(1, 0), (0, 1), (-1, 0)])): {"choices" : list(range(12, 24)), "weights" : [1 for i in range(12)]},             
            tuple(sorted([(-1, 0), (0, 1)])): {"choices" : list(range(24, 36)), "weights" : [1 for i in range(12)]},                           
            tuple(sorted([(1, 0), (0, -1), (0, 1)])): {"choices" : list(range(36, 48)), "weights" : [1 for i in range(12)]},              
            tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): {"choices" : list(range(48, 60)), "weights" : [1 for i in range(12)]}, 
            tuple(sorted([(-1, 0), (0, -1), (0, 1)])): {"choices" : list(range(60, 72)), "weights" : [1 for i in range(12)]},              
            tuple(sorted([(1, 0), (0, -1)])): {"choices" : list(range(72, 84)), "weights" : [1 for i in range(12)]},                             
            tuple(sorted([(-1, 0), (0, -1), (1, 0)])): {"choices" : list(range(84, 96)), "weights" : [1 for i in range(12)]},               
            tuple(sorted([(-1, 0), (0, -1)])): {"choices" : list(range(96, 108)), "weights" : [1 for i in range(12)]},                             
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
                if name.startswith("midground"):
                    imgs = Spritesheet.midground_handler(name)
                else:
                    imgs = Spritesheet.tile_handler(name)
                add_loaded_sprite_number(len(imgs))
                cls.SPRITES[name.lower()] = imgs


        cls.NORMAL_LIGHT_MAPS = {}
        path = "assets/light_maps/tiles"

        for name in os.listdir(path):
            img = pygame.image.load(f"{path}/{name}").convert_alpha()
            img.set_colorkey((0, 0, 0))
            add_loaded_sprite_number(1)
            cls.NORMAL_LIGHT_MAPS[int(name.split(".")[0])] = img

    def __init__(self, game, type_, variant, pos, normal=None):
        super().__init__()
        self.game = game
        self.screen = self.game.screen

        self.type = type_ #tile type e.g. grass, the folder
        self.variant = variant #tile variant e.g. grass_8, the asset itself
        self.pos = pos
        self.z = Z_LAYERS["foreground tiles"]

        self.normal = normal

    #dictionary object used for json saving
    @property
    def dict(self) -> dict:
        return {"type":self.type, "variant":self.variant, "pos":self.pos}
    
    #actually draw it onto the screen
    def update(self, transparent=False, dim=0):
        if self.normal == None:
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

        if self.normal != None and self.normal != 4:
            # self.screen.blit(Tile.NORMAL_LIGHT_MAPS[self.normal], [
            #     (self.pos[0] * TILE_SIZE) - self.game.offset.x, 
            #     (self.pos[1] * TILE_SIZE) - self.game.offset.y
            # ])
            self.game.state_loader.current_state.light_manager.add_tile_highlight(Tile.NORMAL_LIGHT_MAPS[self.normal], vec(self.pos) * TILE_SIZE)

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
    
    @classmethod
    def create_offgrid_tile(cls, game, type_, variant, pos, *kwargs):
        from scripts.world_loading.custom_offgrid import Torch, Bridge
        
        if type_ == "torch":
            return Torch(game, variant, pos)
        elif type_ == "bridge":
            return Bridge(game, variant, pos, *kwargs)
        else:
            return Offgrid_Tile(game, type_, variant, pos, *kwargs)

    def __init__(self, game, type_, variant, pos, *kwargs):
        super().__init__()
        self.game = game
        self.screen = self.game.screen

        self.type = type_
        self.variant = variant
        self.pos = pos
        self.z = Z_LAYERS["background offgrid"]

        try:
            other: dict = [*kwargs[0]][0]
            if len(other.keys()):
                for key, value in other.items():
                    setattr(self, key, value)
        except IndexError:
            pass

    @property
    def dict(self):
        info = self.__dict__.copy()
        for unneeded in ['_Sprite__g', '_Sprite__image', '_Sprite__rect', 'game', 'screen', 'z']:
            del info[unneeded]
        return info
    
    def update(self):
        img = Offgrid_Tile.SPRITES[self.type][self.variant]

        if self.type == "bridge":
            pygame.draw.line(self.screen, (255, 0, 0), self.pos - self.game.offset + vec(img.size) / 2, self.end_pos- self.game.offset + vec(img.size) / 2, 2)
            self.screen.blit(img, self.pos - self.game.offset)
            self.screen.blit(img, self.end_pos - self.game.offset)
            return
        
        self.screen.blit(img, self.pos - self.game.offset)
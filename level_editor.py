import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *
    
import random
import sys
from typing import Literal

from scripts.world_loading.backgrounds import Editor_Background
from scripts.world_loading.tilemap import Tilemap
from scripts.world_loading.tiles import Tile, Offgrid_Tile

from scripts.config.SETTINGS import SIZE, FPS, WIDTH, HEIGHT, TILE_SIZE
from scripts.utils.CORE_FUNCS import vec, check_loaded_sprite_number

pygame.Rect = pygame.FRect

    ##############################################################################################

class BreakParticle(pygame.sprite.Sprite):
    def __init__(self, game, groups, pos, col):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen

        self.tilesize = 2
        self.col = col

        self.image = pygame.Surface((self.tilesize, self.tilesize))
        self.image.fill(self.col)
        self.rect = self.image.get_rect(topleft=pos)
        self.x = random.uniform(-2, 2)

        self.grav = random.uniform(0, 5)
        self.alpha = 255
        self.decay = random.randint(10, 16)

    def update(self):
        self.alpha -= self.decay
        self.image.set_alpha(self.alpha)

        if self.alpha <= 0:
            self.kill()

        self.rect.x += self.x
        self.rect.y -= self.grav
        self.grav -= random.uniform(0, 1)

        self.draw()

    def draw(self):
        self.screen.blit(self.image, self.rect.topleft)


class PlaceParticle(pygame.sprite.Sprite):
    def __init__(self, game, groups, pos):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen

        self.pos = pos
        self.timer = 0

    def update(self):
        self.timer += 2
        if self.timer > 32:
            self.kill()
        self.draw()

    def draw(self):
        rect = pygame.Rect(0, 0, self.timer, self.timer)
        rect.center = self.pos - self.game.offset
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 1)

    ##############################################################################################

class Editor:
    def __init__(self):
        self.initialise()

        #initalising pygame window
        flags = pygame.RESIZABLE | pygame.SCALED
        self.screen = pygame.display.set_mode(SIZE, flags)
        pygame.display.toggle_fullscreen()
        self.clock = pygame.time.Clock()
        self.running = True

        self.offset = vec(-5, 7)
        self.scroll_speed = 5
        self.background = Editor_Background(self)
        self.font = pygame.font.SysFont('Verdana', 10)
        self.particles = pygame.sprite.Group()

        self.tilemap = Tilemap(self, editor_flag=True)
        self.cache_sprites()
        check_loaded_sprite_number()
        self.on_grid = True

        self.assets = Tile.SPRITES.copy()
        self.asset_names = list(self.assets.keys())
        self.current_tilegroup = 0
        self.current_tilevariant = 0
        self.l_flood_start = None
        self.r_flood_start = None

        self.offgrid_assets = Offgrid_Tile.SPRITES.copy()
        self.offgrid_names = list(self.offgrid_assets.keys())
        self.offgrid_tilegroup = 0
        self.offgrid_tilevariant = 0

        self.sidebar_open = False
        self.sidebar = pygame.Surface((WIDTH/4, HEIGHT), pygame.SRCALPHA)
        self.sidebar.fill((68, 63, 86))
        self.sidebar_pos = vec(WIDTH*1.5, 0)
        self.sidebar_yscroll = 0
        self.spring_vel = vec()

        self.left_button = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.polygon(self.left_button, (92, 78, 115), [(0, h := self.left_button.get_height()/2), (h*2, 0), (h*2, h*2)])
        self.left_shadow = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.polygon(self.left_shadow, (92-50, 78-50, 115-50), [(0, h := self.left_button.get_height()/2), (h*2, 0), (h*2, h*2)])
        self.right_button = pygame.transform.flip(self.left_button, True, False)
        self.right_shadow = pygame.transform.flip(self.left_shadow, True, False)
        self.left_right_button_pressed = False
        self.delta_l = self.delta_r = 0

        self.layers = {0 : {}}
        self.current_layer = -1

    def initialise(self):
        pygame.init()  #general pygame
        pygame.font.init() #font stuff
        pygame.display.set_caption("Platformer - Level Editor") #Window Title

        pygame.mixer.pre_init(44100, 16, 2, 4096) #music stuff
        pygame.mixer.init()

        pygame.event.set_blocked(None) #setting allowed events to reduce lag
        pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEWHEEL])

    def cache_sprites(self):
        Tile.cache_sprites()
        Offgrid_Tile.cache_sprites()

        ##################################################################################

    def calculate_offset(self):
        keys = pygame.key.get_pressed()
        speed = vec()
        if keys[pygame.K_a]:
            speed.x -= self.scroll_speed
        if keys[pygame.K_d]:
            speed.x += self.scroll_speed
        if keys[pygame.K_w]:
            speed.y -= self.scroll_speed
        if keys[pygame.K_s]:
            speed.y += self.scroll_speed
        
        if keys[pygame.K_LSHIFT]:
            speed *= 2
        self.offset += speed

        ##################################################################################

    def sidebar_update(self):
        #backdrop shadow
        shadow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shadow.fill((10, 10, 10))
        shadow.set_alpha(160)
        self.screen.blit(shadow, (0, 0))

        #resetting the sidebar itself
        self.sidebar = pygame.Surface((WIDTH/3, HEIGHT), pygame.SRCALPHA)
        self.sidebar.fill((68, 63, 86))

        #the actual tiles themselves
        current_tilegroup = self.asset_names[self.current_tilegroup]
        self.sidebar_tiles_update(current_tilegroup)

        #tile title
        if self.on_grid:
            label_shadow = self.font.render(current_tilegroup.capitalize(), False, (40, 40, 40))
            label = self.font.render(current_tilegroup.capitalize(), False, (255, 255, 255))
        else:
            label_shadow = self.font.render(self.offgrid_names[self.offgrid_tilegroup].capitalize(), False, (40, 40, 40))
            label = self.font.render(self.offgrid_names[self.offgrid_tilegroup].capitalize(), False, (255, 255, 255))
        self.sidebar.blit(label_shadow, (13, label.get_height()+1))
        self.sidebar.blit(label, (12, label.get_height()))
            
        #the left and right buttons
        self.delta_l = self.delta_r = 0
        self.left_right_button_update()
        self.sidebar.blit(self.left_shadow, (WIDTH/4 - (self.left_button.get_width() * 3) + 11, 9 + self.delta_l))
        self.sidebar.blit(self.left_button, (WIDTH/4 - (self.left_button.get_width() * 3) + 10, 7 + self.delta_l))
        self.sidebar.blit(self.right_shadow, (WIDTH/4 - (self.left_button.get_width() * 2) + 9+5, 9 + self.delta_r))
        self.sidebar.blit(self.right_button, (WIDTH/4 - (self.left_button.get_width() * 2) + 10+5, 7 + self.delta_r))

        #updating the sidebar's position using a spring 
        stiffness = 0.2
        damping = 0.35
        self.spring_vel = self.spring_vel.lerp((vec(WIDTH * 0.75, 0) - self.sidebar_pos) * stiffness, damping)
        if self.spring_vel.magnitude() < .1:
            self.spring_vel = vec()
            self.sidebar_pos = vec(WIDTH * 0.75, 0)
        self.sidebar_pos += self.spring_vel

        self.screen.blit(self.sidebar, self.sidebar_pos)

                ##################################################################

    def sidebar_tiles_update(self, current_tilegroup):
        mouse = pygame.mouse.get_pressed()
        mousePos = pygame.mouse.get_pos()

        if self.on_grid:
            assets = self.assets[current_tilegroup]
            for i, asset in enumerate(assets):

                tile_size = TILE_SIZE
                asset = pygame.transform.scale(asset.copy(), (tile_size, tile_size))
                mask = pygame.mask.from_surface(asset)
                mask.invert()
                shadow = mask.to_surface()
                shadow.set_colorkey((255, 255, 255))
                mask.invert()

                row_num = 5
                x = (i % row_num)  * tile_size + ((i % row_num) * 5) + 8 
                y = (i // row_num) * tile_size + ((i // row_num) * 5) + 37

                if y + self.sidebar_yscroll < tile_size/2:
                    continue
                elif tile_size / 2 < y + self.sidebar_yscroll < tile_size:
                    dist = tile_size - (y + self.sidebar_yscroll)
                    alpha = 255 - (255 * (dist / 11))
                    asset.set_alpha(alpha)
                    shadow.set_alpha(alpha)
                    
                self.sidebar.blit(shadow, (x+2, y+2 + self.sidebar_yscroll))
                
                if pygame.Rect([x + WIDTH*0.75, y + self.sidebar_yscroll, *asset.get_size()]).collidepoint(mousePos):
                    self.sidebar.blit(asset, (x, y-2 + self.sidebar_yscroll))
                    pygame.draw.polygon(
                        self.sidebar, 
                        (220, 220, 220, 192), 
                        [vec(p) + vec(x, y-2 + self.sidebar_yscroll) for p in mask.outline()], 
                        2
                    )

                    if mouse[0]:
                        self.current_tilevariant = i
                else:
                    self.sidebar.blit(asset, (x, y + self.sidebar_yscroll))
        else:
            assets = self.offgrid_assets[self.offgrid_names[self.offgrid_tilegroup]]

            x = 8
            y = 37
            for i, asset in enumerate(assets):
                asset: pygame.Surface
                mask = pygame.mask.from_surface(asset)
                mask.invert()
                shadow = mask.to_surface()
                shadow.set_colorkey((255, 255, 255))
                mask.invert()

                if y + self.sidebar_yscroll < asset.get_height()/2:
                    continue
                elif asset.get_height() / 2 < y + self.sidebar_yscroll < asset.get_height():
                    dist = asset.get_height() - (y + self.sidebar_yscroll)
                    alpha = 255 - (255 * (dist / 11))
                    asset.set_alpha(alpha)
                    shadow.set_alpha(alpha)
                    
                self.sidebar.blit(shadow, (x+2, y+2 + self.sidebar_yscroll))
                
                if pygame.Rect([x + WIDTH*0.75, y + self.sidebar_yscroll, *asset.get_size()]).collidepoint(mousePos):
                    self.sidebar.blit(asset, (x, y-2 + self.sidebar_yscroll))
                    pygame.draw.polygon(
                        self.sidebar, 
                        (220, 220, 220, 192), 
                        [vec(p) + vec(x, y-2 + self.sidebar_yscroll) for p in mask.outline()], 
                        2
                    )

                    if mouse[0]:
                        self.offgrid_tilevariant = i
                else:
                    self.sidebar.blit(asset, (x, y + self.sidebar_yscroll))

                x += asset.get_width() + 5
                if x > WIDTH/4:
                    y += asset.height() + 5
                    x = 8

    def left_right_button_update(self):
        mousePos = pygame.mouse.get_pos()
        mouse = pygame.mouse.get_pressed()
        if self.left_button.get_rect(topleft=(WIDTH - (self.left_button.get_width() * 3) + 10, 7)).collidepoint(mousePos):
            self.delta_l = -1
            if mouse[0]:
                if self.left_right_button_pressed == False:
                    if self.on_grid:
                        self.current_tilevariant = 0
                        self.sidebar_yscroll = 0
                        self.current_tilegroup -= 1
                        if self.current_tilegroup < 0:
                            self.current_tilegroup = len(self.asset_names) - 1
                    else:
                        self.offgrid_tilevariant = 0
                        self.sidebar_yscroll = 0
                        self.offgrid_tilegroup -= 1
                        if self.offgrid_tilegroup < 0:
                            self.offgrid_tilegroup = len(self.offgrid_names) - 1

                    self.left_right_button_pressed = True
            else:
                self.left_right_button_pressed = False

        elif self.right_button.get_rect(topleft=(WIDTH - (self.left_button.get_width() * 2) + 15, 7)).collidepoint(mousePos):
            self.delta_r = -1
            if mouse[0]:
                if self.left_right_button_pressed == False:
                    if self.on_grid:
                        self.current_tilevariant = 0
                        self.sidebar_yscroll = 0
                        self.current_tilegroup += 1
                        if self.current_tilegroup >= len(self.asset_names):
                            self.current_tilegroup = 0
                    else:
                        self.offgrid_tilevariant = 0
                        self.sidebar_yscroll = 0
                        self.offgrid_tilegroup += 1
                        if self.offgrid_tilegroup >= len(self.offgrid_names):
                            self.offgrid_tilegroup = 0
                    self.left_right_button_pressed = True
            else:
                self.left_right_button_pressed = False

                ##################################################################

    def sidebar_reset(self):
        self.sidebar_pos = vec(WIDTH*1.5, 0)
        self.sidebar_yscroll = 0

        ##################################################################################

    def mouse_stuff(self, current_img):
        keys = pygame.key.get_pressed()
        mousePos = pygame.mouse.get_pos()
        mouse = pygame.mouse.get_pressed()

        if self.on_grid:
            tilePos = (
                int((mousePos[0] + self.offset.x) // TILE_SIZE), 
                int((mousePos[1] + self.offset.y) // TILE_SIZE))
            tile_loc = str(tilePos[0]) + ";" + str(tilePos[1])
            self.screen.blit(current_img, (vec(tilePos) * TILE_SIZE) - self.offset)
        else:  
            self.screen.blit(current_img, [mousePos[0] - current_img.get_width()//2, mousePos[1] - current_img.get_height()//2])

        #breaking
        if mouse[0] or self.l_flood_start != None:
            if self.on_grid:
                if keys[pygame.K_RSHIFT] or keys[pygame.K_LALT]:
                    self.flood_left(tile_loc, tilePos, 'flood')
                else:
                    if self.l_flood_start != None:
                        self.flood_left(tile_loc, tilePos, 'erase')
                    else:
                        self.left_click(tile_loc, tilePos)
            else:
                self.offgrid_left_click()

        #placing
        if mouse[2] or self.r_flood_start != None:
            if self.on_grid:
                if keys[pygame.K_RSHIFT] or keys[pygame.K_LALT]:
                    self.flood_right(tile_loc, tilePos, 'flood', current_img)
                else:
                    if self.r_flood_start != None:
                        self.flood_right(tile_loc, tilePos, 'place')
                    else:
                        self.right_click(tile_loc, tilePos)
            else:
                self.offgrid_right_click(current_img)
                self.held = True
        else:
            self.held = False

        #pick-block
        if mouse[1]:
            if self.on_grid:
                if tile_loc in self.tilemap.tilemap[self.current_layer if self.current_layer != -1 else 0]:
                    tile: Tile = self.tilemap.tilemap[self.current_layer if self.current_layer != -1 else 0][tile_loc]
                    self.current_tilegroup = self.asset_names.index(tile.type)
                    self.current_tilevariant = tile.variant

                ##################################################################

    def left_click(self, tile_loc, tilePos):
        #making sure the layers start at 0
        #-1 is strictly for displaying in the editor
        layers = [self.current_layer] if self.current_layer != -1 else list(self.layers.keys())
        delete = False

        for current_layer in layers:
            if current_layer not in self.layers.keys() or current_layer not in self.tilemap.tilemap.keys(): 
                return

            if tile_loc in self.layers[current_layer]:
                del self.layers[current_layer][tile_loc]

            if tile_loc in self.tilemap.tilemap[current_layer]:
                tile: Tile = self.tilemap.tilemap[current_layer][tile_loc]
                img = Tile.SPRITES[tile.type][tile.variant]
                delete: pygame.Surface = img 
                del self.tilemap.tilemap[current_layer][tile_loc]

        if delete:
            for x in range(0, delete.get_width(), 2):
                for y in range(0, delete.get_height(), 2):
                    if random.randint(0, 1) == 0:
                        BreakParticle(
                            self,
                            [self.particles],
                            [tilePos[0] * TILE_SIZE + x - self.offset.x, tilePos[1] * TILE_SIZE + y - self.offset.y], 
                            delete.get_at((x, y)),
                        )


    def right_click(self, tile_loc, tilePos):
        #making sure the layers start at 0
        #-1 is strictly for displaying in the editor
        current_layer = self.current_layer if self.current_layer != -1 else 0

        #adding a new layer dict if it doesnt exist. this will need to be culled later to avoid 
        #tiles "behind" other tiles being blitted unnecessarily, and also cull empty dicts for file storage
        if current_layer not in self.layers.keys():
            self.layers[current_layer] = {}
            
        #actually adding the tile
        self.layers[current_layer][tile_loc] = {
            "type" : self.asset_names[self.current_tilegroup],
            "variant" : self.current_tilevariant,
            "pos" : [
                tilePos[0],
                tilePos[1]
            ]
        }
        
        self.tilemap.add_tile(
            layer = current_layer,
            type = self.asset_names[self.current_tilegroup],
            variant = self.current_tilevariant,
            tile_loc = tile_loc,
            pos = [
                tilePos[0],
                tilePos[1]
            ]
        )

        #particle effects
        PlaceParticle(
            self,
            [self.particles],
            [tilePos[0] * TILE_SIZE + TILE_SIZE/2, tilePos[1] * TILE_SIZE + TILE_SIZE/2], 
        )

                ##################################################################

    def flood_left(self, tile_loc, tilePos, mode: Literal["flood", "erase"]):

        if self.l_flood_start == None:
            self.l_flood_start = [c*self.tilemap.tile_size for c in tilePos]
        end_pos = [c*self.tilemap.tile_size for c in tilePos]
        zipped = list(zip(self.l_flood_start - self.offset, end_pos - self.offset))

        top_left = [min(zipped[0]), min(zipped[1])]
        bottom_right = [max(zipped[0]) + self.tilemap.tile_size, max(zipped[1]) + self.tilemap.tile_size]
        width = abs(zipped[0][0] - zipped[0][1]) + self.tilemap.tile_size
        height = abs(zipped[1][0] - zipped[1][1]) + self.tilemap.tile_size

        if mode == 'flood':
            pygame.draw.rect(self.screen, (255, 255, 255), [top_left[0], top_left[1], width, height], 5)
        
        elif mode == 'erase':
            self.l_flood_start = None

            delete = False
            tilePos = [0, 0]
            for x in range(int(top_left[0] + self.offset.x), int(bottom_right[0] + self.offset.x), self.tilemap.tile_size):
                tilePos[0] = x // self.tilemap.tile_size
                for y in range(int(top_left[1] + self.offset.y), int(bottom_right[1] + self.offset.y), self.tilemap.tile_size):
                    tilePos[1] = y // self.tilemap.tile_size
                    tileloc = str(tilePos[0]) + ";" + str(tilePos[1])

                    layers = [self.current_layer] if self.current_layer != -1 else list(self.layers.keys())
                    for current_layer in layers:
                        if current_layer not in self.layers.keys() or current_layer not in self.tilemap.tilemap.keys(): 
                            return
                        
                        if tileloc in self.layers[current_layer]:
                            del self.layers[current_layer][tileloc]

                        if tileloc in self.tilemap.tilemap[current_layer]:
                            tile: Tile = self.tilemap.tilemap[current_layer][tileloc]
                            img = Tile.SPRITES[tile.type][tile.variant]
                            delete: pygame.Surface = img 
                            del self.tilemap.tilemap[current_layer][tileloc]

                            for x1 in range(0, delete.get_width(), 2):
                                for y1 in range(0, delete.get_height(), 2):
                                    if random.randint(0, 1) == 0:
                                        BreakParticle(
                                            self,
                                            [self.particles],
                                            [tilePos[0] * TILE_SIZE + x1 - self.offset.x, tilePos[1] * TILE_SIZE + y1 - self.offset.y], 
                                            delete.get_at((x1, y1)),
                                        )

    def flood_right(self, tile_loc, tilePos, mode: Literal["flood", "place"], current_img=None):

        if self.r_flood_start == None:
            self.r_flood_start = [c*self.tilemap.tile_size for c in tilePos]
        end_pos = [c*self.tilemap.tile_size for c in tilePos]
        zipped = list(zip(self.r_flood_start - self.offset, end_pos - self.offset))

        top_left = [min(zipped[0]), min(zipped[1])]
        bottom_right = [max(zipped[0]) + self.tilemap.tile_size, max(zipped[1]) + self.tilemap.tile_size]
        width = abs(zipped[0][0] - zipped[0][1]) + self.tilemap.tile_size
        height = abs(zipped[1][0] - zipped[1][1]) + self.tilemap.tile_size

        if mode == 'flood':
            for x in range(int(top_left[0]), int(bottom_right[0]), self.tilemap.tile_size):
                for y in range(int(top_left[1]), int(bottom_right[1]), self.tilemap.tile_size):
                    self.screen.blit(current_img, (x, y))

            pygame.draw.rect(self.screen, (255, 255, 255), [top_left[0], top_left[1], width, height], 5)
        
        elif mode == 'place':
            self.r_flood_start = None
            tile_Pos = [0, 0]
            for x in range(int(top_left[0] + self.offset.x), int(bottom_right[0] + self.offset.x), self.tilemap.tile_size):
                tile_Pos[0] = x // self.tilemap.tile_size
                for y in range(int(top_left[1] + self.offset.y), int(bottom_right[1] + self.offset.y), self.tilemap.tile_size):
                    tile_Pos[1] = y // self.tilemap.tile_size
                    tileloc = str(tile_Pos[0]) + ";" + str(tile_Pos[1])

                    current_layer = self.current_layer if self.current_layer != -1 else 0
                    if current_layer not in self.layers.keys():
                        self.layers[current_layer] = {}
                        
                    self.layers[current_layer][tile_loc] = {
                        "type" : self.asset_names[self.current_tilegroup],
                        "variant" : self.current_tilevariant,
                        "pos" : [
                            tilePos[0],
                            tilePos[1]
                        ]
                    }
    
                    self.tilemap.add_tile(
                        layer = current_layer,
                        type = self.asset_names[self.current_tilegroup],
                        variant = self.current_tilevariant,
                        tile_loc = tileloc,
                        pos = [
                            tile_Pos[0],
                            tile_Pos[1]
                        ]
                    )
                    
                    PlaceParticle(
                        self,
                        [self.particles],
                        [tile_Pos[0] * TILE_SIZE + TILE_SIZE/2, tile_Pos[1] * TILE_SIZE + TILE_SIZE/2], 
                    )

                ##################################################################

    def offgrid_left_click(self):
        mousePos = pygame.mouse.get_pos()
        for tile in self.tilemap.offgrid_tiles.copy():
            tile_img = self.offgrid_assets[self.offgrid_names[self.offgrid_tilegroup]][self.offgrid_tilevariant].copy()
            tile_r = pygame.Rect(tile.pos[0] - self.offset.x, tile.pos[1] - self.offset.y, *tile_img.get_size())
            if tile_r.collidepoint(mousePos):
                self.tilemap.offgrid_tiles.remove(tile)

    def offgrid_right_click(self, current_img):
        if not self.held:
            mousePos = pygame.mouse.get_pos()
            pos = [mousePos[0] - current_img.get_width()//2 + self.offset.x, mousePos[1] - current_img.get_height()//2 + self.offset.y]
            
            if pos not in [t.pos for t in self.tilemap.offgrid_tiles]:
                self.tilemap.add_offgrid_tile(
                    type = self.offgrid_names[self.offgrid_tilegroup],
                    variant = self.offgrid_tilevariant,
                    pos = pos
                )
                    
                PlaceParticle(
                    self,
                    [self.particles],
                    [pos[0] + current_img.get_width() // 2, pos[1] + current_img.get_height() // 2], 
                )

        ##################################################################################

    def handle_events(self):
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEWHEEL:
                if not self.sidebar_open:
                    if self.on_grid:
                        if keys[pygame.K_LSHIFT]:
                            self.current_tilegroup -= event.y
                            if self.current_tilegroup >= len(self.asset_names):
                                self.current_tilegroup = 0
                            elif self.current_tilegroup < 0:
                                self.current_tilegroup = len(self.asset_names) - 1
                            self.current_tilevariant = 0

                        else:
                            self.current_tilevariant -= event.y
                            if self.current_tilevariant >= len(self.assets[self.asset_names[self.current_tilegroup]]):
                                self.current_tilevariant = 0
                            elif self.current_tilevariant < 0:
                                self.current_tilevariant = len(self.assets[self.asset_names[self.current_tilegroup]]) - 1

                    else:
                        if keys[pygame.K_LSHIFT]:
                            self.offgrid_tilegroup -= event.y
                            if self.offgrid_tilegroup >= len(self.offgrid_names):
                                self.offgrid_tilegroup = 0
                            elif self.offgrid_tilegroup < 0:
                                self.offgrid_tilegroup = len(self.offgrid_names) - 1
                            self.offgrid_tilevariant = 0

                        else:
                            self.offgrid_tilevariant -= event.y
                            if self.offgrid_tilevariant >= len(self.offgrid_assets[self.offgrid_names[self.offgrid_tilegroup]]):
                                self.offgrid_tilevariant = 0
                            elif self.offgrid_tilevariant < 0:
                                self.offgrid_tilevariant = len(self.offgrid_assets[self.offgrid_names[self.offgrid_tilegroup]]) - 1
                else:
                    self.sidebar_yscroll = min(0, self.sidebar_yscroll + event.y * 8)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.running = False

                elif event.key == pygame.K_g:
                    self.on_grid = not self.on_grid

                elif event.key == pygame.K_TAB:
                    if self.sidebar_open == False:
                        self.sidebar_reset()
                    self.sidebar_open = not self.sidebar_open

                elif event.key == pygame.K_ESCAPE:
                    if self.sidebar_open:
                        self.sidebar_open = False

                elif event.key == pygame.K_COMMA:
                    self.current_layer -= 1
                    if self.current_layer < -1:
                        self.current_layer = -1
                elif event.key == pygame.K_PERIOD:
                    self.current_layer += 1

                if event.key == pygame.K_s and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                    self.tilemap.save()
                if event.key == pygame.K_o and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                    self.tilemap.load()
                if event.key == pygame.K_t and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                    self.tilemap.auto_tile()

    def run(self):
        last_time = pygame.time.get_ticks()
        while self.running:
            #deltatime
            self.dt = (current_time := pygame.time.get_ticks()) - last_time
            self.dt /= 1000
            last_time = current_time

            self.handle_events()
            self.screen.fill((30, 30, 30))
            self.background.update()

            #render tiles
            for layer in sorted(self.tilemap.tilemap.keys(), reverse=True):
                for tile in self.tilemap.tilemap[layer].keys():
                    tile: Tile = self.tilemap.tilemap[layer][tile]
                    if pygame.Rect((tile.pos[0] * TILE_SIZE) - self.offset.x, 
                                (tile.pos[1] * TILE_SIZE) - self.offset.y,
                                TILE_SIZE, TILE_SIZE).colliderect(pygame.Rect(0, 0, WIDTH, HEIGHT)):
                        tile.update(transparent=(layer != self.current_layer) and (not (self.current_layer == -1)), dim=layer * 20)

            #render offgrid tiles
            for tile in self.tilemap.offgrid_tiles:
                tile.update()

            #particles obviously
            self.particles.update()

            #axes
            pygame.draw.line(self.screen, (150, 150, 150), (-self.offset.x, 0), (-self.offset.x, HEIGHT), 1)
            pygame.draw.line(self.screen, (150, 150, 150), (0, HEIGHT - self.offset.y - 8), (WIDTH, HEIGHT - self.offset.y - 8), 1)

            #camera offset
            self.calculate_offset()
            offset_surf = self.font.render(f"{[int(self.offset.x), int(self.offset.y + 8)]}", False, (255, 255, 255))
            self.screen.blit(offset_surf, (5, HEIGHT-15))

            #lil transparent render of current object in top left corner
            if self.on_grid:
                current_tile_img = self.assets[self.asset_names[self.current_tilegroup]][self.current_tilevariant].copy()
            else:
                current_tile_img = self.offgrid_assets[self.offgrid_names[self.offgrid_tilegroup]][self.offgrid_tilevariant].copy()
            current_tile_img.set_alpha(100)
            self.screen.blit(current_tile_img, (16, 16))

            #mouse input handler for placing, breaking, picking tiles etc
            if not self.sidebar_open:
                self.mouse_stuff(current_tile_img)

            #help shortcuts
            if pygame.key.get_pressed()[pygame.K_h]:
                labels = [
                    "CTRL + O: Load File",
                    "CTRL + S: Save File",
                    "CTRL + T: Auto Tile",
                    "",
                    "<> : Change Layer",
                    "TAB : Tile Menu",
                    "G: Toggle Grid",
                    "",
                    "SHIFT+WASD : Speed",
                    "WASD: Move",
                    "",
                    "ALT + Click: Flood Fill/Place",
                    "RMB: Place",
                    "MMB: Pick",
                    "LMB: Break",
                ]
                for i, text in enumerate(labels):
                    label = self.font.render(text, False, (255, 255, 255))
                    self.screen.blit(label, label.get_rect(right=WIDTH-5, y = HEIGHT-15-(10*i)))
            else:
                label = self.font.render("Press H for Shortcuts", False, (255, 255, 255))
                self.screen.blit(label, label.get_rect(right=WIDTH-5, y = HEIGHT-15))

            if self.on_grid:
                #the current layer displayed (0 for everything, otherwise the nth layer with everything else transluscent)
                layer_label = self.font.render(f"{'Layer: '  + (str(self.current_layer) if self.current_layer > -1 else 'ALL'):>11}", False, (255, 255, 255))
                self.screen.blit(layer_label, layer_label.get_rect(right=WIDTH-5, y=5))

            if self.sidebar_open:
                self.sidebar_update()

            pygame.display.update()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()
    

    ##############################################################################################

if __name__ == "__main__":
    game = Editor()
    game.run()
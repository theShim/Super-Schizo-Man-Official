import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *
    
import random

from scripts.config.SETTINGS import SIZE, FPS
from scripts.utils.CORE_FUNCS import vec

pygame.Rect = pygame.FRect

    ##############################################################################################

class BreakParticle(pygame.sprite.Sprite):
    def __init__(self, pos, col, parent):
        super().__init__()
        self.parent = parent
        self.tilesize = 2
        self.col = col

        self.image = pygame.Surface((self.tilesize, self.tilesize))
        self.image.fill(self.col)
        self.rect = self.image.get_rect(topleft=pos)
        self.alpha = 255
        self.x = random.uniform(-2, 2)

        self.grav = random.uniform(0, 5)

    def update(self, screen):
        self.alpha -= 12
        self.image.set_alpha(self.alpha)

        if self.alpha <= 0:
            self.parent.remove(self)

        self.rect.x += self.x
        self.rect.y -= self.grav
        self.grav -= random.uniform(0, 1)

        self.draw(screen)

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class PlaceParticle(pygame.sprite.Sprite):
    def __init__(self, pos, parent):
        super().__init__()
        self.pos = pos
        self.parent: pygame.sprite.Group = parent
        self.timer = 0

    def update(self, screen):
        self.timer += 2
        if self.timer > 32:
            self.parent.remove(self)
        self.draw(screen)

    def draw(self, screen):
        rect = pygame.Rect(0, 0, self.timer, self.timer)
        rect.center = self.pos - editor.offset
        pygame.draw.rect(screen, (255, 255, 255), rect, 1)

    ##############################################################################################

class Editor:
    def __init__(self):
        self.initialise()

        self.offset = vec()
        self.scroll_speed = 5
        self.clock = pygame.time.Clock()

        self.tilemap = Tilemap(self)
        self.particles = pygame.sprite.Group()


        self.full_tiles = {'grass', 'stone'} #tiles that should be scaled up
        tile_names = None
        sprite_groups = []
        for i, x in enumerate(os.walk("assets/tiles")):
            if i == 0:
                tile_names = x[1]
                continue

            path = x[0]
            imgs = sorted(x[2], key=lambda x: int(x.split(".")[0]))

            sprites = []
            for img in imgs:
                img_path = path + "/" + img
                spr = pygame.image.load(img_path).convert_alpha()

                if len(list(filter(path.endswith, self.full_tiles))):
                    spr = pygame.transform.scale(spr, (TILE_SIZE, TILE_SIZE))
                    
                spr.set_colorkey((0, 0, 0))
                sprites.append(spr)
            sprite_groups.append(sprites)

        self.assets = {}
        for i, name in enumerate(tile_names):
            self.assets[name] = sprite_groups[i]
        self.asset_names = tile_names


        self.sidebar_open = False
        self.sidebar = pygame.Surface((WIDTH/4, HEIGHT), pygame.SRCALPHA)
        self.sidebar.fill((68, 63, 86))
        self.sidebar_pos = vec(WIDTH*1.5, 0)
        self.sidebar_yscroll = 0

        self.current_tilegroup = 0
        self.current_tilevariant = 0
        self.l_flood_start = None
        self.r_flood_start = None

        self.left_button = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.polygon(self.left_button, (92, 78, 115), [(0, h := self.left_button.get_height()/2), (h*2, 0), (h*2, h*2)])
        self.left_shadow = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.polygon(self.left_shadow, (92-50, 78-50, 115-50), [(0, h := self.left_button.get_height()/2), (h*2, 0), (h*2, h*2)])
        self.right_button = pygame.transform.flip(self.left_button, True, False)
        self.right_shadow = pygame.transform.flip(self.left_shadow, True, False)
        self.left_right_button_pressed = False

        self.layers = {0 : {}}
        self.current_layer = 0
    
        ######################################################################################

    def initialise(self):
        pygame.init()  #general pygame
        pygame.display.set_caption("Super Schizo Man - LEVEL EDITOR")

        pygame.font.init() #font stuff
        self.font = pygame.font.SysFont('Verdana', 10)

        #music stuff
        pygame.mixer.pre_init(44100, 16, 2, 4096)
        pygame.mixer.init()

        #setting allowed events to reduce lag
        pygame.event.set_blocked(None) 
        pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEWHEEL])
        
        #initalising pygame window
        flags = pygame.RESIZABLE | pygame.SCALED
        self.screen = pygame.display.set_mode(SIZE, flags)
        pygame.display.toggle_fullscreen()

        Tile.cache_sprites()

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

    def mouse_stuff(self, current_img):
        keys = pygame.key.get_pressed()
        mousePos = pygame.mouse.get_pos()
        mouse = pygame.mouse.get_pressed()

        tilePos = (
            int((mousePos[0] + self.offset.x) // TILE_SIZE), 
            int((mousePos[1] + self.offset.y) // TILE_SIZE))
        tile_loc = str(tilePos[0]) + ";" + str(tilePos[1])

        self.screen.blit(current_img, (vec(tilePos) * TILE_SIZE) - self.offset)


        #breaking
        if mouse[0] or self.l_flood_start != None:
            if keys[pygame.K_RSHIFT] or keys[pygame.K_LALT]:
                self.flood_left(tile_loc, tilePos, 'flood')
            else:
                if self.l_flood_start != None:
                    self.flood_left(tile_loc, tilePos, 'erase')
                else:
                    self.left_click(tile_loc, tilePos)

        #placing
        if mouse[2] or self.r_flood_start != None:
            if keys[pygame.K_RSHIFT] or keys[pygame.K_LALT]:
                self.flood_right(tile_loc, tilePos, 'flood', current_img)
            else:
                if self.r_flood_start != None:
                    self.flood_right(tile_loc, tilePos, 'place')
                else:
                    self.right_click(tile_loc, tilePos)
        else:
            self.held = False

        #pick-block
        if mouse[1]:
            if tile_loc in self.tilemap.tilemap[self.current_layer]:
                tile: Tile = self.tilemap.tilemap[self.current_layer][tile_loc]
                self.current_tilegroup = self.asset_names.index(tile.type)
                self.current_tilevariant = tile.variant



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

                    if tileloc in self.tilemap.tilemap[self.current_layer]:
                        tile: Tile = self.tilemap.tilemap[self.current_layer][tileloc]
                        img = Tile.SPRITES[tile.type][tile.variant]
                        delete: pygame.Surface = img 
                        del self.tilemap.tilemap[self.current_layer][tileloc]

                        for x1 in range(0, delete.get_width(), 2):
                            for y1 in range(0, delete.get_height(), 2):
                                if random.randint(0, 1) == 0:
                                    self.particles.add(BreakParticle(
                                        [tilePos[0] * self.tilemap.tile_size + x1 - self.offset.x, 
                                         tilePos[1] * self.tilemap.tile_size + y1 - self.offset.y], 
                                        delete.get_at((x1, y1)),
                                        self.particles
                                    ))

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
    
                    self.tilemap.add_tile(
                        layer = self.current_layer,
                        type = self.asset_names[self.current_tilegroup],
                        variant = self.current_tilevariant,
                        tile_loc = tileloc,
                        pos = [
                            tile_Pos[0],
                            tile_Pos[1]
                        ]
                    )
                    
                    self.particles.add(PlaceParticle(
                        [tile_Pos[0] * TILE_SIZE + TILE_SIZE/2, tile_Pos[1] * TILE_SIZE + TILE_SIZE/2], 
                        self.particles
                    ))


    def left_click(self, tile_loc, tilePos):
        if self.current_layer not in self.layers.keys() or self.current_layer not in self.tilemap.tilemap.keys(): 
            return

        delete = False

        if tile_loc in self.layers[self.current_layer]:
            del self.layers[self.current_layer][tile_loc]

        if tile_loc in self.tilemap.tilemap[self.current_layer]:
            tile: Tile = self.tilemap.tilemap[self.current_layer][tile_loc]
            img = Tile.SPRITES[tile.type][tile.variant]
            delete: pygame.Surface = img 
            del self.tilemap.tilemap[self.current_layer][tile_loc]

        if delete:
            for x in range(0, delete.get_width(), 2):
                for y in range(0, delete.get_height(), 2):
                    if random.randint(0, 1) == 0:
                        self.particles.add(BreakParticle(
                            [tilePos[0] * TILE_SIZE + x - self.offset.x, tilePos[1] * TILE_SIZE + y - self.offset.y], 
                            delete.get_at((x, y)),
                            self.particles
                        ))


    def right_click(self, tile_loc, tilePos):
        if self.current_layer not in self.layers.keys():
            self.layers[self.current_layer] = {}
            
        self.layers[self.current_layer][tile_loc] = {
            "type" : self.asset_names[self.current_tilegroup],
            "variant" : self.current_tilevariant,
            "pos" : [
                tilePos[0],
                tilePos[1]
            ]
        }
        
        self.tilemap.add_tile(
            layer = self.current_layer,
            type = self.asset_names[self.current_tilegroup],
            variant = self.current_tilevariant,
            tile_loc = tile_loc,
            pos = [
                tilePos[0],
                tilePos[1]
            ]
        )

        self.particles.add(PlaceParticle(
            [tilePos[0] * TILE_SIZE + TILE_SIZE/2, tilePos[1] * TILE_SIZE + TILE_SIZE/2], 
            self.particles
        ))


        ##################################################################################

    def sidebar_update(self):
        #backdrop shadow
        shadow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shadow.fill((10, 10, 10))
        shadow.set_alpha(160)
        self.screen.blit(shadow, (0, 0))

        #resetting the sidebar itself
        self.sidebar = pygame.Surface((WIDTH/4, HEIGHT), pygame.SRCALPHA)
        self.sidebar.fill((68, 63, 86))

        current_tilegroup = self.asset_names[self.current_tilegroup]
        label_shadow = self.font.render(current_tilegroup.capitalize(), False, (40, 40, 40))
        label = self.font.render(current_tilegroup.capitalize(), False, (255, 255, 255))
        self.sidebar.blit(label_shadow, (13, label.get_height()+1))
        self.sidebar.blit(label, (12, label.get_height()))


        mousePos = pygame.mouse.get_pos()
        mouse = pygame.mouse.get_pressed()
        delta_l = delta_r = 0
        if self.left_button.get_rect(topleft=(WIDTH - (self.left_button.get_width() * 3) + 10, 7)).collidepoint(mousePos):
            delta_l = -1
            if mouse[0]:
                if self.left_right_button_pressed == False:
                    self.current_tilevariant = 0
                    self.sidebar_yscroll = 0
                    self.current_tilegroup -= 1
                    if self.current_tilegroup < 0:
                        self.current_tilegroup = len(self.asset_names) - 1
                    self.left_right_button_pressed = True
            else:
                self.left_right_button_pressed = False

        elif self.right_button.get_rect(topleft=(WIDTH - (self.left_button.get_width() * 2) + 15, 7)).collidepoint(mousePos):
            delta_r = -1
            if mouse[0]:
                if self.left_right_button_pressed == False:
                    self.current_tilevariant = 0
                    self.sidebar_yscroll = 0
                    self.current_tilegroup += 1
                    if self.current_tilegroup >= len(self.asset_names):
                        self.current_tilegroup = 0
                    self.left_right_button_pressed = True
            else:
                self.left_right_button_pressed = False

        assets = self.assets[current_tilegroup]
        for i, asset in enumerate(assets):

            asset = asset.copy()
            mask = pygame.mask.from_surface(asset)
            mask.invert()
            shadow = mask.to_surface()
            shadow.set_colorkey((255, 255, 255))
            mask.invert()

            x = (i % 4)  * TILE_SIZE + ((i%4)*5) + 8 
            y = (i // 4) * TILE_SIZE + ((i//4)*5) + 37

            if y + self.sidebar_yscroll < TILE_SIZE/2:
                continue
            elif TILE_SIZE / 2 < y + self.sidebar_yscroll < TILE_SIZE:
                dist = TILE_SIZE - (y + self.sidebar_yscroll)
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
            

        self.sidebar.blit(self.left_shadow, (WIDTH/4 - (self.left_button.get_width() * 3) + 11, 9 + delta_l))
        self.sidebar.blit(self.left_button, (WIDTH/4 - (self.left_button.get_width() * 3) + 10, 7 + delta_l))
        self.sidebar.blit(self.right_shadow, (WIDTH/4 - (self.left_button.get_width() * 2) + 9+5, 9 + delta_r))
        self.sidebar.blit(self.right_button, (WIDTH/4 - (self.left_button.get_width() * 2) + 10+5, 7 + delta_r))

        self.sidebar_pos = self.sidebar_pos.lerp(vec(WIDTH * 0.75, 0), 0.3)
        self.screen.blit(self.sidebar, self.sidebar_pos)

    def sidebar_reset(self):
        self.sidebar_pos = vec(WIDTH*1.5, 0)
        self.sidebar_yscroll = 0

        ##################################################################################

    def run(self):

        last_time = pygame.time.get_ticks()
        running = True
        while running:
            #deltatime
            self.dt = (current_time := pygame.time.get_ticks()) - last_time
            self.dt /= 1000
            last_time = current_time

            keys = pygame.key.get_pressed()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEWHEEL:
                    if not self.sidebar_open:
                        self.current_tilevariant -= event.y

                        if self.current_tilevariant >= len(self.assets[self.asset_names[self.current_tilegroup]]):
                            self.current_tilevariant = 0
                        elif self.current_tilevariant < 0:
                            self.current_tilevariant = len(self.assets[self.asset_names[self.current_tilegroup]]) - 1
                    else:
                        self.sidebar_yscroll = min(0, self.sidebar_yscroll + event.y * 8)

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False

                    if event.key == pygame.K_TAB:
                        if self.sidebar_open == False:
                            self.sidebar_reset()
                        self.sidebar_open = not self.sidebar_open

                    if event.key == pygame.K_ESCAPE:
                        if self.sidebar_open:
                            self.sidebar_open = False

                    if event.key == pygame.K_COMMA:
                        self.current_layer -= 1
                        if self.current_layer < 0:
                            self.current_layer = 0
                    if event.key == pygame.K_PERIOD:
                        self.current_layer += 1

                    if event.key == pygame.K_s and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                        self.tilemap.save()
                    if event.key == pygame.K_o and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                        self.tilemap.load()
                    if event.key == pygame.K_t and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                        self.tilemap.auto_tile()
                    
            self.calculate_offset()
            self.screen.fill((30, 30, 30))

            for layer in sorted(self.tilemap.tilemap.keys()):
                for tile in self.tilemap.tilemap[layer].keys():
                    self.tilemap.tilemap[layer][tile].update(dim=layer != self.current_layer)
            self.particles.update(self.screen)

            #axes
            pygame.draw.line(self.screen, (255, 255, 255), (-self.offset.x, 0), (-self.offset.x, HEIGHT), 1)
            pygame.draw.line(self.screen, (255, 255, 255), (0, HEIGHT - self.offset.y - 8), (WIDTH, HEIGHT - self.offset.y - 8), 1)

            #lil transparent render of current object in top left corner
            current_tile_img = self.assets[self.asset_names[self.current_tilegroup]][self.current_tilevariant].copy()
            current_tile_img.set_alpha(100)
            self.screen.blit(current_tile_img, (16, 16))

            #mouse handling
            if not self.sidebar_open:
                self.mouse_stuff(current_tile_img)


            offset_surf = self.font.render(f"{[int(self.offset.x), int(self.offset.y + 8)]}", False, (255, 255, 255))
            self.screen.blit(offset_surf, (5, HEIGHT-15))

            if keys[pygame.K_h]:
                labels = [
                    "RSHIFT + Click: Flood Fill/Place",
                    "CTRL + O: Load File",
                    "CTRL + S: Save File",
                    "CTRL + T: Auto Tile",
                    "<> : Change Layer",
                    "G: Toggle Grid",
                    "WASD: Move",
                    "LMB: Break",
                    "RMB: Place",
                    "MMB: Pick",
                ]
                for i, text in enumerate(labels):
                    label = self.font.render(text, False, (255, 255, 255))
                    self.screen.blit(label, label.get_rect(right=WIDTH-5, y = HEIGHT-15-(10*i)))
            else:
                label = self.font.render("Press H for Shortcuts", False, (255, 255, 255))
                self.screen.blit(label, label.get_rect(right=WIDTH-5, y = HEIGHT-15))

            layer_label = self.font.render(f"{'Layer: '  + str(self.current_layer):>10}", False, (255, 255, 255))
            self.screen.blit(layer_label, layer_label.get_rect(right=WIDTH-5, y=5))


            if self.sidebar_open:
                self.sidebar_update()



            pygame.display.update()
            self.clock.tick(FPS)

    ##############################################################################################

if __name__ == "__main__":
    editor = Editor()
    editor.run()
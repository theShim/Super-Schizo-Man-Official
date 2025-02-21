import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import os
# import cv2
import numpy as np
import random
import math

from scripts.config.SETTINGS import WIDTH, HEIGHT, Z_LAYERS, FRIC, GRAV, CONTROLS, DEBUG, FPS
from scripts.utils.CORE_FUNCS import vec, lerp, add_loaded_sprite_number
from scripts.utils.sprite_animator import SpriteAnimator

    ##############################################################################################

class Player(pygame.sprite.Sprite):

    @classmethod
    def cache_sprites(cls):
        Player.SPRITES = {}
        scales = {1 : 2, 2: 1}
        for char_num in os.listdir('assets/entities/players'):
            path = 'assets/entities/players/' + str(char_num)
            Player.SPRITES[int(char_num)] = {}

            for anim in os.listdir(path):
                imgs = []
                for move_name in os.listdir(f"{path}/{anim}"):
                    img = pygame.image.load(f"{path}/{anim}/{move_name}").convert_alpha()
                    # img = pygame.Surface(base.get_size())

                    # #solid outline
                    # for y in range(img.height):
                    #     for x in range(img.width):
                    #         if base.get_at((x, y)) == (0, 0, 0, 0):
                    #             for offset in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    #                 x1 = sorted([0, base.width-1, x + offset[0]])[1]
                    #                 y1 = sorted([0, base.height-1, y + offset[1]])[1]
                    #                 if base.get_at((x1, y1)) != (0, 0, 0, 0):
                    #                     img.set_at((x, y), (1, 0, 0))
                    #                     break
                    #         else:
                    #             img.set_at((x, y), base.get_at((x, y)))

                    img = pygame.transform.scale(img, pygame.math.Vector2(img.get_size())*scales[int(char_num)])

                    #mask outline
                    # copy = img.copy()
                    # pygame.draw.polygon(img, (1, 0, 0, 192), pygame.mask.from_surface(img).outline(), 2)
                    # img.blit(copy, (0, 0))

                    img.set_colorkey((0, 0, 0))
                    imgs.append(img)
                add_loaded_sprite_number(len(imgs))
                animator = SpriteAnimator(imgs, animation_speed=0.2)
                Player.SPRITES[int(char_num)][anim.lower()] = animator

    def __init__(self, game, groups, char_num=1, spawn_pos=(WIDTH/2, -HEIGHT/2)):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen

        self.sprites: dict = Player.SPRITES[char_num]
        self.status = "idle"
        self.z = Z_LAYERS["player"]

        image: pygame.Surface = self.sprites[self.status].get_sprite() #current sprite
        self.spawn_pos = spawn_pos #depends on where the spawning tile is
        self.rect = image.get_rect(topleft=spawn_pos) #rect for movement and stuff
        self.size = image.get_size()
        self.direction = 'left' #which way the player is facing
        self.hitbox_size = vec(image.get_size()) #actual hitbox

        self.vel = vec() #x and y velocity
        self.acc = vec(0, GRAV)
        self.run_speed = 40 #scalar
        self.jump_vel = 10
        self.jumps = 2 #total number of jumps left
        self.jumpHeld = False #ensures player only jumps once

        self.landed = False #checks if the player is currently on the floor
        self.in_water = False
        self.in_water_duration = 0 #how long theyve been in water
        self.water_glow_timer = 5

        self.squish = 0
        self.squish_vel = 0

    #actual colliding rect
    @property
    def hitbox(self):
        return pygame.Rect(self.rect.centerx - self.hitbox_size.x / 2, self.rect.y, self.hitbox_size.x, self.hitbox_size.y)
    
    @property
    def image(self):
        spr = self.current_sprite.get_sprite()
        if self.direction == 'left':
            spr = pygame.transform.flip(spr, True, False)
            spr.set_colorkey((0, 0, 0))
        return spr

    @property
    def current_sprite(self) -> SpriteAnimator:
        return self.sprites.get(self.status, self.sprites["idle"])
        
        ###################################################################################### 

    #handles x-directional movements, changing their acceleration
    def horizontal_move(self, keys):
        old = self.direction
        if keys[CONTROLS["left"]]:
            self.acc.x = -1 * self.run_speed
            self.direction = 'left'
        if keys[CONTROLS["right"]]:
            self.acc.x = 1 * self.run_speed
            self.direction = 'right'

        #if the player is on the floor and changes directions, add some run particles
        # if self.landed:
        #     if self.direction != old:
        #         for i in range(random.randint(1, 3)):
        #             particle_manager.add_particle("background", "run", pos=self.hitbox.midbottom, facing=self.direction)

        #change the current animation depending on if the player is moving/holding the buttons
        if not (keys[CONTROLS['left']] or keys[CONTROLS['right']]):
            self.change_status('idle')
        else:
            self.change_status('run')

    #handles jump inputs
    def jump(self, keys):
        if keys[CONTROLS["jump"]] or keys[CONTROLS['up']]:
            if self.jumps > 0 and self.jumpHeld == False:
                self.vel.y = -self.jump_vel
                self.jumps -= 1 #lower the remaining jumps for double jump capability
                self.jumpHeld = True
        else:
            if self.vel.y < 0:
                self.vel.y = lerp(0, self.vel.y , 0.1) #allows for short hops and high jumps by interpolation
            self.jumpHeld = False

        #change the current animation depending on if the player is moving up or down
        if self.vel.y > 0:
            self.change_status('fall')
        elif self.vel.y < 0:
            self.change_status('jump')

    #accelerating and moving the player
    def apply_forces(self):
        self.vel.x += self.acc.x * self.game.dt #horizontal acceleration
        self.vel.y += self.acc.y * self.game.dt #vertical acceleration (gravity and jumping)

        self.vel.x *= FRIC #applying friction
        if -0.5 < self.vel.x < 0.5: #bounds to prevent sliding bug
            self.vel.x = 0

        self.rect.topleft += self.vel# * self.game.dt #actually applying the velocity

        if self.rect.bottom > HEIGHT*3: #failsafe if they fall into the void, prolly tie this into the stage later
            self.rect.topleft = self.spawn_pos
            self.vel.y = 0

    def move(self, keys):
        self.acc = vec(0, GRAV)

        self.horizontal_move(keys)
        self.jump(keys)
        # self.special_moves(keys)
        self.apply_forces()
            
        ###################################################################################### 

    def collisions(self):
        collision_tolerance = 10
        for rect in self.game.state_loader.tilemap.nearby_physics_rects(self.hitbox.center):
            # pygame.draw.rect(self.screen, (255, 0 ,0), [rect.x - self.game.offset.x, rect.y - self.game.offset.y, *rect.size], 1)
            if self.hitbox.colliderect(rect):
                
                #if the player lands
                if abs(self.hitbox.bottom - rect.top) < collision_tolerance + 10 and self.vel.y > 0:
                    # if self.landed == False:
                    #     # for i in range(max(2, int(self.vel.y/3))): #add landing particles
                    #     #     c = random.uniform(150, 200)
                    #     #     particle_manager.add_particle(
                    #     #         "background", 
                    #     #         "land", 
                    #     #         pos=self.hitbox.midbottom, 
                    #     #         scale=min(7, int(self.vel.y/2)), 
                    #     #         colour=(c, c, c)
                    #     #     )

                    if self.landed == False:
                        self.landed = True
                        if self.vel.y > 8:
                            self.squish = self.vel.y * 0.75

                    self.vel.y = 0 #reset y velocity
                    self.rect.bottom = rect.top + 1
                    self.jumps = 2 #reset jumps
                    break
                
                #ceiling
                if abs(self.hitbox.top - rect.bottom) < collision_tolerance and self.vel.y < 0:
                    self.rect.top = rect.bottom 
                    self.vel.y = 0
                
                #walls
                if abs(self.hitbox.right - rect.left) < collision_tolerance and self.vel.x > 0:
                    self.rect.right = rect.left
                    self.vel.x = 0
                if abs(self.hitbox.left - rect.right) < collision_tolerance and self.vel.x < 0:
                    self.rect.left =  rect.right
                    self.vel.x = 0
        else:
            #if the player hasn't collided with the floor then they're midair
            self.landed = False

    def offgrid_collisions(self):
        for tile in self.game.state_loader.tilemap.offgrid_render():
            if tile.type == "bridge":
                # if tile.touching:
                #     if self.status in ['fall']:
                #         self.change_status('idle')

                for j in tile.joints:
                    if tile.player_collisions(j, self): 
                        break
            
        ###################################################################################### 

    #changing the animation
    def change_status(self, status):
        if status != self.status:
            self.current_sprite.reset_frame()
            self.status = status

    #updating the current animation sprite
    def animate(self):
        self.current_sprite.next(self.game.dt)
            
        ###################################################################################### 

    def update(self):
        keys = pygame.key.get_pressed()
        self.move(keys)
        self.collisions()
        self.offgrid_collisions()

        self.animate()
        self.draw()

        if self.in_water:
            if self.in_water_duration <= 100:
                self.in_water_duration += self.water_glow_timer
        elif self.in_water == False:
            if self.in_water_duration:
                self.in_water_duration -= self.water_glow_timer
        self.in_water = False

    def get_image(self):
        spr = self.image

        if self.squish > 0:
            if self.squish < 0.01: 
                self.squish = 0

            self.squish_vel += (tension := 0.01) * (-self.squish) - self.squish_vel * (dampening := 0.1)
            self.squish += self.squish_vel

            spr = pygame.transform.scale(spr, (spr.width + self.squish / 2, spr.height - self.squish))
        
        return spr

    def draw(self):
        spr = self.get_image() #get sprite and flip if needed

        rect = spr.get_rect(midbottom=self.hitbox.midbottom - self.game.offset)
        self.screen.blit(spr, rect)

        glow_size = 96 if not self.in_water_duration else lerp(60, 96, min(100, self.in_water_duration) / 100)
        self.game.state_loader.current_state.light_manager.add_glow(self.hitbox.center, glow_size, (255, 255, 255))

        # if DEBUG: #hitbox
        #     pygame.draw.rect(self.screen, (200, 0, 0), [self.hitbox.x - self.game.offset.x, self.hitbox.y - self.game.offset.y, *self.hitbox.size], 1)
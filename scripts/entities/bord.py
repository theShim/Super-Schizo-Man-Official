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
from scripts.utils.CORE_FUNCS import vec, lerp, add_loaded_sprite_number, Timer
from scripts.utils.sprite_animator import SpriteAnimator

    ##############################################################################################

class Bord(pygame.sprite.Sprite):

    @classmethod
    def cache_sprites(cls):
        cls.SPRITES = {}
        for char_num in os.listdir('assets/entities/bord'):
            path = 'assets/entities/bord/' + str(char_num)
            cls.SPRITES[int(char_num)] = {}

            for anim in os.listdir(path):
                imgs = []
                for move_name in os.listdir(f"{path}/{anim}"):
                    img = pygame.image.load(f"{path}/{anim}/{move_name}").convert_alpha()
                    img.set_colorkey((0, 0, 0))
                    imgs.append(img)

                add_loaded_sprite_number(len(imgs))
                animator = SpriteAnimator(imgs, animation_speed=0.05  if anim.lower() != "eat" else 0.2, loop=False if anim.lower() == "eat" else True)
                cls.SPRITES[int(char_num)][anim.lower()] = animator

    def __init__(self, game, groups, pos, char_num = 1):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen
        self.z = Z_LAYERS["entities"]

        self.sprites: dict = Bord.SPRITES[char_num].copy()
        self.status = "idle"

        image: pygame.Surface = self.sprites[self.status].get_sprite() #current sprite
        self.spawn_pos = pos #depends on where the spawning tile is
        self.rect = image.get_frect(topleft=pos) #rect for movement and stuff
        self.size = image.get_size()
        self.direction = random.choice(['left', 'right']) #which way the player is facing
        self.hitbox_size = vec(image.get_size()) #actual hitbox size

        self.vel = vec() #x and y velocity
        self.acc = vec(0, GRAV)
        self.touched = False
        self.touch_x = 12
        self.midtouch_flag = None
        self.move_timer = Timer(FPS * (random.randint(4, 8) / 2), 1)
        self.landed = False

        self.eat_timer = Timer(FPS * random.randint(3, 5), 1)

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

    def move(self):
        self.acc = vec(0, GRAV / 2)

        if self.game.player.hitbox.colliderect(self.hitbox):
            self.touched = True

        if not self.touched:
            if self.status != "eat":
                self.move_timer.update()
                if self.move_timer.finished:
                    if self.landed:
                        self.move_timer.reset()
                        self.move_timer.change_speed(random.uniform(0.7, 2))

                        max_dist = 50
                        if not self.game.state_loader.current_state.tilemap.enemy_tile_infront_to_walk(self.hitbox.center, self.direction, max_dist):
                            self.direction = "left" if self.direction == "right" else "right"

                        self.vel.x = random.uniform(1.2, 2.2) * (-1 if self.direction == "left" else 1)
                        self.vel.y = -random.uniform(1.2, 2.2)
        else:
            self.change_status("flying")

            if random.randint(1, 20) == 1:
                self.game.state_loader.current_state.particle_manager.add_particle(
                    "bord particle", 
                    pos=self.image.get_rect(midbottom=self.hitbox.midbottom).center + vec(random.uniform(-5, 5), random.uniform(-5, 5)),
                    vel=self.vel.clamp_magnitude(10),
                    col=random.choice([(17+200, 158+80, 214+40), (71+180, 170+80, 209+40)])
                )

            #add code here
            if self.direction == 'left':
                self.acc.x = -random.uniform(1.0, 1.25) * 2
            else:
                self.acc.x = random.uniform(1.0, 1.25) * 2

            self.acc.y = -random.uniform(1, 1.5) * 2  # Strong upward movement

            # Add a wobble effect by slightly dipping the bird downwards at a random point in its flight
            if random.randint(1, 20) == 1:  # Occurs randomly to simulate the wobble
                self.vel.y += 4 * random.uniform(0.1, 0.2)  # Slight dip
                self.vel.x *= 0.8

        if self.rect.bottom - self.game.offset.y < -50:
            return self.kill()

        self.apply_forces()

    #accelerating and moving the player
    def apply_forces(self):
        self.vel.x += self.acc.x * self.game.dt #horizontal acceleration
        self.vel.y += self.acc.y * self.game.dt #vertical acceleration (gravity and jumping)

        #change the current animation depending on if the player is moving up or down
        if not self.touched and self.status != "eat":
            if self.vel.y > 0:
                self.change_status('flying')
            elif self.vel.y < 0:
                self.change_status('flying')

        if self.landed and (not self.touched):
            self.vel.x *= FRIC #applying friction
            if -0.5 < self.vel.x < 0.5: #bounds to prevent sliding bug
                self.vel.x = 0

        self.rect.topleft += self.vel# * self.game.dt #actually applying the velocity

        if self.rect.bottom > HEIGHT*3: #failsafe if they fall into the void, prolly tie this into the stage later
            self.rect.topleft = self.spawn_pos
            self.vel.y = 0
            
        ###################################################################################### 

    def collisions(self):
        collision_tolerance = 10
        for rect in self.game.state_loader.tilemap.nearby_physics_rects(self.hitbox.center):
            # pygame.draw.rect(self.screen, (255, 0 ,0), [rect.x - self.game.offset.x, rect.y - self.game.offset.y, *rect.size], 1)
            if self.hitbox.colliderect(rect):
                
                #if the player lands
                if abs(self.hitbox.bottom - rect.top) < collision_tolerance and self.vel.y > 0:
                    self.vel.y = 0 #reset y velocity
                    self.rect.bottom = rect.top + 1
                    if self.status != "eat":
                        self.change_status("idle")
                    self.landed = True
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
        
        ###################################################################################### 

    #changing the animation
    def change_status(self, status):
        if status != self.status:
            # self.current_sprite.reset_frame()
            self.status = status

    #updating the current animation sprite
    def animate(self):
        self.current_sprite.next(self.game.dt)

        if self.status == "eat":
            if self.current_sprite.finished:
                self.change_status("idle")
        
        ###################################################################################### 

    def update(self):
        self.move()
        self.collisions()

        if self.landed and not self.touched:
            self.eat_timer.update()
            if self.eat_timer.finished:
                self.change_status("eat")
                self.current_sprite.reset_frame()
                self.eat_timer.reset()

        # if self.status != "eat":
        #     self.change_status("eat")

        # if self.touched:
        #     self.game.state_loader.current_state.particle_manager.add_particle(
        #         "bord after image", 
        #         image=self.image, 
        #         pos=self.image.get_rect(midbottom=self.hitbox.midbottom).topleft
        #     )

        self.animate()
        self.draw()

    def draw(self):
        spr = self.image #get sprite and flip if needed

        rect = spr.get_rect(midbottom=self.hitbox.midbottom - self.game.offset)
        self.screen.blit(spr, rect)
        
        self.game.state_loader.current_state.light_manager.add_glow(self.hitbox.midbottom - vec(0, 4), 32, (200, 200, 200))
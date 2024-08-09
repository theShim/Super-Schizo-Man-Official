import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *
    
import random
import sys
import math
import time
import numpy as np

    ##############################################################################################

#initialising pygame stuff
pygame.init()  #general pygame
pygame.font.init() #font stuff
pygame.mixer.pre_init(44100, 16, 2, 4096) #music stuff
pygame.mixer.init()
pygame.event.set_blocked(None) #setting allowed events to reduce lag
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP])
pygame.display.set_caption("")

#initalising pygame window
flags = pygame.DOUBLEBUF | pygame.SCALED#| pygame.FULLSCREEN
SIZE = WIDTH, HEIGHT = (600, 600)
screen = pygame.display.set_mode(SIZE, flags)
clock = pygame.time.Clock()

#renaming common functions
vec = pygame.math.Vector2

#useful functions
def gen_colour():
    return (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))

def euclidean_distance(point1, point2):
    return vec(point1).distance_to(vec(point2))

def rotate(origin, point, angle):
    ox, oy = origin
    px, py = point
    angle = math.radians(angle)

    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return vec(qx, qy)

    ##############################################################################################

class Grid(pygame.sprite.Sprite):
    def __init__(self, n=1):
        self.grid = np.random.randint(0, 2, (HEIGHT, WIDTH))
        self.flag = True
        self.offsets = [(i, j) for i in range(-1, 2) for j in range(-1, 2) if not (i == j == 0)]
        self.scalar = n

    def mouse(self):
        mouse = pygame.mouse.get_pressed()
        if mouse[0]:
            self.flag = False
            mousePos = pygame.mouse.get_pos()
            self.grid[mousePos[0], mousePos[1]] = 1
        else:
            self.flag = True

    def update(self):
        self.mouse()
        for i in range(self.scalar):
            self.draw()

    def draw(self):
        # Create a padded grid to handle edge cases
        padded_grid = np.pad(self.grid, pad_width=1, mode='constant', constant_values=0)
        
        # Calculate neighbours
        neighbours = (
            padded_grid[ :-2,  :-2] + padded_grid[ :-2, 1:-1] + padded_grid[ :-2, 2:  ] +
            padded_grid[1:-1,  :-2] +                         padded_grid[1:-1, 2:  ] +
            padded_grid[2:  ,  :-2] + padded_grid[2:  , 1:-1] + padded_grid[2:  , 2:  ]
        )
        
        if self.flag:
            self.grid = np.where((self.grid == 1) & ((neighbours == 2) | (neighbours == 3)), 1, 0) | (self.grid == 0) & ((neighbours == 3) | (neighbours == 6))

        # Update the display
        pixel_array = np.stack((self.grid, self.grid, self.grid), axis=-1) * 255
        pygame.surfarray.blit_array(screen, pixel_array)

g = Grid()


    ##############################################################################################

last_time = time.time()

running = True
while running:

    dt = time.time() - last_time
    last_time = time.time()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False

    screen.fill((30, 30, 30))
    g.update()

    #fps
    pygame.display.set_caption(f'FPS: {int(clock.get_fps())}')

    pygame.display.update()
    clock.tick(60)

pygame.quit()
sys.exit()
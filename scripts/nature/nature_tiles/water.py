import contextlib
with contextlib.redirect_stdout(None):
    import pygame; pygame.init()
    from pygame.locals import *
    
import math
import random
import os
import numpy as np
from scipy.interpolate import interp1d

from scripts.config.SETTINGS import TILE_SIZE, Z_LAYERS, SIZE
from scripts.utils.CORE_FUNCS import vec, euclidean_distance

    ##############################################################################################

def get_curve(points, interval=1):
    x_new = np.arange(points[0].x, points[-1].x, interval)
    x = np.array([i.x for i in points])
    y = np.array([i.y for i in points])
    f = interp1d(x, y, kind='cubic', fill_value='extrapolate')
    y_new = f(x_new)
    x1 = list(x_new)
    y1 = list(y_new)
    points = [vec(x1[i], y1[i]) for i in range(len(x1))]
    return points, (minmax:=[min(x1), max(x1), min(y1), max(y1)])

    ##############################################################################################

class Water_Spring(pygame.sprite.Sprite):
    def __init__(self, pos, target_height=None):
        super().__init__()
        self.pos: vec = pos
        self.radius = 2
        self.target_height = target_height if target_height else self.pos + vec(0, TILE_SIZE//8)

        self.dampening = 0.05 * 2
        self.tension = 0.01
        self.vel = 0
        self.held = False
        self.pinned = False

    def move(self, flag):
        if self.pinned:
            return 
        
        dh = self.target_height - self.pos.y
        self.vel += self.tension * dh - self.vel * self.dampening
        self.pos.y += self.vel
        
        dh = self.target_height - self.pos.y
        if abs(dh) < 0.05:
            self.pos.y = self.target_height
        else:
            flag[0] = True

    def update(self, flag:list[bool]):
        self.move(flag)

    def draw(self, screen, offset):
        start, end = int(min(self.pos.y, self.target_height)), int(max(self.pos.y, self.target_height))
        for y in range(start, end, 20):
            pygame.draw.circle(screen, (255, 255, 255), vec(self.pos.x, y) - offset, self.radius/8)

        pygame.draw.circle(screen, (255, 255, 255), self.pos - offset, self.radius)

    ##############################################################################################

class Water(pygame.sprite.Sprite):
    def __init__(self, game, pos, size, variant):
        super().__init__()
        self.game = game
        self.screen = self.game.screen
        self.z = Z_LAYERS["midground offgrid"]

        self.pos = vec(pos) * TILE_SIZE
        self.variant = variant
        self.size = vec(size) * TILE_SIZE
        self.rect = pygame.Rect(self.pos.x, self.pos.y, self.size.x, self.size.y)
        
        self.col = [(0, 104, 191, 64), ][variant]
        self.moving = False
        self.idle = pygame.Surface((self.size.x, self.size.y - TILE_SIZE//8), pygame.SRCALPHA)
        self.idle.fill(self.col)

        for y in range(96):
            alpha = int(64 + 96 - y)  #adjust alpha based on depth
            pygame.draw.line(self.idle, (0, 104, 191, alpha), (0, self.idle.get_height()-y), (self.idle.get_width(), self.idle.get_height()-y))

        self.idle.set_alpha(192)
        pygame.draw.line(self.idle, (255, 255, 255), (0,0), (self.size.x, 0))

        self.springs = pygame.sprite.Group()
        self.spacing = TILE_SIZE/2
        for i in range(int(self.pos.x), int(self.pos.x + self.size.x)+int(self.spacing), int(self.spacing)):
            self.springs.add(Water_Spring(vec(i, self.pos.y), self.pos.y))
        self.springs.sprites()[0].pinned = True
        self.springs.sprites()[-1].pinned = True

    ##############################################################################################

    def spread_wave(self):
        spread = 0.02
        for i in range(1, len(self.springs) - 1):
            springs = self.springs.sprites().copy()
            springs[i - 1].vel += spread * (springs[i].pos.y - springs[i - 1].pos.y)
            springs[i + 1].vel += spread * (springs[i].pos.y - springs[i + 1].pos.y)


    def player_collision(self, player):
        # if player.vel.y <= 0:
        #     return
        
        for spring in self.springs.sprites():
            if spring.pinned: continue
            if player.hitbox.collidepoint(spring.pos):
                spring.pos.y += min(10, 1.2 ** player.vel.y)

        if self.rect.colliderect(player.hitbox):
            if player.vel.y > 0:
                player.vel.y *= 0.84
            player.in_water = True

    ##############################################################################################

    def update(self):
        self.spread_wave()
        flag = [False]
        self.springs.update(flag)
        
        if flag[0]:
            self.moving = True
        else:
            self.moving = False

        self.draw()


    def draw(self):
        if self.moving:
            springs = self.springs.sprites().copy()
            points, minmax = get_curve(list(map(lambda s: s.pos, springs)))

            buffer_width = minmax[1] - minmax[0]
            buffer_height = minmax[3] - minmax[2]
            if buffer_height < 0.01: buffer_height = 0
            surf = pygame.Surface((buffer_width + self.size[0], buffer_height + self.size[1]), pygame.SRCALPHA)
            pygame.draw.polygon(
                surf,
                self.col,
                [
                    vec(self.pos[0]-minmax[0], self.pos[1]-minmax[2]+self.size[1]-TILE_SIZE//8), 
                    *(points2 := list(map(lambda p:p-vec(minmax[0], minmax[2]), points))), 
                    vec(self.pos[0]-minmax[0]+self.size[0], self.pos[1]-minmax[2]+self.size[1]-TILE_SIZE//8)
                ]
            )

            for y in range(96):
                alpha = min(255, int(64 + 96 - y))  #adjust alpha based on depth
                pygame.draw.line(surf, (0, 104, 191, alpha), (0, surf.get_height()-y), (self.size.x, surf.get_height()-y))
            surf.set_alpha(192)

            pygame.draw.lines(surf, (255, 255, 255), False, points2)
            self.screen.blit(surf, self.pos - self.game.offset + vec(0, TILE_SIZE//8))

            # for i in range(1, len(points)):
            #     pygame.draw.lines(screen, (255, 255, 255), points[i-1] - offset + vec(0, TILE_SIZE//8), points[i] - offset + vec(0, TILE_SIZE//8))
        else:
            self.screen.blit(self.idle, self.pos - self.game.offset + vec(0, TILE_SIZE//8))

    ##############################################################################################

class Water_Handler:

    @staticmethod
    def segment_water(water_tiles):
        groups = []
        visited = set()
        for pos in water_tiles:
            if pos not in visited:
                group = []
                Water_Handler.dfs(pos, water_tiles, visited, group)
                groups.append(group)
        return groups

    @staticmethod
    def get_adjacent_tiles(pos, tiles):
        x, y = pos
        adjacent_tiles = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if (dx != dy) and (x + dx, y + dy) in tiles:
                    adjacent_tiles.append((x + dx, y + dy))
        return adjacent_tiles

    @staticmethod    
    def dfs(start_pos, tiles, visited: set, group: list):
        visited.add(start_pos)
        group.append([start_pos, tiles[start_pos]])
        adjacent_tiles = Water_Handler.get_adjacent_tiles(start_pos, tiles)
        for tile in adjacent_tiles:
            if tile not in visited:
                Water_Handler.dfs(tile, tiles, visited, group)
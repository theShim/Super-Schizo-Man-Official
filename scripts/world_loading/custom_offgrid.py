import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import random
import numpy as np
import math

from scripts.world_loading.tiles import Offgrid_Tile

from scripts.utils.CORE_FUNCS import vec
from scripts.config.SETTINGS import WIDTH, HEIGHT, FPS, Z_LAYERS

    ##############################################################################################

class Torch(Offgrid_Tile):
    def __init__(self, game, variant, pos):
        super().__init__(game, "torch", variant, pos)
        self.z = Z_LAYERS["foreground offgrid"]

        self.SPRITES = Offgrid_Tile.SPRITES["torch"]

        self.flame_intensity = 24
        self.start = True

    def update(self):
        img = self.SPRITES[self.variant]
        self.screen.blit(img, self.pos - self.game.offset)

        if self.start:
            for i in range(self.flame_intensity):
                self.game.state_loader.current_state.particle_manager.add_particle("fire", pos=(self.pos + vec(random.uniform(-5, 5) + 12, random.uniform(-5, 5) - 2)), radius=random.uniform(1, 3))
            self.start = False

    ##############################################################################################

class Bridge(Offgrid_Tile):
    def __init__(self, game, variant, pos, *kwargs):
        super().__init__(game, "bridge", variant, pos, *kwargs)
        self.z = Z_LAYERS["foreground offgrid"]
        self.end_pos = self.end_pos

        self.points = np.linspace(self.pos, self.end_pos, 12) + vec(Offgrid_Tile.SPRITES[self.type][self.variant].size) / 2
        self.old_points = self.points.copy()
        self.pinned = [0, len(self.points)-1]
        self.touching = False

        self.joints = [(i, i+1) for i in range(len(self.points)-1)]
        self.tension = 0.8
        self.lengths = []
        for j in self.joints:
            p1 = self.points[j[0]].tolist()
            p2 = self.points[j[1]].tolist()
            length = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2) * self.tension
            self.lengths.append(length)

    def move(self):
        temp = self.points.copy()

        delta = (self.points - self.old_points)
        delta[:, 1] += 0.9 / 4
        immovable_mask = np.zeros_like(self.points, dtype=bool)
        immovable_mask[self.pinned] = True
        delta[immovable_mask] = 0

        self.points += delta
        self.old_points = temp

    def constrain(self):
        for joint, length in zip(self.joints, self.lengths):
            p1, p2 = self.points[joint[0]], self.points[joint[1]]
            diff = p1 - p2
            dist = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

            try:
                update = 0.5 * diff * (length - dist) / dist
                update[np.isnan(update)] = 0  
            except ZeroDivisionError:
                update = np.zeros_like(diff)

            if not (joint[0] in self.pinned or joint[1] in self.pinned):
                self.points[joint[0]] += update
                self.points[joint[1]] -= update
            elif joint[0] not in self.pinned and joint[1] in self.pinned:
                self.points[joint[0]] += 2 * update
            elif joint[0] in self.pinned and joint[1] not in self.pinned:
                self.points[joint[1]] -= 2 * update

    def player_collisions(self, joint, player):
        p1 = vec(self.points[joint[0]].tolist())
        p2 = vec(self.points[joint[1]].tolist())
        rect: pygame.Rect = player.hitbox

        if pygame.Rect(p1.x, p1.y, p2.x - p1.x, p2.y - p1.y).colliderect(rect):
            v = p2 - p1
            t = (rect.midbottom[0] - p1.x) / (p2.x - p1.x)
            y = (p1 + (v * t)).y
            player.rect.bottom = y# (p1.y + p2.y) / 2

            player.vel.y = 0 #reset y velocity
            player.jumps = 2 #reset jumps
            player.landed = True
            self.touching = True
            self.points[joint[0]] += 1 if self.points[joint[0]] not in self.points[self.pinned] else 0 
            self.points[joint[1]] += 1 if self.points[joint[1]] not in self.points[self.pinned] else 0  
            return True
        
        self.touching = False
        return False

    def update(self):
        self.move()
        self.constrain()

        self.draw()

    def draw_segment(self, screen, offset, a, b):
        a = vec(a)
        b = vec(b)
        p1 = a.lerp(b, 0.1)
        p2 = b.lerp(a, 0.1)

        delta_y = p2[1] - p1[1]
        delta_x = p2[0] - p1[0]
        angle = math.atan2(delta_y, delta_x)

        cos = math.cos
        sin = math.sin
        points = [
            p1 + vec(cos(angle-90), sin(angle-90)) * 5 - offset,
            p1 + vec(cos(angle+90), sin(angle+90)) * 5 - offset,
            p2 + vec(cos(angle+90), sin(angle+90)) * 5 - offset,
            p2 + vec(cos(angle-90), sin(angle-90)) * 5 - offset,
        ]
        pygame.draw.polygon(screen, (64, 25, 24), points)

        points = [
            p1 + vec(cos(angle-90), sin(angle-90)) * 5 - offset,
            p1 + vec(cos(angle-90), sin(angle-90)) * 3 - offset,
            p2 + vec(cos(angle-90), sin(angle-90)) * 3 - offset,
            p2 + vec(cos(angle-90), sin(angle-90)) * 5 - offset,
        ]
        pygame.draw.polygon(screen, (143, 101, 83), points)

    def draw(self):
        img = Offgrid_Tile.SPRITES[self.type][self.variant]
        # pygame.draw.line(self.screen, (255, 255, 255), self.pos - self.game.offset + vec(img.size) / 2, self.end_pos- self.game.offset + vec(img.size) / 2, 2)

        # for point in self.points:
        #     pygame.draw.circle(self.screen, (255, 255, 255), point - self.game.offset, 5)
        # points = self.points - self.game.offset
        # pygame.draw.lines(self.screen, (255, 255, 255), False, points, 2)

        pygame.draw.rect(
            self.screen, 
            (135, 97, 62),
            [self.pos[0] - self.game.offset.x, self.pos[1]-35 - self.game.offset.y, 5, 35]
        )
        pygame.draw.rect(
            self.screen, 
            (135, 97, 62),
            [self.end_pos[0] - self.game.offset.x + img.width / 2, self.end_pos[1]-35 - self.game.offset.y, 5, 35]
        )

        for i, j in enumerate(self.joints):
            p1 = self.points[j[0]].tolist()
            p2 = self.points[j[1]].tolist()
            pygame.draw.line(self.screen, (95, 58, 48), vec(p1) - self.game.offset - vec(0, 2), vec(p2) - self.game.offset - vec(0, 2), 1)
            pygame.draw.line(self.screen, (95, 58, 48), vec(p1) - self.game.offset + vec(0, 2), vec(p2) - self.game.offset + vec(0, 2), 1)

            if i%2 == 1:
                p = vec(p1)
                pygame.draw.line(self.screen, (172, 125, 81), (p.lerp(vec(p2), 0.5)) - self.game.offset, p - self.game.offset - vec(0, 30), 3)
                pygame.draw.line(self.screen, (172, 125, 81), (p.lerp(vec(self.points[self.joints[i-1][0]].tolist()), 0.5)) - self.game.offset, p - self.game.offset - vec(0, 30), 3)

            #planks
            if i == len(self.joints)-1:
                self.draw_segment(self.screen, self.game.offset, p1, p2)
            if i:
                self.draw_segment(self.screen, self.game.offset, vec(self.points[self.joints[i-1][0]].tolist()), p1)

            pygame.draw.line(self.screen, (107, 61, 41), vec(p1) - self.game.offset - vec(0, 30), vec(p2) - self.game.offset - vec(0, 30), 2)

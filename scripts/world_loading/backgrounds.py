import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import random
import math

from scripts.config.SETTINGS import WIDTH, HEIGHT, SIZE
from scripts.utils.CORE_FUNCS import vec

    ############################################################################################## 

class Editor_Background:
    def __init__(self, game):
        self.game = game
        self.screen = self.game.screen

        self.line_width = 40
        self.line_speed = 1
        self.lines = [
            [[0, HEIGHT - (i*self.line_width)], [WIDTH, HEIGHT - self.line_width * 4 - (i*self.line_width)]]
            for i in range(-6, 9, 2)
        ]

    def update(self):
        #diagonal lines scrolling up
        for l in self.lines:
            p1 = l[0]
            p2 = l[1]
            pygame.draw.line(self.screen, (20, 20, 20), p1, p2, self.line_width)

            p1[1] -= self.line_speed
            p2[1] -= self.line_speed
            if p1[1] < -self.line_width:
                p1[1] = HEIGHT - (-5*self.line_width)
                p2[1] = HEIGHT - self.line_width * 4 - (-5*self.line_width)


class Editor_Background2:
    def __init__(self, game):
        self.game = game
        self.screen = self.game.screen

        self.line_number = 40
        self.lines = [{
            "start" : vec(random.uniform(-WIDTH/2, WIDTH), random.uniform(0, HEIGHT * 1.5)),
            "end" : vec(),
            "colour" : random.choices([(22, 22, 22), (55, 55, 55)], [2, 1])[0],
            "z" : random.uniform(1.5, 7),
        } for i in range(self.line_number)]

        self.scale = [1.25, -3.5]
        for i in range(len(self.lines)):
            start = self.lines[i]["start"]
            scale_scalar = 100 / self.lines[i]["z"]
            self.lines[i]["end"] = (end := start + vec(self.scale) * scale_scalar)
            self.lines[i]["height"] = abs(start.y - end.y)
            self.lines[i]["speed"] = scale_scalar / 100
            self.lines[i]["width"] = max(14, scale_scalar / 2)


        self.particles = []
        for i in range(30):
            angle = math.radians(random.uniform(0, 360))
            radius = random.uniform(2, 4)
            pos = vec(random.uniform(0, WIDTH), random.uniform(0, HEIGHT))
            col = random.choice([(78, 78, 78), (69, 69, 69), (81, 81, 81)])
            vel = vec(random.uniform(4, 6), random.uniform(-2, 0))
            self.particles.append({"angle" : angle, "radius" : radius, "pos" : pos, "col" : col, "vel" : vel, "rot_direction":random.choice([-1, 1])})

    def draw_line(self, start, end, line_width = 10, colour = None):
        colour = colour or random.choice([(22, 22, 22), (55, 55, 55)])
        points = [
            vec(start[0] - line_width / 2, start[1]),
            vec(start[0] + line_width / 2, start[1]),
            vec(end[0] + line_width / 2, end[1]),
            vec(end[0] - line_width / 2, end[1]),
        ]
        pygame.draw.polygon(self.screen, colour, points)

    def draw_particle(self, info):
        points = [
            info["pos"] + vec(math.cos(info["angle"]), math.sin(info["angle"])) * info["radius"],
            info["pos"] + vec(math.cos(info["angle"] + math.pi / 2), math.sin(info["angle"] + math.pi / 2)) * info["radius"],
            info["pos"] + vec(math.cos(info["angle"] + math.pi), math.sin(info["angle"] + math.pi)) * info["radius"],
            info["pos"] + vec(math.cos(info["angle"] + (3 * math.pi) / 2), math.sin(info["angle"] + (3 * math.pi) / 2)) * info["radius"],
        ]
        pygame.draw.polygon(self.screen, info["col"], points)

    def update(self):
        self.screen.fill((30, 30, 30))

        for line in sorted(self.lines, key=lambda l: l["z"], reverse=True):
            self.draw_line(line["start"], line["end"], line_width=line["width"], colour=line["colour"])
            line["start"] += vec(self.scale) * line["speed"] * (self.game.dt * 80)
            line["end"] += vec(self.scale) * line["speed"] * (self.game.dt * 80)

            if line["start"].y < 0:
                line["start"].y = HEIGHT + line["height"]
                line["end"].y = HEIGHT
                line["start"].x = (x := random.uniform(-WIDTH/2, WIDTH))
                line["end"].x = x + self.scale[0] * (100 / line["z"])

        for particle in self.particles:
            self.draw_particle(particle)
            particle["vel"].y -= random.uniform(-1, 1) / 10
            particle["angle"] += (particle["vel"].magnitude() / 100) * particle["rot_direction"] * (self.game.dt * 80)
            particle["pos"] += (particle["vel"] / 2) * (self.game.dt * 80)

            if particle["pos"].y < 0 or particle["pos"].x > WIDTH:
                particle["pos"].x = 0
                particle["pos"].y = random.uniform(0, HEIGHT)
                particle["vel"] = vec(random.uniform(4, 6), random.uniform(0, 0))

    ############################################################################################## 

class Night_Sky:
    def __init__(self, game):
        self.game = game
        self.screen = self.game.screen

        self.bg = pygame.Surface((1280, 400), pygame.SRCALPHA)
        col1 = pygame.Color(40+16, 45+10, 73+30)
        col2 = pygame.Color(5+16, 4+10, 30+30)
        for y in range(HEIGHT//2):
            t = y / (HEIGHT//2)
            col = col1.lerp(col2, t)
            pygame.draw.line(self.bg, col, (0, y), (WIDTH*2, y))
        pygame.draw.rect(self.bg, col2, [0, HEIGHT//2, WIDTH*2, HEIGHT//2])

        # self.bg.blit(pygame.transform.scale(pygame.image.load("assets/backgrounds/night_sky/0.png").convert_alpha(), (1280, 400)), (0, 0))

    def update(self):
        self.screen.blit(self.bg, (-self.game.offset.x / 4, 0))
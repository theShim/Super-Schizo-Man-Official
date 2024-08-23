import contextlib
from typing import Any
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import random, math

from scripts.utils.CORE_FUNCS import vec
from scripts.config.SETTINGS import Z_LAYERS, TILE_SIZE, HEIGHT, GRAV

    ################################################################################################

class Rain_Particle(pygame.sprite.Sprite):
    def __init__(self, game, groups, pos):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen
        self.environment_manager = self.game.state_loader.current_state.environment_manager
        self.z = Z_LAYERS["foreground particle"]

        self.length = random.randint(4, 8)
        self.fall_speed = random.uniform(5, 10) * 2
        
        self.top_x = random.uniform(0.2, 2)
        self.bottom_x = self.top_x + random.uniform(0.4, 2) / 100
        self.top_x *= self.environment_manager.wind
        self.bottom_x *= self.environment_manager.wind
        
        self.pos = vec(pos)
        self.end_pos = vec(self.pos.x, self.pos.y + self.length + self.bottom_x)

        self.collision = random.randint(1, 100) == 1

    def move(self):
        self.pos.y += 0.9 * self.fall_speed
        self.end_pos.y += 0.9 * self.fall_speed

        self.pos.x += self.top_x
        self.end_pos.x += self.bottom_x

    def tile_collisions(self, tiles):
        if len(tiles):
            probability = int(2000 / len(tiles)) + 1
            if random.randint(1, probability) == 1:
                t = random.choice(tiles)
                pos = [random.uniform((t.pos[0] * TILE_SIZE), (t.pos[0] * TILE_SIZE) + TILE_SIZE), (t.pos[1] * TILE_SIZE) + random.uniform(0, TILE_SIZE/2)]
                for i in range(1, 3):
                    Rain_Splash(self.game, self.groups(), pos, random.uniform(2, 3))
                    # self.music_player.play("rain_splash", "rain")
        
    def update(self, tiles):
        if self.pos.y - self.game.offset.y > HEIGHT:
            return self.kill()

        self.move()
        if self.collision and self.environment_manager.weather["rain"]:
            self.tile_collisions(tiles)
        self.draw()

    def draw(self):
        pygame.draw.line(self.screen, (173, 206, 240), self.pos - self.game.offset, self.end_pos - self.game.offset)



class Rain_Splash(pygame.sprite.Sprite):
    def __init__(self, game, groups, pos, scale):
        super().__init__(groups)
        self.game = game
        self.screen = self.game.screen
        self.z = Z_LAYERS["foreground particle"]

        self.pos = vec(pos)
        self.scale = scale
        self.angle = math.radians(random.uniform(-120, -60))
        self.rotation = math.radians(random.uniform(0, 90))
        self.speed = random.uniform(4, 8)
        self.colour = (173, 206, 240)
        self.glow_col = (255, 255, 255)
        self.grav = 0

    def move(self):
        self.pos += vec(math.cos(self.angle), math.sin(self.angle)) * self.speed
        self.pos.y += self.grav
        self.grav += GRAV * self.game.dt

    def update(self):
        self.scale -= 0.2
        if self.scale <= 0:
            return self.kill()

        self.rotation += math.radians(self.speed)
        self.move()

        self.draw()

    def draw(self):
        points = [
            self.pos - self.game.offset + vec(math.cos(self.rotation), math.sin(self.rotation)) * self.scale,
            self.pos - self.game.offset + vec(math.cos(self.rotation + math.pi/2), math.sin(self.rotation + math.pi/2)) * self.scale,
            self.pos - self.game.offset + vec(math.cos(self.rotation + math.pi), math.sin(self.rotation + math.pi)) * self.scale,
            self.pos - self.game.offset + vec(math.cos(self.rotation + 3*math.pi/2), math.sin(self.rotation + 3*math.pi/2)) * self.scale,
        ]
        pygame.draw.polygon(self.screen, self.colour, points)
        pygame.draw.polygon(self.screen, list(map(lambda x: x-100, self.colour)), points, math.ceil(self.scale/4))

        self.game.state_loader.current_state.light_manager.add_glow(self.pos, self.scale * 4, self.glow_col)
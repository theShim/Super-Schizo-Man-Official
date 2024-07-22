import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

import random

from scripts.world_loading.tiles import Offgrid_Tile

from scripts.utils.CORE_FUNCS import vec
from scripts.config.SETTINGS import WIDTH, HEIGHT, FPS, Z_LAYERS

    ##############################################################################################

class Torch(Offgrid_Tile):
    def __init__(self, game, variant, pos):
        super().__init__(game, "torch", variant, pos)
        self.z = Z_LAYERS["foreground offgrid"]

        self.SPRITES = Offgrid_Tile.SPRITES["torch"]

        self.flame_intensity = 30
        self.start = True

    def update(self):
        img = self.SPRITES[self.variant]
        self.screen.blit(img, self.pos - self.game.offset)

        if self.start:
            for i in range(self.flame_intensity):
                self.game.state_loader.current_state.particle_manager.add_particle("fire", pos=(self.pos + vec(random.uniform(-5, 5) + 12, random.uniform(-5, 5) - 2)), radius=random.uniform(1, 3))
            self.start = False
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *
    
import sys

from scripts.entities.player import Player
from scripts.nature.nature_tiles.grass import Grass_Manager
from scripts.states.state_machine import State_Loader
from scripts.world_loading.tiles import Tile, Offgrid_Tile

from scripts.config.SETTINGS import DEBUG, WINDOW_TITLE, SIZE, FPS, WIDTH, HEIGHT, CAMERA_FOLLOW_SPEED
from scripts.utils.CORE_FUNCS import vec, check_loaded_sprite_number
from scripts.utils.debugger import Debugger

pygame.Rect = pygame.FRect

if DEBUG:
    #code profiling for performance optimisations
    import pstats
    import cProfile
    import io

    ##############################################################################################

class Game:
    def __init__(self):
        #intiaising pygame stuff
        self.initialise()

        #initalising pygame window
        flags = pygame.RESIZABLE | pygame.SCALED
        self.screen = pygame.display.set_mode(SIZE, flags)
        pygame.display.toggle_fullscreen()
        self.clock = pygame.time.Clock()
        self.running = True
        self.offset = vec()

        self.cache_sprites()

        #various sprite groups, just to collect everything together
        self.all_sprites = pygame.sprite.Group()
        self.entities = pygame.sprite.Group()
        self.player = Player(self, [self.all_sprites, self.entities])

        self.state_loader = State_Loader(self, start="debug")
        self.state_loader.populate_states()

        if DEBUG:
            self.debugger = Debugger()
            self.fps_clock = pygame.time.Clock()

        check_loaded_sprite_number()

    def initialise(self):
        pygame.init()  #general pygame
        pygame.font.init() #font stuff
        pygame.display.set_caption(WINDOW_TITLE) #Window Title

        pygame.mixer.pre_init(44100, 16, 2, 4096) #music stuff
        pygame.mixer.init()

        pygame.event.set_blocked(None) #setting allowed events to reduce lag
        pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.KEYUP, pygame.MOUSEWHEEL])

    def cache_sprites(self):
        Tile.cache_sprites()
        Offgrid_Tile.cache_sprites()
        Player.cache_sprites()
        Grass_Manager.cache_sprites()

    def calculate_offset(self):
        #have the screen offset kinda lerp to the player location
        self.offset.x += (self.player.rect.centerx - WIDTH/2 - self.offset.x) / CAMERA_FOLLOW_SPEED
        self.offset.y += (self.player.rect.centery - HEIGHT/2 - self.offset.y) / CAMERA_FOLLOW_SPEED

        #restricting the offsets
        #MAKE THIS DIFFERENT ACCORDING TO CUSTOM STAGE SIZES LATER
        #e.g. if self.offset.x < self.stage.offset.bounds[0]: x = self.stage.offset.bounds[0]
        if self.offset.x < 0:
            self.offset.x = 0
        # if self.offset.x > math.inf:
        #     self.offset.x = math.inf

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.running = False


    def run(self):
        if DEBUG:
            PROFILER = cProfile.Profile()
            PROFILER.enable()

        last_time = pygame.time.get_ticks()
        while self.running:
            #deltatime
            self.dt = (current_time := pygame.time.get_ticks()) - last_time
            self.dt /= 1000
            last_time = current_time

            self.handle_events()
            self.screen.fill((30, 30, 30))

            self.state_loader.update()

            if DEBUG:
                self.debugger.update()
                self.fps_clock.tick_busy_loop()
                self.debugger.add_text(f"FPS: {round(self.clock.get_fps(), 1)} | {round(self.fps_clock.get_fps(), 1)}")

            pygame.display.update()
            self.clock.tick(FPS)

        if DEBUG:
            PROFILER.disable()
            PROFILER.dump_stats("test.stats")
            pstats.Stats("test.stats", stream=(s:=io.StringIO())).sort_stats((sortby:=pstats.SortKey.CUMULATIVE)).print_stats()
            print(s.getvalue())

        pygame.quit()
        sys.exit()
    

    ##############################################################################################

if __name__ == "__main__":
    game = Game()
    game.run()
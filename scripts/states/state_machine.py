import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

from scripts.particles.particle_manager import Particle_Manager
from scripts.world_loading.tilemap import Tilemap

from scripts.config.SETTINGS import WIDTH, HEIGHT, FPS

    ##############################################################################################

#state handler / finite state machine that stores a queue of all states
# e.g. ["title_screen", "cutscene_1", "cutscene_2", "world_1"] (beats world 1) ->
#      ["title_screen", "cutscene_1", "cutscene_2", "world_2"] (presses exit button to main menu) ->
#      ["title_screen"] (loads world 2) ->
#      ["title_screen", "world_2"]

class State_Loader:
    def __init__(self, game, start="splash_screen"):
        self.game = game
        self.stack: list[State] = []

        self.start = start #what the state machine should begin on, useful for debugging to save having to run the entire game
        self.states = {}

    #storing all the states. has to be done post initialisation as the states are created after the State class below
    #is created
    def populate_states(self):
        # from scripts.states.states.splash_screen import Splash_Screen
        # from scripts.states.states.title_screen import Title_Screen

        from scripts.states.states.debug_stage import Debug_Stage

        self.states = {
            "debug" : Debug_Stage(self.game)
        }

        #adding the first state
        if self.start:
            try: self.add_state(self.states[self.start])
            except KeyError: self.add_state(MissingState(self.game, self.start))

        #############################################################################
    
    @property
    def current_state(self):
        return self.stack[-1]

    #the current state's tilemap, or the last state that has a tilemap
    @property
    def tilemap(self):# -> Tilemap:
        try:
            t = self.current_state.tilemap
            return t
        except AttributeError:
            for i in range(len(self.stack)-2, -1, -1):
                if (t := self.stack[i].tilemap): 
                    break
            else:
                t = "No Tilemap".lower()
            return t

        #############################################################################

    def add_state(self, state):
        self.stack.append(state)

    def pop_state(self):
        self.last_state = self.stack.pop(-1)

    def get_state(self, name):
        return self.states.get(name, default=None)

        #############################################################################

    #the main method, mostly rendering it and all sprite updates
    def update(self):
        self.stack[-1].update()

    ##############################################################################################

class State:
    def __init__(self, game, name, prev=None):
        self.game = game
        self.screen = self.game.screen

        self.name = name
        self.prev = prev #the previous state
        self.tilemap = Tilemap(self.game)
        self.particle_manager = Particle_Manager(self.game, self)

        self.bg_music = None

    def update(self):
        # if self.bg_music:
        #     if not self.game.music_player.is_playing("bg"):
        #         self.game.music_player.set_vol(vol=1, channel="bg")
        #         self.game.music_player.play(self.bg_music, "bg", loop=True, fade_in=1000)

        self.tilemap.nature_manager.update()
        self.particle_manager.update()

        self.game.calculate_offset() #camera
        self.render()

    def render(self):
        for spr in sorted(
                (
                    self.game.all_sprites.sprites() + 
                    [tile for tile in self.tilemap.offgrid_render()] + 
                    self.tilemap.nature_manager.render() + 
                    self.tilemap.render()
                ), 
                key=lambda s: s.z
            ):
            spr.update()

class Cutscene(State):
    def __init__(self, game, name, prev=None):
        super().__init__(game, name, prev)
        del self.tilemap

    def update(self):
        pass

    def render(self):
        pass

    ##############################################################################################

class MissingState:
    def __init__(self, game, state_name):
        self.game = game
        self.screen = self.game.screen
        self.state_name = state_name
        self.font = pygame.font.SysFont('Verdana', 10)

    def update(self):
        self.screen.fill((10, 10, 10))
        text = self.font.render(f"State: \"{self.state_name}\" Missing", False, (255, 255, 255))
        self.screen.blit(text, text.get_rect(bottomleft=(0, HEIGHT)))
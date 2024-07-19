import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

from scripts.config.SETTINGS import WIDTH, HEIGHT

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
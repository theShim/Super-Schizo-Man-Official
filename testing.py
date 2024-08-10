import random
import pygame

from pygame.locals import *


pygame.init()


SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

clock = pygame.time.Clock()

BG_COLOR = 0, 0, 0
PLAYER_COLOR = 255, 255, 255


class Player(pygame.sprite.Sprite):
    WALK_SPEED = 3
    RUN_SPEED = 6
    JUMP_SPEED = 15
    GRAVITY = 0.5

    def __init__(self):
        self.surf = pygame.Surface((32, 32))
        self.surf.fill(PLAYER_COLOR)
        self.new_pos()
        self.vx = 0
        self.vy = 0

    def new_pos(self):
        self.rect = self.surf.get_rect(
            left=random.randrange(SCREEN_WIDTH),
            top=random.randrange(SCREEN_HEIGHT // 3),
        )

    def draw(self):
        screen.blit(self.surf, self.rect)

    def move(self):
        self.rect.move_ip(self.vx, self.vy)

    def on_ground(self):
        return self.rect.bottom == SCREEN_HEIGHT - 1

    def keep_on_screen(self):
        if self.rect.left < 0:
            self.rect.left = 0
            self.vx = 0
        if self.rect.right >= SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH - 1
            self.vx = 0
        if self.rect.top < 0:
            self.rect.top = 0
            self.vy = 0
        if self.rect.bottom >= SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT - 1
            self.vy = 0

    def update(self, pressed_keys):
        if pressed_keys[K_LEFT] and not pressed_keys[K_RIGHT]:
            self.vx = -self.RUN_SPEED if pressed_keys[K_SPACE] else -self.WALK_SPEED
        elif pressed_keys[K_RIGHT] and not pressed_keys[K_LEFT]:
            self.vx = self.RUN_SPEED if pressed_keys[K_SPACE] else self.WALK_SPEED
        else:
            self.vx = 0
        self.vy += self.GRAVITY
        if pressed_keys[K_UP] and self.on_ground():
            self.vy = -self.JUMP_SPEED
        self.move()
        self.keep_on_screen()


def loop():
    player = Player()

    while True:
        # get events
        for e in pygame.event.get():
            if e.type == QUIT:
                return 
            elif e.type == KEYDOWN:
                if e.key == K_ESCAPE or e.key == K_q:
                    return
                elif e.key == K_r:
                    player.new_pos()

        pressed_keys = pygame.key.get_pressed()

        # update
        player.update(pressed_keys)

        # draw
        screen.fill(BG_COLOR)
        player.draw()
        pygame.display.flip()

        # tick
        clock.tick(60)


loop()

pygame.quit()
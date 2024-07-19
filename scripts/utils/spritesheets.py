import pygame
from scripts.config.SETTINGS import TILE_SIZE

def crop(spritesheet: pygame.Surface, x, y, width, height):
    try:
        return spritesheet.subsurface([x, y, width, height])
    except ValueError:
        surf = pygame.Surface((width, height)).convert_alpha()
        surf.blit(spritesheet, (0, 0), area=[x, y, width, height])
        return surf

class Spritesheet:

    @staticmethod
    def tile_handler(spritesheet_name: str, tilesize = TILE_SIZE, colourkey=(0, 0, 0)) -> list[pygame.sprite.Sprite]:
        path = "assets/tiles"
        sheet = pygame.image.load(f"{path}/{spritesheet_name}/spritesheet.png").convert_alpha()

        imgs = []
        for y in range(0, sheet.height, tilesize):
            for x in range(0, sheet.width, tilesize):
                img = crop(sheet, x, y, tilesize, tilesize)
                if tilesize != TILE_SIZE:
                    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                img.set_colorkey(colourkey)
                imgs.append(img)
        return imgs

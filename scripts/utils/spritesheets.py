import pygame
from scripts.config.SETTINGS import TILE_SIZE
from scripts.utils.CORE_FUNCS import crop

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

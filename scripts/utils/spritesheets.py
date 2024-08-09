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

    @staticmethod
    def midground_handler(spritesheet_name: str, tilesize = TILE_SIZE, colourkey=(0, 0, 0)) -> list[pygame.sprite.Sprite]:
        path = "assets/tiles"
        sheet = pygame.image.load(f"{path}/{spritesheet_name}/spritesheet.png").convert_alpha()
        edited_imgs = []

        mods = []
        for y in range(tilesize*3, sheet.height, tilesize):
            for x in range(0, sheet.width, tilesize):
                img = crop(sheet, x, y, tilesize, tilesize)
                if tilesize != TILE_SIZE:
                    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                img.set_colorkey(colourkey)
                mods.append(img)

        for y in range(0, tilesize*3, tilesize):
            for x in range(0, sheet.width, tilesize):
                img = crop(sheet, x, y, tilesize, tilesize)
                if tilesize != TILE_SIZE:
                    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
                img.set_colorkey(colourkey)

                for mod in mods:
                    edited_img = img.copy()
                    edited_img.blit(mod, (0, 0))
                    edited_imgs.append(edited_img)

                    edited_img = img.copy()
                    edited_img.blit(pygame.transform.flip(mod, False, True), (0, 0))
                    edited_imgs.append(edited_img)
                    
                    edited_img = img.copy()
                    edited_img.blit(pygame.transform.flip(mod, True, False), (0, 0))
                    edited_imgs.append(edited_img)
                    
                    edited_img = img.copy()
                    edited_img.blit(pygame.transform.flip(mod, True, True), (0, 0))
                    edited_imgs.append(edited_img)
        
        return edited_imgs
    

    @staticmethod
    def player(player_number, spritesheet_name: str, size, colourkey=(0, 0, 0), save=False):
        path = f"assets/entities/players/{player_number}/{spritesheet_name}"
        sheet = pygame.image.load(path + "/spritesheet.png").convert_alpha()
        sprites = []

        for x in range(0, sheet.width, size[0]):
            spr = crop(sheet, x, 0, size[0], size[1])
            spr.set_colorkey((colourkey))

            if save:
                pygame.image.save(spr, f"{path}/{x // size[0]}.png")
            else:
                sprites.append(spr)

        if not save:
            return sprites
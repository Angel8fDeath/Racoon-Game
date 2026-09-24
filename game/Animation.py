import pygame


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(
        self,
        pos_x,
        pos_y,
        animation_files,
        animation_speed=0.25,
        loop=False,
    ):
        super().__init__()

        self.animation_speed = animation_speed
        self.loop = loop

        # Load animation images
        self.sprites = [
            pygame.image.load(image).convert_alpha()
            for image in animation_files
        ]

        self.current_sprite = 0
        self.playing = False

        self.image = self.sprites[self.current_sprite]
        self.rect = self.image.get_rect()
        self.rect.topleft = (pos_x, pos_y)

    def play(self):
        # Don't restart the animation if it's already playing
        if not self.playing:
            self.current_sprite = 0
            self.playing = True

    def stop(self):
        self.playing = False
        self.current_sprite = 0
        self.image = self.sprites[0]

    def update(self):
        if not self.playing:
            return

        self.current_sprite += self.animation_speed

        # Animation finished
        if int(self.current_sprite) >= len(self.sprites):

            if self.loop:
                self.current_sprite = 0

            else:
                self.current_sprite = len(self.sprites) - 1
                self.playing = False

        self.image = self.sprites[int(self.current_sprite)]

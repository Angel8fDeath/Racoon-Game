import pygame
from pathlib import Path
import random

ASSET_DIR = Path(__file__).resolve().parent.parent / "images"
SOUND_DIR = ASSET_DIR

WIDTH = 1200
HEIGHT = 900

def run_intro(window):
    raccoon_sound = pygame.mixer.Sound(SOUND_DIR / "Trash.mp3")
    raccoon_image = pygame.image.load(ASSET_DIR / "RaccoonBASE.png").convert_alpha()
    trash_image = pygame.image.load(ASSET_DIR / "Trash.png").convert_alpha()
    flashlight_image = pygame.image.load(ASSET_DIR / "Flashlight.png").convert_alpha()

    trash_image = pygame.transform.scale(trash_image, (trash_image.get_width() * 12, trash_image.get_height() * 12))
    flashlight_image = pygame.transform.scale(flashlight_image, (flashlight_image.get_width() * 9, flashlight_image.get_height() * 9))
    raccoon_image = pygame.transform.scale(raccoon_image, (raccoon_image.get_width() * 5, raccoon_image.get_height() * 5))

    light = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    darkness = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 50)

    start_time = pygame.time.get_ticks()
    sound_played = False
    running = True

    while running:
        elapsed = (pygame.time.get_ticks() - start_time) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
            if elapsed >= 10 and event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return True
            if elapsed >= 10 and event.type == pygame.MOUSEBUTTONDOWN and pygame.Rect(500, 700, 200, 70).collidepoint(event.pos):
                return True

        window.fill((30, 35, 50))

        if elapsed >= 1.5 and not sound_played:
            raccoon_sound.play()
            sound_played = True

        if 2 <= elapsed <= 6.5:
            shake_x, shake_y = random.randint(-3, 3), random.randint(-3, 3)
            window.blit(trash_image, (100 + shake_x, -50 + shake_y))
        else:
            window.blit(trash_image, (100, -50))

        light.fill((0, 0, 0, 0))

        if elapsed >= 6.5:
            window.blit(flashlight_image, (60, 500))
            window.blit(raccoon_image, (0, 0))

            pygame.draw.polygon(light, (255, 255, 255), [
                (WIDTH * 0.1, HEIGHT * 1.2),
                (WIDTH * 0.335, HEIGHT * 0.2),
                (WIDTH * 0.67, HEIGHT * 0.49)
            ])
            pygame.draw.circle(light, (255, 255, 255), (WIDTH * 0.5, HEIGHT * 0.35), WIDTH * 0.2)

        darkness.fill((0, 0, 0, 180))
        darkness.blit(light, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        window.blit(darkness, (0, 0))

        if elapsed >= 10:
            continue_rect = pygame.Rect(500, 700, 200, 70)
            pygame.draw.rect(window, (80, 80, 80), continue_rect)
            pygame.draw.rect(window, (220, 220, 220), continue_rect, 2)
            window.blit(font.render("CONTINUE", True, (255, 255, 255)), (520, 715))

        pygame.display.flip()
        clock.tick(60)

def main():
    pygame.init()
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Raccoon Game Intro")
    try:
        run_intro(window)
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()
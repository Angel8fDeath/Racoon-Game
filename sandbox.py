import pygame
from pathlib import Path
import time

from game import HEIGHT, PLAYER_SIZE, WIDTH, keyboard_state, move_player, setup_window


def run_sandbox():
    """Run the gameplay loop locally without starting a LAN server or client."""
    window = setup_window("Gameplay Sandbox")
    
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 28)
    trash_image = pygame.image.load("Trash.png").convert_alpha()
    trash_image = pygame.transform.scale(trash_image,(trash_image.get_width() * 9, trash_image.get_height() * 9))
    raccoon_path = Path(__file__).with_name("RaccoonBASE.png.png")
    raccoon = pygame.image.load(raccoon_path).convert_alpha()
    raccoon = pygame.transform.smoothscale(raccoon, (PLAYER_SIZE, PLAYER_SIZE))
    player = pygame.Rect(
        (WIDTH - PLAYER_SIZE) // 2,
        (HEIGHT - PLAYER_SIZE) // 2,
        PLAYER_SIZE,
        PLAYER_SIZE,
    )
    waiting = True
    start_time = time.time()
    button_visible = False

    button = pygame.Rect(300, 250, 200, 75)

    running = True

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if button_visible and button.collidepoint(event.pos):
                        waiting = False
            if waiting and time.time() - start_time >= 10:
                button_visible = True

            if waiting:
                window.fill((30, 35, 50))
                if button_visible:
                    # Button shadow
                    shadow = button.move(6, 6)
                    pygame.draw.rect(window, (20, 20, 20), shadow, border_radius=12)

                    # Main button
                    pygame.draw.rect(window, (60, 180, 90), button, border_radius=12)

                    # Dark outline
                    pygame.draw.rect(window, (20, 70, 35), button, 5, border_radius=12)

                    # Highlight at the top
                    highlight = pygame.Rect(
                        button.x + 8,
                        button.y + 6,
                        button.width - 16,
                        10
                    )
                    pygame.draw.rect(window, (120, 230, 140), highlight, border_radius=5)

                    # Text
                    font = pygame.font.Font(None, 42)
                    text = font.render("CONTINUE", True, (255, 255, 255))
                    text_rect = text.get_rect(center=button.center)

                    # Text shadow
                    shadow_text = font.render("CONTINUE", True, (30, 60, 35))
                    shadow_rect = shadow_text.get_rect(
                        center=(button.centerx + 2, button.centery + 3)
                    )
                    window.blit(shadow_text, shadow_rect)

                    window.blit(text, text_rect)

                pygame.display.flip()
                clock.tick(60)

            else:
                move_player(player, keyboard_state())
                window.fill((30, 35, 50))
                window.blit(trash_image, (150, -20))
                window.blit(raccoon, player)
                status = font.render("Arrow keys to move | ESC to quit", True, (220, 220, 220))
                window.blit(status, (15, 15))
                pygame.display.flip()
                clock.tick(60)
    finally:
        pygame.quit()


if __name__ == "__main__":
    run_sandbox()
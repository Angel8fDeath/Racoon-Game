import base64
import io
import json
from pathlib import Path

import pygame


WIDTH, HEIGHT = 1200, 900
WORLD_WIDTH, WORLD_HEIGHT = 2400, 1800
PLAYER_SIZE = 50
PLAYER_IMAGE_PATH = Path(__file__).parent.parent / "images" / "RaccoonBASE.png"
MAX_PLAYERS = 5
PORT = 5000


def send_message(connection, message):
	connection.sendall((json.dumps(message) + "\n").encode("utf-8"))


def setup_window(title):
	pygame.init()
	if pygame.display.get_driver() == "offscreen":
		pygame.quit()
		raise RuntimeError("No graphical display is available. Run the game on a local desktop.")
	window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
	pygame.display.set_caption(title)
	return window


def load_player_image(image_data=None):
	if image_data:
		image_source = io.BytesIO(base64.b64decode(image_data))
	else:
		image_source = str(PLAYER_IMAGE_PATH)
	image = pygame.image.load(image_source).convert_alpha()
	return pygame.transform.smoothscale(image, (PLAYER_SIZE, PLAYER_SIZE))


def keyboard_state():
	keys = pygame.key.get_pressed()
	return {
		"type": "input",
		"left": bool(keys[pygame.K_LEFT]),
		"right": bool(keys[pygame.K_RIGHT]),
		"up": bool(keys[pygame.K_UP]),
		"down": bool(keys[pygame.K_DOWN]),
	}



def camera_position(player_position):
	player_x, player_y = player_position
	camera_x = max(0, min(player_x + PLAYER_SIZE // 2 - WIDTH // 2, WORLD_WIDTH - WIDTH))
	camera_y = max(0, min(player_y + PLAYER_SIZE // 2 - HEIGHT // 2, WORLD_HEIGHT - HEIGHT))
	return camera_x, camera_y


def draw_background(window, camera_x, camera_y):
	tile_size = 100
	window.fill((72, 111, 67))
	start_x = -(camera_x % tile_size)
	start_y = -(camera_y % tile_size)
	for screen_y in range(start_y, HEIGHT, tile_size):
		for screen_x in range(start_x, WIDTH, tile_size):
			world_x = screen_x + camera_x
			world_y = screen_y + camera_y
			color = (78, 119, 71) if (world_x // tile_size + world_y // tile_size) % 2 else (72, 111, 67)
			pygame.draw.rect(window, color, (screen_x, screen_y, tile_size, tile_size))
	pygame.draw.line(window, (105, 145, 87), (0, 0), (WIDTH, 0), 2)


def move_player(rect, controls):
	if controls.get("left"):
		rect.x -= 5
	if controls.get("right"):
		rect.x += 5
	if controls.get("up"):
		rect.y -= 5
	if controls.get("down"):
		rect.y += 5
	rect.clamp_ip(pygame.Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT))
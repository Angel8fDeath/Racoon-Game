import base64
import io
import json
from pathlib import Path

import pygame


WIDTH, HEIGHT = 800, 600
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
	window = pygame.display.set_mode((WIDTH, HEIGHT))
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


def move_player(rect, controls):
	if controls.get("left"):
		rect.x -= 5
	if controls.get("right"):
		rect.x += 5
	if controls.get("up"):
		rect.y -= 5
	if controls.get("down"):
		rect.y += 5
	rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))
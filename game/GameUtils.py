import base64
import io
import json
import math
from pathlib import Path

import pygame


WIDTH, HEIGHT = 1200, 900
WORLD_WIDTH, WORLD_HEIGHT = 2400, 1800
PLAYER_SIZE = 58
FLASHLIGHT_RADIUS = 380
FLASHLIGHT_HALF_SPREAD = math.radians(16)
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
	surface = pygame.display.get_surface()
	window_width, window_height = surface.get_size() if surface else (WIDTH, HEIGHT)
	mouse_x, mouse_y = pygame.mouse.get_pos()
	return {
		"type": "input",
		"left": bool(keys[pygame.K_LEFT]),
		"right": bool(keys[pygame.K_RIGHT]),
		"up": bool(keys[pygame.K_UP]),
		"down": bool(keys[pygame.K_DOWN]),
		"aim": [mouse_x - window_width // 2, mouse_y - window_height // 2],
	}



def camera_position(player_position):
	player_x, player_y = player_position
	camera_x = max(0, min(player_x + PLAYER_SIZE // 2 - WIDTH // 2, WORLD_WIDTH - WIDTH))
	camera_y = max(0, min(player_y + PLAYER_SIZE // 2 - HEIGHT // 2, WORLD_HEIGHT - HEIGHT))
	return camera_x, camera_y


def draw_background(window, camera_x, camera_y):
	tile_size = 100
	window_width, window_height = window.get_size()
	window.fill((20, 28, 24))
	start_x = -(camera_x % tile_size)
	start_y = -(camera_y % tile_size)
	for screen_y in range(start_y, window_height, tile_size):
		for screen_x in range(start_x, window_width, tile_size):
			world_x = screen_x + camera_x
			world_y = screen_y + camera_y
			color = (25, 36, 29) if (world_x // tile_size + world_y // tile_size) % 2 else (20, 28, 24)
			pygame.draw.rect(window, color, (screen_x, screen_y, tile_size, tile_size))
	pygame.draw.line(window, (48, 66, 45), (0, 0), (window_width, 0), 2)


def draw_flashlight(window, origin, aim_vector):
	vector_x, vector_y = aim_vector
	length = math.hypot(vector_x, vector_y)
	if length < 0.1:
		vector_x, vector_y, length = 0, -1, 1
	direction = math.atan2(vector_y, vector_x)
	radius = min(window.get_size()) * 0.42
	half_spread = FLASHLIGHT_HALF_SPREAD
	left = (origin[0] + math.cos(direction - half_spread) * radius, origin[1] + math.sin(direction - half_spread) * radius)
	right = (origin[0] + math.cos(direction + half_spread) * radius, origin[1] + math.sin(direction + half_spread) * radius)
	light = pygame.Surface(window.get_size(), pygame.SRCALPHA)
	pygame.draw.polygon(light, (255, 222, 145, 78), [origin, left, right])
	pygame.draw.polygon(light, (255, 236, 180, 34), [origin, (origin[0] + (left[0] - origin[0]) * 0.62, origin[1] + (left[1] - origin[1]) * 0.62), (origin[0] + (right[0] - origin[0]) * 0.62, origin[1] + (right[1] - origin[1]) * 0.62)])
	pygame.draw.circle(light, (255, 225, 150, 72), origin, round(PLAYER_SIZE * 1.45))
	window.blit(light, (0, 0))


def is_inside_flashlight(origin, target, aim_vector):
	vector_x = target[0] - origin[0]
	vector_y = target[1] - origin[1]
	distance = math.hypot(vector_x, vector_y)
	if distance > FLASHLIGHT_RADIUS:
		return False
	if distance == 0:
		return True
	aim_x, aim_y = aim_vector
	aim_length = math.hypot(aim_x, aim_y)
	if aim_length < 0.1:
		aim_x, aim_y, aim_length = 0, -1, 1
	dot = (vector_x * aim_x + vector_y * aim_y) / (distance * aim_length)
	return dot >= math.cos(FLASHLIGHT_HALF_SPREAD)


def draw_catch_indicator(window, center, progress):
	progress = max(0.0, min(1.0, progress))
	if progress == 0:
		return
	radius = max(10, round(PLAYER_SIZE * 0.24))
	pygame.draw.circle(window, (12, 14, 16), center, radius + 3)
	pygame.draw.circle(window, (104, 42, 42), center, radius, 2)
	if progress > 0:
		points = [center]
		for step in range(25):
			angle = -math.pi / 2 + (math.tau * progress * step / 24)
			points.append((center[0] + math.cos(angle) * radius, center[1] + math.sin(angle) * radius))
		pygame.draw.polygon(window, (239, 98, 68), points)
	pygame.draw.circle(window, (255, 184, 120), center, radius, 2)


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
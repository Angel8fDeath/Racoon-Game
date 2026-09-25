import base64
import heapq
import io
import json
import math
import random
from pathlib import Path

import pygame


WIDTH, HEIGHT = 1200, 900
WORLD_WIDTH, WORLD_HEIGHT = 4800, 3600
PLAYER_SIZE = 100
NEST_RECT = pygame.Rect(180, WORLD_HEIGHT // 2 - 240, 420, 480)
FOOD_ZONE_RECTS = [
	pygame.Rect(WORLD_WIDTH - 620, 260 + index * 650, 360, 300)
	for index in range(5)
]
DASH_BOOST_SPEED = 700
DASH_BOOST_DURATION = 0.45
DASH_COOLDOWN = 3.0
FLASHLIGHT_RADIUS = 380
FLASHLIGHT_HALF_SPREAD = math.radians(16)
PLAYER_IMAGE_PATH = Path(__file__).parent.parent / "images" / "Magic Raccooon" / "MagicRaccoon01.png"
PLAYER_ANIMATION_PATHS = sorted(PLAYER_IMAGE_PATH.parent.glob("MagicRaccoon*.png"))
MAX_PLAYERS = 5
PORT = 5000
SHOW_HITBOXES = True


def generate_obstacles(seed, count=24):
	randomizer = random.Random(seed)
	reserved = [
		NEST_RECT.inflate(260, 260),
		pygame.Rect(0, WORLD_HEIGHT // 2 - 260, 1050, 520),
		pygame.Rect(WORLD_WIDTH - 1050, WORLD_HEIGHT // 2 - 300, 1050, 600),
	]
	reserved.extend(zone.inflate(100, 100) for zone in FOOD_ZONE_RECTS)
	obstacles = []
	for _ in range(count * 12):
		if len(obstacles) >= count:
			break
		width = randomizer.randrange(130, 321, 20)
		height = randomizer.randrange(110, 281, 20)
		candidate = pygame.Rect(
			randomizer.randrange(700, WORLD_WIDTH - width - 700, 80),
			randomizer.randrange(220, WORLD_HEIGHT - height - 220, 80),
			width,
			height,
		)
		if any(candidate.colliderect(area) for area in reserved):
			continue
		if any(candidate.inflate(120, 120).colliderect(obstacle) for obstacle in obstacles):
			continue
		obstacles.append([candidate.x, candidate.y, candidate.width, candidate.height])
	return obstacles


def find_path(start_position, goal_position, obstacles, grid_size=120):
	columns = max(1, WORLD_WIDTH // grid_size)
	rows = max(1, WORLD_HEIGHT // grid_size)
	blocked = set()
	for column in range(columns):
		for row in range(rows):
			cell = pygame.Rect(column * grid_size + 8, row * grid_size + 8, grid_size - 16, grid_size - 16)
			if any(cell.colliderect(pygame.Rect(obstacle).inflate(PLAYER_SIZE, PLAYER_SIZE)) for obstacle in obstacles):
				blocked.add((column, row))

	def to_cell(position):
		return (
			max(0, min(columns - 1, int(position[0] // grid_size))),
			max(0, min(rows - 1, int(position[1] // grid_size))),
		)

	start = to_cell(start_position)
	goal = to_cell(goal_position)
	blocked.discard(start)
	blocked.discard(goal)
	frontier = [(0, start)]
	came_from = {start: None}
	cost_so_far = {start: 0}
	while frontier:
		_, current = heapq.heappop(frontier)
		if current == goal:
			break
		for delta_x, delta_y in ((1, 0), (-1, 0), (0, 1), (0, -1)):
			next_cell = current[0] + delta_x, current[1] + delta_y
			if not (0 <= next_cell[0] < columns and 0 <= next_cell[1] < rows) or next_cell in blocked:
				continue
			new_cost = cost_so_far[current] + 1
			if next_cell not in cost_so_far or new_cost < cost_so_far[next_cell]:
				cost_so_far[next_cell] = new_cost
				heuristic = abs(goal[0] - next_cell[0]) + abs(goal[1] - next_cell[1])
				heapq.heappush(frontier, (new_cost + heuristic, next_cell))
				came_from[next_cell] = current
	if goal not in came_from:
		return []
	path = []
	current = goal
	while current is not None:
		path.append((current[0] * grid_size + grid_size // 2, current[1] * grid_size + grid_size // 2))
		current = came_from[current]
	return list(reversed(path))


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


def load_player_images(image_data=None):
	images = []
	if image_data:
		image_source = io.BytesIO(base64.b64decode(image_data))
		images.append(pygame.image.load(image_source).convert_alpha())
	for image_path in PLAYER_ANIMATION_PATHS:
		if image_data and image_path == PLAYER_IMAGE_PATH:
			continue
		images.append(pygame.image.load(str(image_path)).convert_alpha())
	prepared_images = []
	for image in images:
		visible_rect = image.get_bounding_rect()
		if visible_rect.width == 0 or visible_rect.height == 0:
			continue
		image = image.subsurface(visible_rect).copy()
		image = pygame.transform.scale_by(image, 3)
		scale = min(1.0, (PLAYER_SIZE * 0.9) / image.get_width(), (PLAYER_SIZE * 0.9) / image.get_height())
		if scale < 1.0:
			image_size = (round(image.get_width() * scale), round(image.get_height() * scale))
			image = pygame.transform.smoothscale(image, image_size)
		prepared_images.append(image)
	return prepared_images


def load_player_image(image_data=None):
	return load_player_images(image_data)[0]


def draw_player(window, images, hitbox, animation_time, moving=False):
	if moving and len(images) > 1:
		image = images[int(animation_time * 5 % len(images))]
	else:
		image = images[0]
	image_rect = image.get_rect(center=hitbox.center)
	window.blit(image, image_rect)


def draw_hitbox(window, hitbox):
	if SHOW_HITBOXES:
		pygame.draw.rect(window, (255, 40, 40), hitbox, 2)


def keyboard_state():
	keys = pygame.key.get_pressed()
	surface = pygame.display.get_surface()
	window_width, window_height = surface.get_size() if surface else (WIDTH, HEIGHT)
	mouse_x, mouse_y = pygame.mouse.get_pos()
	return {
		"type": "input",
		"left": bool(keys[pygame.K_LEFT]) or bool(keys[pygame.K_a]),
		"right": bool(keys[pygame.K_RIGHT]) or bool(keys[pygame.K_d]),
		"up": bool(keys[pygame.K_UP]) or bool(keys[pygame.K_w]),
		"down": bool(keys[pygame.K_DOWN]) or bool(keys[pygame.K_s]),
		"dash": bool(keys[pygame.K_SPACE]),
		"interact": bool(keys[pygame.K_e]),
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


def draw_obstacles(window, camera_x, camera_y, obstacles):
	for raw_obstacle in obstacles:
		obstacle = pygame.Rect(raw_obstacle).move(-camera_x, -camera_y)
		pygame.draw.rect(window, (10, 14, 12), obstacle.inflate(14, 14), border_radius=10)
		pygame.draw.rect(window, (48, 58, 49), obstacle, border_radius=8)
		pygame.draw.rect(window, (79, 91, 72), obstacle.inflate(-12, -12), 3, border_radius=6)
		pygame.draw.line(window, (104, 111, 83), obstacle.topleft, obstacle.bottomright, 3)


def draw_food_zones(window, camera_x, camera_y, delivered_food):
	for index, zone in enumerate(FOOD_ZONE_RECTS):
		rect = zone.move(-camera_x, -camera_y)
		color = (191, 143, 62) if index in delivered_food else (92, 124, 84)
		pygame.draw.rect(window, (12, 18, 14), rect.inflate(12, 12))
		for offset_x, offset_y, radius, shade in ((70, 100, 42, (61, 67, 59)), (150, 170, 52, (84, 74, 56)), (250, 95, 46, (50, 58, 53)), (205, 235, 36, (116, 83, 57))):
			pygame.draw.circle(window, shade, (rect.x + offset_x, rect.y + offset_y), radius)
		pygame.draw.rect(window, (24, 29, 25), (rect.x + 92, rect.y + 55, 88, 54), border_radius=12)
		pygame.draw.rect(window, color, rect, 4)
		pygame.draw.circle(window, color, rect.center, 22, 3)
		label = pygame.font.Font(None, 26).render("FOOD ZONE", True, (241, 235, 220))
		window.blit(label, (rect.centerx - label.get_width() // 2, rect.y + 12))


def draw_nest(window, camera_x, camera_y, food_count=0):
	rect = NEST_RECT.move(-camera_x, -camera_y)
	pygame.draw.rect(window, (12, 18, 14), rect.inflate(12, 12))
	body = pygame.Rect(rect.x + 34, rect.y + 60, rect.width - 68, rect.height - 82)
	lid = pygame.Rect(rect.x + 15, rect.y + 34, rect.width - 30, 42)
	pygame.draw.rect(window, (74, 91, 78), body, border_radius=8)
	pygame.draw.rect(window, (112, 128, 101), lid, border_radius=6)
	pygame.draw.line(window, (35, 47, 39), lid.midleft, lid.midright, 6)
	pygame.draw.circle(window, (35, 47, 39), (body.x + 55, body.bottom + 8), 18)
	pygame.draw.circle(window, (35, 47, 39), (body.right - 55, body.bottom + 8), 18)
	label = pygame.font.Font(None, 34).render("NEST", True, (241, 235, 220))
	window.blit(label, (body.centerx - label.get_width() // 2, body.y + 42))
	counter = pygame.font.Font(None, 30).render(f"FOOD: {food_count}", True, (255, 220, 145))
	window.blit(counter, (body.centerx - counter.get_width() // 2, body.y + 92))


def draw_food_counter(window, rect, count):
	bar_y = rect.bottom + 5
	counter_rect = pygame.Rect(rect.right + 10, bar_y - 7, 112, 20)
	pygame.draw.rect(window, (8, 10, 12), counter_rect)
	pygame.draw.rect(window, (191, 143, 62), counter_rect, 1)
	text = pygame.font.Font(None, 22).render(f"FOOD {count}/3", True, (255, 220, 145))
	window.blit(text, (counter_rect.x + 6, counter_rect.y + 2))


def draw_food_action(window, center, action, feedback=None):
	if action:
		progress = max(0.0, min(1.0, action.get("progress", 0.0)))
		radius = PLAYER_SIZE // 2 + 12
		circle_rect = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
		pygame.draw.circle(window, (12, 14, 16), center, radius + 4)
		pygame.draw.arc(window, (255, 220, 145), circle_rect, -math.pi / 2, -math.pi / 2 + math.tau * progress, 5)
		label = "COLLECTING" if action.get("type") == "collect" else "DEPOSITING"
		text = pygame.font.Font(None, 22).render(label, True, (255, 220, 145))
		window.blit(text, (center[0] - text.get_width() // 2, center[1] - radius - 25))
	elif feedback:
		text = pygame.font.Font(None, 22).render(feedback, True, (151, 205, 116))
		window.blit(text, (center[0] - text.get_width() // 2, center[1] - PLAYER_SIZE // 2 - 25))


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


def draw_stamina_bar(window, rect, remaining, maximum=DASH_COOLDOWN):
	ratio = max(0.0, min(1.0, remaining / maximum if maximum else 0.0))
	bar = pygame.Rect(rect.x, rect.bottom + 5, rect.width, 6)
	pygame.draw.rect(window, (8, 10, 12), bar)
	pygame.draw.rect(window, (92, 124, 84), bar, 1)
	if ratio > 0:
		fill = pygame.Rect(bar.x + 1, bar.y + 1, round((bar.width - 2) * ratio), bar.height - 2)
		pygame.draw.rect(window, (151, 205, 116), fill)


def move_rect(rect, delta_x, delta_y, obstacles):
	rect.x += delta_x
	for obstacle in obstacles:
		obstacle_rect = pygame.Rect(obstacle)
		if rect.colliderect(obstacle_rect):
			if delta_x > 0:
				rect.right = obstacle_rect.left
			elif delta_x < 0:
				rect.left = obstacle_rect.right
	rect.y += delta_y
	for obstacle in obstacles:
		obstacle_rect = pygame.Rect(obstacle)
		if rect.colliderect(obstacle_rect):
			if delta_y > 0:
				rect.bottom = obstacle_rect.top
			elif delta_y < 0:
				rect.top = obstacle_rect.bottom
	rect.clamp_ip(pygame.Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT))


def move_player(rect, controls, obstacles=()):
	delta_x = 5 * (int(bool(controls.get("right"))) - int(bool(controls.get("left"))))
	delta_y = 5 * (int(bool(controls.get("down"))) - int(bool(controls.get("up"))))
	move_rect(rect, delta_x, delta_y, obstacles)


def dash_direction(controls):
	direction_x = int(controls.get("right", False)) - int(controls.get("left", False))
	direction_y = int(controls.get("down", False)) - int(controls.get("up", False))
	if direction_x == 0 and direction_y == 0:
		direction_x, direction_y = controls.get("aim", [0, -1])
	length = math.hypot(direction_x, direction_y)
	if length < 0.1:
		return None
	return direction_x / length, direction_y / length


def apply_dash_boost(rect, boost, elapsed, obstacles=()):
	ratio = max(0.0, min(1.0, boost["remaining"] / DASH_BOOST_DURATION))
	direction_x, direction_y = boost["direction"]
	move_rect(rect, round(direction_x * DASH_BOOST_SPEED * ratio * elapsed), round(direction_y * DASH_BOOST_SPEED * ratio * elapsed), obstacles)
	boost["remaining"] -= elapsed
	return boost["remaining"] > 0
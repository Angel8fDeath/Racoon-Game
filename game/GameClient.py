import json
import socket
import threading
import time

import pygame

from lobby import LobbyView, RED_BRIGHT
from GameUtils import (
	HEIGHT,
	PLAYER_SIZE,
	WORLD_HEIGHT,
	WORLD_WIDTH,
	WIDTH,
	FOOD_ZONE_RECTS,
	NEST_RECT,
	camera_position,
	draw_background,
	draw_obstacles,
	draw_food_zones,
	draw_nest,
	draw_food_counter,
	draw_food_action,
	draw_flashlight,
	draw_catch_indicator,
	draw_stamina_bar,
	draw_player,
	draw_hitbox,
	DASH_COOLDOWN,
	keyboard_state,
	load_player_images,
	send_message,
	setup_window,
)


def client_game(address, port, player_name="Player"):
	connection = socket.create_connection((address, port))
	reader = connection.makefile("r", encoding="utf-8")
	welcome = json.loads(reader.readline())
	player_id = welcome["player_id"]
	player_name = "".join(character for character in str(player_name) if character.isprintable()).strip()[:20] or "Player"
	send_message(connection, {"type": "player_info", "name": player_name})
	latest_state = {}
	latest_names = {str(player_id): player_name}
	latest_aims = {}
	latest_catch_progress = {}
	latest_timer = 300
	latest_delivered_food = []
	latest_carried_food = []
	latest_food_counts = {}
	latest_nest_food = 0
	latest_food_actions = {}
	latest_food_feedback = {}
	latest_obstacles = []
	dash_stamina = {}
	previous_positions = {}
	lobby_state = {"players": [0, player_id], "names": latest_names, "votes": {}, "selected_mode": "Survivors", "chaser_id": None}
	state_lock = threading.Lock()
	running = True
	game_started = False
	game_chaser_id = None
	return_to_menu = False
	last_stamina_update = time.monotonic()

	def receive_states():
		nonlocal running, latest_state, latest_names, latest_aims, latest_catch_progress, latest_timer, latest_delivered_food, latest_carried_food, latest_food_counts, latest_nest_food, latest_food_actions, latest_food_feedback, latest_obstacles, lobby_state, game_started, game_chaser_id, dash_stamina
		try:
			for line in reader:
				message = json.loads(line)
				if message.get("type") == "state":
					with state_lock:
						latest_state = message["players"]
						latest_names = message.get("names", latest_names)
						latest_aims = message.get("aims", latest_aims)
						game_chaser_id = message.get("chaser_id", game_chaser_id)
						latest_catch_progress = message.get("catch_progress", latest_catch_progress)
						latest_timer = message.get("timer", latest_timer)
						latest_delivered_food = message.get("delivered_food", latest_delivered_food)
						latest_carried_food = message.get("carried_food", latest_carried_food)
						latest_food_counts = message.get("food_counts", latest_food_counts)
						latest_nest_food = message.get("nest_food", latest_nest_food)
						latest_food_actions = message.get("food_actions", latest_food_actions)
						latest_obstacles = message.get("obstacles", latest_obstacles)
						for event in message.get("food_events", []):
							latest_food_feedback[event["player_id"]] = (event["message"], time.monotonic() + 1.0)
				elif message.get("type") == "lobby":
					with state_lock:
						lobby_state = message
						latest_names = message.get("names", latest_names)
				elif message.get("type") == "start_game":
					game_chaser_id = message.get("chaser_id")
					latest_obstacles = message.get("obstacles", [])
					game_started = True
				elif message.get("type") == "return_lobby":
					with state_lock:
						latest_state = {}
						latest_delivered_food = []
						latest_carried_food = []
						latest_food_counts = {}
						latest_food_actions = {}
						latest_obstacles = []
					game_started = False
				elif message.get("type") == "dash_success":
					with state_lock:
						dash_stamina[str(message.get("player_id"))] = 0.0
		except (OSError, ValueError):
			running = False

	threading.Thread(target=receive_states, daemon=True).start()
	window = setup_window(f"LAN Game - Player {player_id + 1}")
	clock = pygame.time.Clock()
	font = pygame.font.Font(None, 28)
	player_font = pygame.font.Font(None, 20)
	player_images = load_player_images(welcome["player_image"])
	lobby = LobbyView(player_id, False)
	try:
		while running and not game_started:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
					continue
				if event.type == pygame.VIDEORESIZE:
					window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
					continue
				action = lobby.handle_event(event)
				if action == "quit":
					running = False
				elif action == "menu":
					return_to_menu = True
					running = False
				elif isinstance(action, tuple) and action[0] == "vote_mode":
					try:
						send_message(connection, {"type": "lobby_action", "action": "vote_mode", "mode": action[1]})
					except OSError:
						running = False
			with state_lock:
				current_lobby = lobby_state.copy()
			lobby.draw(window, current_lobby)
			pygame.display.flip()
			clock.tick(30)

		while running:
			if not game_started:
				for event in pygame.event.get():
					if event.type == pygame.QUIT:
						running = False
					elif event.type == pygame.VIDEORESIZE:
						window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
					else:
						action = lobby.handle_event(event)
						if action == "quit":
							running = False
						elif action == "menu":
							return_to_menu = True
							running = False
						elif isinstance(action, tuple) and action[0] == "vote_mode":
							try:
								send_message(connection, {"type": "lobby_action", "action": "vote_mode", "mode": action[1]})
							except OSError:
								running = False
				with state_lock:
					current_lobby = lobby_state.copy()
				lobby.draw(window, current_lobby)
				pygame.display.flip()
				clock.tick(30)
				continue
			for event in pygame.event.get():
				if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
					running = False
			try:
				send_message(connection, keyboard_state())
			except OSError:
				running = False
			now = time.monotonic()
			stamina_elapsed = min(0.2, now - last_stamina_update)
			last_stamina_update = now
			with state_lock:
				state = latest_state.copy()
				names = latest_names.copy()
				aims = latest_aims.copy()
				catch_progress = latest_catch_progress.copy()
				timer = latest_timer
				delivered_food = latest_delivered_food.copy()
				carried_food = latest_carried_food.copy()
				food_counts = latest_food_counts.copy()
				nest_food = latest_nest_food
				food_actions = latest_food_actions.copy()
				food_feedback = latest_food_feedback.copy()
				obstacles = latest_obstacles.copy()
				for player_id in list(dash_stamina):
					dash_stamina[player_id] = min(DASH_COOLDOWN, dash_stamina[player_id] + stamina_elapsed)
				stamina = dash_stamina.copy()
			local_position = state.get(str(player_id), [WORLD_WIDTH // 2, WORLD_HEIGHT // 2])
			camera_x, camera_y = camera_position(local_position)
			draw_background(window, camera_x, camera_y)
			draw_obstacles(window, camera_x, camera_y, obstacles)
			draw_food_zones(window, camera_x, camera_y, delivered_food)
			draw_nest(window, camera_x, camera_y, nest_food)
			if game_chaser_id is not None and str(game_chaser_id) in state:
				chaser_position = state[str(game_chaser_id)]
				chaser_rect = pygame.Rect(chaser_position[0] - camera_x, chaser_position[1] - camera_y, PLAYER_SIZE, PLAYER_SIZE)
				draw_flashlight(window, chaser_rect.center, aims.get(str(game_chaser_id), [0, -1]))
			for raw_id, position in state.items():
				rect = pygame.Rect(position[0] - camera_x, position[1] - camera_y, PLAYER_SIZE, PLAYER_SIZE)
				position_key = tuple(position)
				moving = previous_positions.get(raw_id) != position_key
				previous_positions[raw_id] = position_key
				draw_player(window, player_images, rect, now, moving)
				draw_hitbox(window, rect)
				label_color = RED_BRIGHT if int(raw_id) == game_chaser_id else (255, 255, 255)
				label = player_font.render(names.get(raw_id, str(int(raw_id) + 1)), True, label_color)
				window.blit(label, (rect.centerx - label.get_width() // 2, rect.top - label.get_height() - 6))
				if int(raw_id) != game_chaser_id and game_chaser_id is not None:
					draw_catch_indicator(window, (rect.centerx, rect.top - 16), float(catch_progress.get(raw_id, 0.0)))
				if int(raw_id) != game_chaser_id:
					draw_stamina_bar(window, rect, stamina.get(raw_id, DASH_COOLDOWN))
				draw_food_counter(window, rect, food_counts.get(raw_id, 0))
				action = food_actions.get(raw_id)
				feedback_state = food_feedback.get(raw_id)
				feedback = feedback_state[0] if feedback_state and feedback_state[1] > now else None
				draw_food_action(window, rect.center, action, feedback)
			status = font.render(f"{player_name} | ESC to disconnect", True, (220, 220, 220))
			window.blit(status, (15, 15))
			timer_text = font.render(f"TIME: {int(timer) // 60}:{int(timer) % 60:02d}", True, (255, 220, 145))
			window.blit(timer_text, (window.get_width() - timer_text.get_width() - 15, 15))
			food_text = font.render(f"NEST FOOD: {nest_food}", True, (255, 220, 145))
			window.blit(food_text, (15, 48))
			if str(player_id) in carried_food:
				carried_text = font.render("CARRYING FOOD - RETURN TO NEST", True, (151, 205, 116))
				window.blit(carried_text, (15, 81))
			pygame.display.flip()
			clock.tick(60)
	finally:
		connection.close()
		pygame.quit()
	return "menu" if return_to_menu else None
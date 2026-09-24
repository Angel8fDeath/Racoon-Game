import json
import socket
import threading

import pygame

from lobby import LobbyView, RED_BRIGHT
from GameUtils import (
	HEIGHT,
	PLAYER_SIZE,
	WORLD_HEIGHT,
	WORLD_WIDTH,
	WIDTH,
	camera_position,
	draw_background,
	keyboard_state,
	load_player_image,
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
	lobby_state = {"players": [0, player_id], "names": latest_names, "votes": {}, "selected_mode": "Survivors", "chaser_id": None}
	state_lock = threading.Lock()
	running = True
	game_started = False
	game_chaser_id = None

	def receive_states():
		nonlocal running, latest_state, latest_names, lobby_state, game_started, game_chaser_id
		try:
			for line in reader:
				message = json.loads(line)
				if message.get("type") == "state":
					with state_lock:
						latest_state = message["players"]
						latest_names = message.get("names", latest_names)
				elif message.get("type") == "lobby":
					with state_lock:
						lobby_state = message
						latest_names = message.get("names", latest_names)
				elif message.get("type") == "start_game":
					game_chaser_id = message.get("chaser_id")
					game_started = True
		except (OSError, ValueError):
			running = False

	threading.Thread(target=receive_states, daemon=True).start()
	window = setup_window(f"LAN Game - Player {player_id + 1}")
	clock = pygame.time.Clock()
	font = pygame.font.Font(None, 28)
	player_image = load_player_image(welcome["player_image"])
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
			for event in pygame.event.get():
				if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
					running = False
			try:
				send_message(connection, keyboard_state())
			except OSError:
				running = False
			with state_lock:
				state = latest_state.copy()
				names = latest_names.copy()
			local_position = state.get(str(player_id), [WORLD_WIDTH // 2, WORLD_HEIGHT // 2])
			camera_x, camera_y = camera_position(local_position)
			draw_background(window, camera_x, camera_y)
			for raw_id, position in state.items():
				rect = pygame.Rect(position[0] - camera_x, position[1] - camera_y, PLAYER_SIZE, PLAYER_SIZE)
				window.blit(player_image, rect)
				label_color = RED_BRIGHT if int(raw_id) == game_chaser_id else (255, 255, 255)
				label = font.render(names.get(raw_id, str(int(raw_id) + 1)), True, label_color)
				window.blit(label, (rect.x + 20, rect.y + 14))
			status = font.render(f"{player_name} | ESC to disconnect", True, (220, 220, 220))
			window.blit(status, (15, 15))
			pygame.display.flip()
			clock.tick(60)
	finally:
		connection.close()
		pygame.quit()
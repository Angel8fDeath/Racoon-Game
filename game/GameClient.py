import json
import socket
import threading

import pygame

from lobby import LobbyView
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


def client_game(address, port):
	connection = socket.create_connection((address, port))
	reader = connection.makefile("r", encoding="utf-8")
	welcome = json.loads(reader.readline())
	player_id = welcome["player_id"]
	latest_state = {}
	lobby_state = {"players": [0, player_id], "votes": {}, "selected_mode": "Survivors"}
	state_lock = threading.Lock()
	running = True
	game_started = False

	def receive_states():
		nonlocal running, latest_state, lobby_state, game_started
		try:
			for line in reader:
				message = json.loads(line)
				if message.get("type") == "state":
					with state_lock:
						latest_state = message["players"]
				elif message.get("type") == "lobby":
					with state_lock:
						lobby_state = message
				elif message.get("type") == "start_game":
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
			local_position = state.get(str(player_id), [WORLD_WIDTH // 2, WORLD_HEIGHT // 2])
			camera_x, camera_y = camera_position(local_position)
			draw_background(window, camera_x, camera_y)
			for raw_id, position in state.items():
				rect = pygame.Rect(position[0] - camera_x, position[1] - camera_y, PLAYER_SIZE, PLAYER_SIZE)
				window.blit(player_image, rect)
				label = font.render(str(int(raw_id) + 1), True, (255, 255, 255))
				window.blit(label, (rect.x + 20, rect.y + 14))
			status = font.render(f"Player {player_id + 1} | ESC to disconnect", True, (220, 220, 220))
			window.blit(status, (15, 15))
			pygame.display.flip()
			clock.tick(60)
	finally:
		connection.close()
		pygame.quit()
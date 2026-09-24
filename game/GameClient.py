import json
import socket
import threading

import pygame

from GameUtils import PLAYER_SIZE, keyboard_state, load_player_image, send_message, setup_window


def client_game(address, port):
	connection = socket.create_connection((address, port))
	reader = connection.makefile("r", encoding="utf-8")
	welcome = json.loads(reader.readline())
	player_id = welcome["player_id"]
	latest_state = {}
	state_lock = threading.Lock()
	running = True

	def receive_states():
		nonlocal running, latest_state
		try:
			for line in reader:
				message = json.loads(line)
				if message.get("type") == "state":
					with state_lock:
						latest_state = message["players"]
		except (OSError, ValueError):
			running = False

	threading.Thread(target=receive_states, daemon=True).start()
	window = setup_window(f"LAN Game - Player {player_id + 1}")
	clock = pygame.time.Clock()
	font = pygame.font.Font(None, 28)
	player_image = load_player_image(welcome["player_image"])
	try:
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
			window.fill((30, 35, 50))
			for raw_id, position in state.items():
				rect = pygame.Rect(position[0], position[1], PLAYER_SIZE, PLAYER_SIZE)
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
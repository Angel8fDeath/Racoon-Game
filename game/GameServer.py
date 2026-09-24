import base64
import json
import socket
import threading

import pygame

from lobby import MODE_OPTIONS
from lobby import LobbyView
from GameUtils import (
	MAX_PLAYERS,
	WORLD_HEIGHT,
	WORLD_WIDTH,
	PLAYER_IMAGE_PATH,
	PLAYER_SIZE,
	keyboard_state,
	camera_position,
	draw_background,
	load_player_image,
	move_player,
	send_message,
	setup_window,
)


class GameServer:
	def __init__(self, host, port):
		self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.listener.bind((host, port))
		self.listener.listen(MAX_PLAYERS - 1)
		self.listener.settimeout(0.5)
		self.lock = threading.Lock()
		self.clients = {}
		self.inputs = {}
		self.next_player_id = 1
		self.player_image_data = base64.b64encode(PLAYER_IMAGE_PATH.read_bytes()).decode("ascii")
		self.phase = "lobby"
		self.votes = {0: MODE_OPTIONS[0]}
		self.running = True

	def start(self):
		threading.Thread(target=self.accept_clients, daemon=True).start()

	def accept_clients(self):
		while self.running:
			try:
				connection, _ = self.listener.accept()
			except socket.timeout:
				continue
			except OSError:
				break

			with self.lock:
				if len(self.clients) >= MAX_PLAYERS - 1:
					connection.close()
					continue
				player_id = self.next_player_id
				self.next_player_id += 1
				self.clients[player_id] = connection
				self.inputs[player_id] = {}
				self.votes[player_id] = MODE_OPTIONS[0]
			try:
				send_message(connection, {
					"type": "welcome",
					"player_id": player_id,
					"player_image": self.player_image_data,
				})
				send_message(connection, {"type": "lobby", **self.get_lobby_state()})
			except OSError:
				self.remove_client(player_id, connection)
				continue
			threading.Thread(target=self.read_client, args=(player_id, connection), daemon=True).start()

	def read_client(self, player_id, connection):
		try:
			for line in connection.makefile("r", encoding="utf-8"):
				message = json.loads(line)
				if message.get("type") == "lobby_action":
					self.handle_lobby_action(player_id, message)
				elif message.get("type") == "input":
					with self.lock:
						self.inputs[player_id] = message
		except (OSError, ValueError):
			pass
		finally:
			self.remove_client(player_id, connection)

	def remove_client(self, player_id, connection):
		with self.lock:
			if self.clients.get(player_id) is connection:
				self.clients.pop(player_id, None)
				self.inputs.pop(player_id, None)
				self.votes.pop(player_id, None)
		try:
			connection.close()
		except OSError:
			pass

	def get_inputs(self):
		with self.lock:
			return {player_id: values.copy() for player_id, values in self.inputs.items()}

	def get_lobby_state(self):
		with self.lock:
			players = [0, *sorted(self.clients)]
			votes = {str(player_id): mode for player_id, mode in self.votes.items() if player_id in players}
			counts = {mode: sum(value == mode for value in votes.values()) for mode in MODE_OPTIONS}
			selected_mode = max(MODE_OPTIONS, key=lambda mode: (counts[mode], -MODE_OPTIONS.index(mode)))
			return {
				"players": players,
				"votes": votes,
				"selected_mode": selected_mode,
			}

	def handle_lobby_action(self, player_id, message):
		if self.phase != "lobby":
			return
		if message.get("action") == "vote_mode" and message.get("mode") in MODE_OPTIONS:
			with self.lock:
				if player_id in self.clients:
					self.votes[player_id] = message["mode"]
		elif message.get("action") == "start_game" and player_id == 0:
			self.start_game()

	def start_game(self):
		if self.phase != "lobby":
			return
		self.phase = "game"
		self.broadcast({"type": "start_game", "mode": self.get_lobby_state()["selected_mode"]})

	def broadcast(self, message):
		with self.lock:
			clients = list(self.clients.items())
		for player_id, connection in clients:
			try:
				send_message(connection, message)
			except OSError:
				self.remove_client(player_id, connection)

	def close(self):
		self.running = False
		self.listener.close()
		with self.lock:
			clients = list(self.clients.values())
		self.clients.clear()
		for connection in clients:
			connection.close()


def host_game(port):
	try:
		window = setup_window(f"LAN Game Host - port {port}")
	except RuntimeError:
		pygame.init()
		window = None
		print(f"Running headlessly on TCP port {port}. Connect desktop clients to this host.")
	server = GameServer("0.0.0.0", port)
	server.start()
	clock = pygame.time.Clock()
	font = pygame.font.Font(None, 28) if window else None
	player_image = load_player_image() if window else None
	players = {0: pygame.Rect(WORLD_WIDTH // 2, WORLD_HEIGHT // 2, PLAYER_SIZE, PLAYER_SIZE)}
	lobby = LobbyView(0, True) if window else None
	running = True
	try:
		if not window:
			server.start_game()
		while running and server.phase == "lobby" and window:
			if window:
				for event in pygame.event.get():
					if event.type == pygame.QUIT:
						running = False
						continue
					action = lobby.handle_event(event)
					if action == "quit":
						running = False
					elif isinstance(action, tuple) and action[0] == "vote_mode":
						with server.lock:
							server.votes[0] = action[1]
					elif action == "start_game":
						server.start_game()
				lobby_state = server.get_lobby_state()
				lobby.draw(window, lobby_state)
				pygame.display.flip()
			server.broadcast({"type": "lobby", **server.get_lobby_state()})
			clock.tick(30)

		while running:
			if window:
				for event in pygame.event.get():
					if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
						running = False

			if window:
				move_player(players[0], keyboard_state())
			inputs = server.get_inputs()
			with server.lock:
				connected_ids = set(server.clients)
			for player_id in connected_ids:
				players.setdefault(player_id, pygame.Rect(WORLD_WIDTH // 2 + player_id * 110, WORLD_HEIGHT // 2, PLAYER_SIZE, PLAYER_SIZE))
				move_player(players[player_id], inputs.get(player_id, {}))
			for player_id in set(players) - connected_ids - {0}:
				players.pop(player_id)

			state = {str(player_id): [rect.x, rect.y] for player_id, rect in players.items()}
			server.broadcast({"type": "state", "players": state})
			if window:
				camera_x, camera_y = camera_position([players[0].x, players[0].y])
				draw_background(window, camera_x, camera_y)
				for player_id, rect in players.items():
					screen_rect = rect.move(-camera_x, -camera_y)
					window.blit(player_image, screen_rect)
					label = font.render(str(player_id + 1), True, (255, 255, 255))
					window.blit(label, (screen_rect.x + 20, screen_rect.y + 14))
				status = font.render(f"Players: {len(players)}/{MAX_PLAYERS} | ESC to stop", True, (220, 220, 220))
				window.blit(status, (15, 15))
				pygame.display.flip()
			clock.tick(60)
	except KeyboardInterrupt:
		pass
	finally:
		server.close()
		pygame.quit()
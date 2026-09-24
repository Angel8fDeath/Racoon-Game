import base64
import json
import socket
import threading
import time

import pygame

from lobby import MODE_OPTIONS
from lobby import LobbyView
from GameUtils import (
	MAX_PLAYERS,
	DASH_COOLDOWN,
	DASH_BOOST_DURATION,
	WORLD_HEIGHT,
	WORLD_WIDTH,
	PLAYER_IMAGE_PATH,
	PLAYER_SIZE,
	keyboard_state,
	camera_position,
	draw_background,
	draw_catch_indicator,
	draw_flashlight,
	apply_dash_boost,
	dash_direction,
	draw_stamina_bar,
	is_inside_flashlight,
	load_player_image,
	move_player,
	send_message,
	setup_window,
)


def attempt_dash(player_id, controls, mode, chaser_id, caught_players, cooldowns, now):
	if mode != "Chase" or player_id == chaser_id or player_id in caught_players or not controls.get("dash"):
		return False
	if now < cooldowns.get(player_id, 0.0):
		return False
	direction = dash_direction(controls)
	if direction is None:
		return False
	cooldowns[player_id] = now + DASH_COOLDOWN
	return direction


class GameServer:
	def __init__(self, host, port, debug_mode=False):
		self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.listener.bind((host, port))
		self.listener.listen(MAX_PLAYERS - 1)
		self.listener.settimeout(0.5)
		self.lock = threading.Lock()
		self.clients = {}
		self.inputs = {}
		self.debug_mode = debug_mode
		self.virtual_player_id = 1 if debug_mode else None
		self.next_player_id = 2 if debug_mode else 1
		self.player_image_data = base64.b64encode(PLAYER_IMAGE_PATH.read_bytes()).decode("ascii")
		self.phase = "lobby"
		self.votes = {0: MODE_OPTIONS[0]}
		self.chaser_id = None
		self.names = {0: "HOST"}
		if self.virtual_player_id is not None:
			self.names[self.virtual_player_id] = "VM RACCOON"
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
				client_limit = MAX_PLAYERS - 2 if self.debug_mode else MAX_PLAYERS - 1
				if len(self.clients) >= client_limit:
					connection.close()
					continue
				player_id = self.next_player_id
				self.next_player_id += 1
				self.clients[player_id] = connection
				self.inputs[player_id] = {}
				self.votes[player_id] = MODE_OPTIONS[0]
				self.names[player_id] = f"PLAYER {player_id + 1}"
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
				if message.get("type") == "player_info":
					name = "".join(character for character in str(message.get("name", "")) if character.isprintable()).strip()[:20]
					with self.lock:
						if player_id in self.clients and name:
							self.names[player_id] = name
				elif message.get("type") == "lobby_action":
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
				self.names.pop(player_id, None)
		try:
			connection.close()
		except OSError:
			pass

	def get_inputs(self):
		with self.lock:
			return {player_id: values.copy() for player_id, values in self.inputs.items()}

	def get_player_names(self):
		with self.lock:
			return {str(player_id): name for player_id, name in self.names.items()}

	def get_lobby_state(self):
		with self.lock:
			players = [0]
			if self.virtual_player_id is not None:
				players.append(self.virtual_player_id)
			players.extend(sorted(self.clients))
			votes = {str(player_id): mode for player_id, mode in self.votes.items() if player_id in players}
			counts = {mode: sum(value == mode for value in votes.values()) for mode in MODE_OPTIONS}
			selected_mode = max(MODE_OPTIONS, key=lambda mode: (counts[mode], -MODE_OPTIONS.index(mode)))
			chaser_id = None
			if selected_mode == "Chase":
				chaser_id = self.chaser_id if self.chaser_id in players else 0
			return {
				"players": players,
				"virtual_player": self.virtual_player_id,
				"names": {str(player_id): name for player_id, name in self.names.items()},
				"votes": votes,
				"selected_mode": selected_mode,
				"chaser_id": chaser_id,
			}

	def handle_lobby_action(self, player_id, message):
		if self.phase != "lobby":
			return
		if message.get("action") == "vote_mode" and message.get("mode") in MODE_OPTIONS:
			with self.lock:
				if player_id in self.clients:
					self.votes[player_id] = message["mode"]
		elif message.get("action") == "select_chaser" and player_id == 0:
			with self.lock:
				players = [0]
				if self.virtual_player_id is not None:
					players.append(self.virtual_player_id)
				players.extend(self.clients)
				if message.get("player_id") in players:
					self.chaser_id = message["player_id"]
		elif message.get("action") == "start_game" and player_id == 0:
			self.start_game()

	def start_game(self):
		if self.phase != "lobby":
			return
		self.phase = "game"
		lobby_state = self.get_lobby_state()
		self.broadcast({"type": "start_game", "mode": lobby_state["selected_mode"], "chaser_id": lobby_state["chaser_id"]})

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


def host_game(port, debug_mode=False, player_name="HOST"):
	try:
		window = setup_window(f"LAN Game Host - port {port}")
	except RuntimeError:
		pygame.init()
		window = None
		print(f"Running headlessly on TCP port {port}. Connect desktop clients to this host.")
	server = GameServer("0.0.0.0", port, debug_mode=debug_mode)
	server.names[0] = player_name.strip()[:20] or "HOST"
	server.start()
	clock = pygame.time.Clock()
	font = pygame.font.Font(None, 28) if window else None
	player_image = load_player_image() if window else None
	players = {0: pygame.Rect(WORLD_WIDTH // 2, WORLD_HEIGHT // 2, PLAYER_SIZE, PLAYER_SIZE)}
	server.catch_progress = {}
	server.caught_players = set()
	server.dash_cooldowns = {}
	dash_stamina = {}
	last_stamina_update = time.monotonic()
	dash_boosts = {}
	last_movement_update = last_stamina_update
	if debug_mode:
		players[server.virtual_player_id] = pygame.Rect(WORLD_WIDTH // 2 + 110, WORLD_HEIGHT // 2, PLAYER_SIZE, PLAYER_SIZE)
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
					if event.type == pygame.VIDEORESIZE:
						window = pygame.display.set_mode(event.size, pygame.RESIZABLE)
						continue
					action = lobby.handle_event(event)
					if action == "quit":
						running = False
					elif isinstance(action, tuple) and action[0] == "vote_mode":
						with server.lock:
							server.votes[0] = action[1]
					elif isinstance(action, tuple) and action[0] == "select_chaser":
						server.handle_lobby_action(0, {"action": "select_chaser", "player_id": action[1]})
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

			host_input = keyboard_state() if window else {"aim": [0, -1]}
			inputs = server.get_inputs()
			lobby_state = server.get_lobby_state()
			chaser_id = lobby_state["chaser_id"]
			now = time.monotonic()
			movement_elapsed = min(0.05, now - last_movement_update)
			last_movement_update = now
			stamina_elapsed = min(0.2, now - last_stamina_update)
			last_stamina_update = now
			for player_id in list(dash_stamina):
				dash_stamina[player_id] = min(DASH_COOLDOWN, dash_stamina[player_id] + stamina_elapsed)
			successful_dashes = []
			with server.lock:
				connected_ids = set(server.clients)
			for player_id in connected_ids:
				players.setdefault(player_id, pygame.Rect(WORLD_WIDTH // 2 + player_id * 110, WORLD_HEIGHT // 2, PLAYER_SIZE, PLAYER_SIZE))
				if player_id not in server.caught_players:
					move_player(players[player_id], inputs.get(player_id, {}))
					if player_id in dash_boosts and not apply_dash_boost(players[player_id], dash_boosts[player_id], movement_elapsed):
						dash_boosts.pop(player_id)
					dash_direction_result = attempt_dash(player_id, inputs.get(player_id, {}), lobby_state["selected_mode"], chaser_id, server.caught_players, server.dash_cooldowns, now)
					if dash_direction_result:
						dash_boosts[player_id] = {"direction": dash_direction_result, "remaining": DASH_BOOST_DURATION}
						successful_dashes.append(player_id)
			if 0 not in server.caught_players:
				move_player(players[0], host_input)
				if 0 in dash_boosts and not apply_dash_boost(players[0], dash_boosts[0], movement_elapsed):
					dash_boosts.pop(0)
				dash_direction_result = attempt_dash(0, host_input, lobby_state["selected_mode"], chaser_id, server.caught_players, server.dash_cooldowns, now)
				if dash_direction_result:
					dash_boosts[0] = {"direction": dash_direction_result, "remaining": DASH_BOOST_DURATION}
					successful_dashes.append(0)
			reserved_players = {0}
			if server.virtual_player_id is not None:
				reserved_players.add(server.virtual_player_id)
			for player_id in set(players) - connected_ids - reserved_players:
				players.pop(player_id)
				server.dash_cooldowns.pop(player_id, None)
				dash_boosts.pop(player_id, None)
				dash_stamina.pop(player_id, None)
			for player_id in successful_dashes:
				dash_stamina[player_id] = 0.0
				if player_id != 0:
					server.broadcast({"type": "dash_success", "player_id": player_id, "cooldown": DASH_COOLDOWN})

			state = {str(player_id): [rect.x, rect.y] for player_id, rect in players.items()}
			aims = {"0": host_input.get("aim", [0, -1])}
			for player_id in connected_ids:
				aims[str(player_id)] = inputs.get(player_id, {}).get("aim", [0, -1])
			if lobby_state["selected_mode"] == "Chase" and chaser_id in players:
				chaser_center = players[chaser_id].center
				for player_id, player_rect in players.items():
					if player_id == chaser_id:
						continue
					if player_id in server.caught_players:
						server.catch_progress[player_id] = 1.0
						continue
					inside_flashlight = is_inside_flashlight(chaser_center, player_rect.center, aims.get(str(chaser_id), [0, -1]))
					progress = server.catch_progress.get(player_id, 0.0)
					progress += 1 / 90 if inside_flashlight else -1 / 900
					server.catch_progress[player_id] = max(0.0, min(1.0, progress))
					if server.catch_progress[player_id] >= 1.0:
						server.caught_players.add(player_id)
			else:
				server.catch_progress.clear()
				server.caught_players.clear()
			catch_progress = {str(player_id): progress for player_id, progress in server.catch_progress.items()}
			server.broadcast({"type": "state", "players": state, "names": server.get_player_names(), "chaser_id": chaser_id, "aims": aims, "catch_progress": catch_progress, "caught_players": [str(player_id) for player_id in server.caught_players]})
			if window:
				camera_x, camera_y = camera_position([players[0].x, players[0].y])
				names = server.get_player_names()
				draw_background(window, camera_x, camera_y)
				chaser_id = lobby_state["chaser_id"]
				if chaser_id in players:
					chaser_screen = players[chaser_id].move(-camera_x, -camera_y)
					draw_flashlight(window, chaser_screen.center, aims.get(str(chaser_id), [0, -1]))
				for player_id, rect in players.items():
					screen_rect = rect.move(-camera_x, -camera_y)
					window.blit(player_image, screen_rect)
					label_color = (239, 98, 68) if player_id == lobby_state["chaser_id"] else (255, 255, 255)
					label = font.render(names.get(str(player_id), str(player_id + 1)), True, label_color)
					window.blit(label, (screen_rect.x + 20, screen_rect.y + 14))
					if player_id != chaser_id and lobby_state["selected_mode"] == "Chase":
						draw_catch_indicator(window, (screen_rect.centerx, screen_rect.top - 16), server.catch_progress.get(player_id, 0.0))
					if player_id != chaser_id:
						draw_stamina_bar(window, screen_rect, dash_stamina.get(player_id, DASH_COOLDOWN))
				status = font.render(f"Players: {len(players)}/{MAX_PLAYERS} | ESC to stop", True, (220, 220, 220))
				window.blit(status, (15, 15))
				pygame.display.flip()
			clock.tick(60)
	except KeyboardInterrupt:
		pass
	finally:
		server.close()
		pygame.quit()
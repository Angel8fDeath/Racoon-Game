import argparse
import json
import socket
import threading

import pygame


WIDTH, HEIGHT = 800, 600
PLAYER_SIZE = 50
MAX_PLAYERS = 5
PORT = 5000
COLORS = [(80, 190, 120), (240, 120, 90), (100, 160, 240), (230, 200, 80), (190, 110, 220)]


def send_message(connection, message):
	connection.sendall((json.dumps(message) + "\n").encode("utf-8"))


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
			try:
				send_message(connection, {"type": "welcome", "player_id": player_id})
			except OSError:
				self.remove_client(player_id, connection)
				continue
			threading.Thread(target=self.read_client, args=(player_id, connection), daemon=True).start()

	def read_client(self, player_id, connection):
		try:
			for line in connection.makefile("r", encoding="utf-8"):
				message = json.loads(line)
				if message.get("type") == "input":
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
		try:
			connection.close()
		except OSError:
			pass

	def get_inputs(self):
		with self.lock:
			return {player_id: values.copy() for player_id, values in self.inputs.items()}

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


def setup_window(title):
	pygame.init()
	if pygame.display.get_driver() == "offscreen":
		pygame.quit()
		raise RuntimeError("No graphical display is available. Run the game on a local desktop.")
	window = pygame.display.set_mode((WIDTH, HEIGHT))
	pygame.display.set_caption(title)
	return window


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
	players = {0: pygame.Rect(375, 275, PLAYER_SIZE, PLAYER_SIZE)}
	running = True
	try:
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
				players.setdefault(player_id, pygame.Rect(75 + player_id * 110, 275, PLAYER_SIZE, PLAYER_SIZE))
				move_player(players[player_id], inputs.get(player_id, {}))
			for player_id in set(players) - connected_ids - {0}:
				players.pop(player_id)

			state = {str(player_id): [rect.x, rect.y] for player_id, rect in players.items()}
			server.broadcast({"type": "state", "players": state})
			if window:
				window.fill((30, 35, 50))
				for player_id, rect in players.items():
					pygame.draw.rect(window, COLORS[player_id % len(COLORS)], rect)
					label = font.render(str(player_id + 1), True, (255, 255, 255))
					window.blit(label, (rect.x + 20, rect.y + 14))
				status = font.render(f"Players: {len(players)}/{MAX_PLAYERS} | ESC to stop", True, (220, 220, 220))
				window.blit(status, (15, 15))
				pygame.display.flip()
			clock.tick(60)
	except KeyboardInterrupt:
		pass
	finally:
		server.close()
		pygame.quit()


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
				pygame.draw.rect(window, COLORS[int(raw_id) % len(COLORS)], rect)
				label = font.render(str(int(raw_id) + 1), True, (255, 255, 255))
				window.blit(label, (rect.x + 20, rect.y + 14))
			status = font.render(f"Player {player_id + 1} | ESC to disconnect", True, (220, 220, 220))
			window.blit(status, (15, 15))
			pygame.display.flip()
			clock.tick(60)
	finally:
		connection.close()
		pygame.quit()


def main():
	parser = argparse.ArgumentParser(description="A small LAN multiplayer Pygame demo")
	mode = parser.add_mutually_exclusive_group(required=True)
	mode.add_argument("--host", action="store_true", help="start the authoritative LAN server")
	mode.add_argument("--connect", metavar="ADDRESS", help="connect to a host on the LAN")
	parser.add_argument("--port", type=int, default=PORT, help=f"TCP port (default: {PORT})")
	args = parser.parse_args()
	if args.host:
		host_game(args.port)
	else:
		client_game(args.connect, args.port)


if __name__ == "__main__":
	main()

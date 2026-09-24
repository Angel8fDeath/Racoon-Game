import pygame

from GameClient import client_game
from GameServer import host_game


WINDOW_WIDTH, WINDOW_HEIGHT = 900, 600
BG_COLOR = (18, 22, 30)
PANEL_COLOR = (33, 40, 54)
BUTTON_COLOR = (84, 148, 255)
BUTTON_ALT = (100, 175, 120)
TEXT_COLOR = (240, 240, 240)
SUBTEXT_COLOR = (170, 180, 200)
BORDER_COLOR = (100, 120, 150)
ERROR_COLOR = (255, 110, 110)


def input_box(screen, font, rect, label, text, active):
	pygame.draw.rect(screen, (18, 27, 40) if active else PANEL_COLOR, rect, border_radius=10)
	pygame.draw.rect(screen, BORDER_COLOR if active else (70, 82, 100), rect, 2, border_radius=10)
	label_surface = font.render(label, True, SUBTEXT_COLOR)
	screen.blit(label_surface, (rect.x, rect.y - 26))
	text_surface = font.render(text, True, TEXT_COLOR)
	screen.blit(text_surface, (rect.x + 14, rect.y + 12))


def draw_button(screen, font, rect, label, selected=False):
	color = BUTTON_ALT if selected else BUTTON_COLOR
	pygame.draw.rect(screen, color, rect, border_radius=12)
	pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=12)
	text_surface = font.render(label, True, TEXT_COLOR)
	screen.blit(text_surface, (rect.centerx - text_surface.get_width() / 2, rect.centery - text_surface.get_height() / 2))


def handle_text_edit(text, key, unicode_char, max_length=32):
	if key in (pygame.K_BACKSPACE, pygame.K_DELETE):
		return text[:-1]
	if key in (pygame.K_TAB, pygame.K_RETURN, pygame.K_ESCAPE):
		return text
	if unicode_char and unicode_char.isprintable() and len(text) < max_length:
		return text + unicode_char
	return text


def launch_host(port_value):
	try:
		port = int(port_value or 5000)
	except ValueError:
		raise ValueError("Port must be a number.")
	host_game(port)


def launch_join(ip_value, port_value):
	try:
		port = int(port_value or 5000)
	except ValueError:
		raise ValueError("Port must be a number.")
	address = ip_value.strip() or "127.0.0.1"
	client_game(address, port)


def run_start_menu_window():
	pygame.init()
	screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
	pygame.display.set_caption("Racoon Game")
	clock = pygame.time.Clock()
	font = pygame.font.Font(None, 36)
	small_font = pygame.font.Font(None, 26)

	mode = "host"
	ip_text = "127.0.0.1"
	port_text = "5000"
	active_field = "port"
	status_text = ""

	host_button = pygame.Rect(120, 160, 260, 90)
	join_button = pygame.Rect(520, 160, 260, 90)
	ip_rect = pygame.Rect(180, 340, 540, 60)
	port_rect = pygame.Rect(180, 430, 540, 60)
	start_rect = pygame.Rect(320, 520, 260, 60)

	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				return
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					pygame.quit()
					return
				if event.key == pygame.K_TAB:
					if mode == "join":
						active_field = "ip" if active_field == "port" else "port"
					else:
						active_field = "port"
					status_text = ""
					continue
				if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
					try:
						if mode == "host":
							pygame.quit()
							launch_host(port_text)
						else:
							pygame.quit()
							launch_join(ip_text, port_text)
						return
					except ValueError as exc:
						status_text = str(exc)
					continue
				if mode == "join" and active_field == "ip":
					ip_text = handle_text_edit(ip_text, event.key, event.unicode, max_length=32)
				elif active_field == "port":
					port_text = handle_text_edit(port_text, event.key, event.unicode, max_length=5)
				status_text = ""
			elif event.type == pygame.MOUSEBUTTONDOWN:
				mouse_pos = pygame.mouse.get_pos()
				if host_button.collidepoint(mouse_pos):
					mode = "host"
					active_field = "port"
					status_text = ""
				if join_button.collidepoint(mouse_pos):
					mode = "join"
					active_field = "ip"
					status_text = ""
				if mode == "join" and ip_rect.collidepoint(mouse_pos):
					active_field = "ip"
				if port_rect.collidepoint(mouse_pos):
					active_field = "port"
				if start_rect.collidepoint(mouse_pos):
					try:
						pygame.quit()
						if mode == "host":
							launch_host(port_text)
						else:
							launch_join(ip_text, port_text)
						return
					except ValueError as exc:
						status_text = str(exc)

		screen.fill(BG_COLOR)
		title = font.render("Racoon Game", True, TEXT_COLOR)
		screen.blit(title, (WINDOW_WIDTH / 2 - title.get_width() / 2, 40))

		draw_button(screen, font, host_button, "Host Game", selected=(mode == "host"))
		draw_button(screen, font, join_button, "Join Game", selected=(mode == "join"))

		input_box(screen, font, ip_rect, "Host IP", ip_text, active_field == "ip" and mode == "join")
		input_box(screen, font, port_rect, "Port", port_text, active_field == "port")
		draw_button(screen, font, start_rect, "Start Host" if mode == "host" else "Connect", selected=True)

		helper = "Type the host computer IP address to connect." if mode == "join" else "Open the room and wait for players to connect."
		helper_surface = small_font.render(helper, True, SUBTEXT_COLOR)
		screen.blit(helper_surface, (WINDOW_WIDTH / 2 - helper_surface.get_width() / 2, 300))

		if status_text:
			status_surface = small_font.render(status_text, True, ERROR_COLOR)
			screen.blit(status_surface, (WINDOW_WIDTH / 2 - status_surface.get_width() / 2, 500))

		pygame.display.flip()
		clock.tick(60)
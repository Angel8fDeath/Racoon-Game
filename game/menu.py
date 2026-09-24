import pygame

from GameClient import client_game
from GameServer import host_game
from lobby import AMBER, BACKGROUND, MUTED, PANEL, PANEL_LIGHT, RED, RED_BRIGHT, TEXT


WINDOW_WIDTH, WINDOW_HEIGHT = 1200, 900
ERROR_COLOR = (239, 98, 68)


def input_box(screen, font, rect, label, text, active, enabled=True):
	fill = PANEL if enabled else (24, 26, 31)
	border = RED_BRIGHT if active else (65, 68, 76)
	text_color = TEXT if enabled else MUTED
	pygame.draw.rect(screen, fill, rect)
	pygame.draw.rect(screen, border, rect, 2)
	label_surface = font.render(label, True, MUTED if enabled else (91, 93, 98))
	screen.blit(label_surface, (rect.x, rect.y - 25))
	text_surface = font.render(text, True, text_color)
	screen.blit(text_surface, (rect.x + 16, rect.y + 16))


def draw_button(screen, font, rect, label, selected=False):
	color = (71, 39, 38) if selected else PANEL
	border = RED_BRIGHT if selected else (65, 68, 76)
	pygame.draw.rect(screen, color, rect)
	pygame.draw.rect(screen, border, rect, 2)
	text_surface = font.render(label, True, TEXT)
	screen.blit(text_surface, (rect.centerx - text_surface.get_width() / 2, rect.centery - text_surface.get_height() / 2))


def draw_background_details(screen):
	for y in range(0, WINDOW_HEIGHT, 48):
		pygame.draw.line(screen, (24, 27, 34), (0, y), (WINDOW_WIDTH, y), 1)
	pygame.draw.polygon(screen, (30, 25, 28), [(0, 0), (300, 0), (0, 300)])
	pygame.draw.polygon(screen, (35, 25, 25), [(1200, 900), (865, 900), (1200, 525)])


def handle_text_edit(text, key, unicode_char, max_length=32):
	if key in (pygame.K_BACKSPACE, pygame.K_DELETE):
		return text[:-1]
	if key in (pygame.K_TAB, pygame.K_RETURN, pygame.K_ESCAPE):
		return text
	if unicode_char and unicode_char.isprintable() and len(text) < max_length:
		return text + unicode_char
	return text


def launch_host(port_value, debug_mode=False, player_name="HOST"):
	try:
		port = int(port_value or 5000)
	except ValueError:
		raise ValueError("Port must be a number.")
	return host_game(port, debug_mode=debug_mode, player_name=player_name)


def launch_join(ip_value, port_value, player_name="Player"):
	try:
		port = int(port_value or 5000)
	except ValueError:
		raise ValueError("Port must be a number.")
	address = ip_value.strip() or "127.0.0.1"
	return client_game(address, port, player_name=player_name)


def _run_start_menu_window():
	pygame.init()
	screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
	pygame.display.set_caption("Racoon Game")
	clock = pygame.time.Clock()
	title_font = pygame.font.Font(None, 63)
	heading_font = pygame.font.Font(None, 45)
	body_font = pygame.font.Font(None, 36)
	small_font = pygame.font.Font(None, 30)

	mode = "host"
	name_text = "HOST"
	ip_text = "127.0.0.1"
	port_text = "5000"
	active_field = "name"
	status_text = ""
	debug_mode = False

	host_button = pygame.Rect(107, 218, 467, 129)
	join_button = pygame.Rect(627, 218, 467, 129)
	name_rect = pygame.Rect(133, 480, 934, 75)
	ip_rect = pygame.Rect(133, 585, 934, 75)
	port_rect = pygame.Rect(133, 690, 934, 75)
	debug_rect = pygame.Rect(133, 375, 934, 68)
	start_rect = pygame.Rect(380, 775, 440, 81)

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
					fields = ["name", "ip", "port"] if mode == "join" else ["name", "port"]
					active_field = fields[(fields.index(active_field) + 1) % len(fields)]
					status_text = ""
					continue
				if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
					try:
						if mode == "host":
							pygame.quit()
							result = launch_host(port_text, debug_mode, name_text)
						else:
							pygame.quit()
							result = launch_join(ip_text, port_text, name_text)
						if result == "menu":
							return "menu"
						return
					except ValueError as exc:
						status_text = str(exc)
					continue
				if active_field == "name":
					name_text = handle_text_edit(name_text, event.key, event.unicode, max_length=20)
				elif mode == "join" and active_field == "ip":
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
					if name_text == "HOST":
						name_text = "Player"
					active_field = "ip"
					status_text = ""
				if mode == "join" and ip_rect.collidepoint(mouse_pos):
					active_field = "ip"
				if name_rect.collidepoint(mouse_pos):
					active_field = "name"
				if port_rect.collidepoint(mouse_pos):
					active_field = "port"
				if mode == "host" and debug_rect.collidepoint(mouse_pos):
					debug_mode = not debug_mode
				if start_rect.collidepoint(mouse_pos):
					try:
						pygame.quit()
						if mode == "host":
							result = launch_host(port_text, debug_mode, name_text)
						else:
							result = launch_join(ip_text, port_text, name_text)
						if result == "menu":
							return "menu"
						return
					except ValueError as exc:
						status_text = str(exc)

		screen.fill(BACKGROUND)
		draw_background_details(screen)
		pygame.draw.rect(screen, RED_BRIGHT, (51, 53, 11, 81))
		title = title_font.render("RACCOON GAME", True, TEXT)
		screen.blit(title, (86, 51))
		subtitle = small_font.render("CHOOSE YOUR DEPLOYMENT CHANNEL", True, AMBER)
		screen.blit(subtitle, (89, 110))

		mode_heading = heading_font.render("DEPLOYMENT TYPE", True, TEXT)
		screen.blit(mode_heading, (107, 168))
		draw_button(screen, body_font, host_button, "HOST GAME", selected=(mode == "host"))
		draw_button(screen, body_font, join_button, "JOIN GAME", selected=(mode == "join"))
		draw_button(screen, small_font, debug_rect, "DEBUG MODE // ADD STATIONARY VM RACCOON", selected=debug_mode and mode == "host")

		input_box(screen, body_font, name_rect, "PLAYER NAME", name_text, active_field == "name", enabled=True)
		input_box(screen, body_font, ip_rect, "HOST IP", ip_text, active_field == "ip" and mode == "join", enabled=mode == "join")
		input_box(screen, body_font, port_rect, "PORT", port_text, active_field == "port", enabled=True)
		draw_button(screen, body_font, start_rect, "START HOST" if mode == "host" else "CONNECT", selected=True)

		if status_text:
			status_surface = small_font.render(status_text, True, ERROR_COLOR)
			screen.blit(status_surface, (WINDOW_WIDTH / 2 - status_surface.get_width() / 2, 870))
		else:
			status_surface = small_font.render("ESC TO ABORT  //  TAB TO CYCLE INPUTS", True, MUTED)
			screen.blit(status_surface, (WINDOW_WIDTH / 2 - status_surface.get_width() / 2, 870))

		pygame.display.flip()
		clock.tick(60)


def run_start_menu_window():
	while _run_start_menu_window() == "menu":
		pass
import pygame

from GameClient import client_game
from GameServer import host_game
from lobby import AMBER, BACKGROUND, MUTED, PANEL, PANEL_LIGHT, RED, RED_BRIGHT, TEXT


WINDOW_WIDTH, WINDOW_HEIGHT = 900, 600
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
	pygame.draw.polygon(screen, (35, 25, 25), [(900, 600), (650, 600), (900, 350)])


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
	title_font = pygame.font.Font(None, 42)
	heading_font = pygame.font.Font(None, 30)
	body_font = pygame.font.Font(None, 24)
	small_font = pygame.font.Font(None, 20)

	mode = "host"
	ip_text = "127.0.0.1"
	port_text = "5000"
	active_field = "port"
	status_text = ""

	host_button = pygame.Rect(80, 145, 350, 86)
	join_button = pygame.Rect(470, 145, 350, 86)
	ip_rect = pygame.Rect(100, 315, 700, 58)
	port_rect = pygame.Rect(100, 410, 700, 58)
	start_rect = pygame.Rect(285, 495, 330, 54)

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

		screen.fill(BACKGROUND)
		draw_background_details(screen)
		pygame.draw.rect(screen, RED_BRIGHT, (34, 35, 7, 54))
		title = title_font.render("DROP POD // RACCOON GAME", True, TEXT)
		screen.blit(title, (57, 34))
		subtitle = small_font.render("CHOOSE YOUR DEPLOYMENT CHANNEL", True, AMBER)
		screen.blit(subtitle, (59, 73))

		mode_heading = heading_font.render("DEPLOYMENT TYPE", True, TEXT)
		screen.blit(mode_heading, (80, 112))
		draw_button(screen, body_font, host_button, "HOST GAME", selected=(mode == "host"))
		draw_button(screen, body_font, join_button, "JOIN GAME", selected=(mode == "join"))

		input_box(screen, body_font, ip_rect, "HOST IP", ip_text, active_field == "ip" and mode == "join", enabled=mode == "join")
		input_box(screen, body_font, port_rect, "PORT", port_text, active_field == "port", enabled=True)
		draw_button(screen, body_font, start_rect, "START HOST" if mode == "host" else "CONNECT", selected=True)

		helper = "ENTER THE HOST ADDRESS TO JOIN THE DROP." if mode == "join" else "OPEN A ROOM AND WAIT FOR YOUR SQUAD TO ARRIVE."
		helper_surface = small_font.render(helper, True, MUTED)
		screen.blit(helper_surface, (WINDOW_WIDTH / 2 - helper_surface.get_width() / 2, 270))

		if status_text:
			status_surface = small_font.render(status_text, True, ERROR_COLOR)
			screen.blit(status_surface, (WINDOW_WIDTH / 2 - status_surface.get_width() / 2, 575))
		else:
			status_surface = small_font.render("ESC TO ABORT  //  TAB TO CYCLE INPUTS", True, MUTED)
			screen.blit(status_surface, (WINDOW_WIDTH / 2 - status_surface.get_width() / 2, 575))

		pygame.display.flip()
		clock.tick(60)
import pygame


MODE_OPTIONS = ("Survivors", "FoodFind", "Chase")
SKIN_OPTIONS = ("Raccoon", "Coming Soon", "Coming Soon")

BACKGROUND = (15, 17, 22)
PANEL = (28, 31, 39)
PANEL_LIGHT = (42, 45, 54)
RED = (202, 68, 56)
RED_BRIGHT = (239, 98, 68)
AMBER = (237, 177, 76)
TEXT = (241, 235, 220)
MUTED = (153, 157, 166)
DISABLED = (91, 93, 98)
BASE_WIDTH, BASE_HEIGHT = 800, 600


class LobbyView:
	def __init__(self, player_id, is_host):
		self.player_id = player_id
		self.is_host = is_host
		self.ui_scale = 1.5
		self.offset = (0, 0)
		self.title_font = pygame.font.Font(None, 63)
		self.heading_font = pygame.font.Font(None, 45)
		self.body_font = pygame.font.Font(None, 36)
		self.small_font = pygame.font.Font(None, 30)
		self.mode_rects = []
		self.skin_rects = []
		self.start_rect = pygame.Rect(0, 0, 0, 0)
		self._update_layout(pygame.display.get_surface())

	def _update_layout(self, screen):
		if screen is not None:
			self.ui_scale = min(screen.get_width() / BASE_WIDTH, screen.get_height() / BASE_HEIGHT)
			scaled_width = round(BASE_WIDTH * self.ui_scale)
			scaled_height = round(BASE_HEIGHT * self.ui_scale)
			self.offset = ((screen.get_width() - scaled_width) // 2, (screen.get_height() - scaled_height) // 2)
		scale = self.ui_scale
		self.title_font = pygame.font.Font(None, max(1, round(42 * scale)))
		self.heading_font = pygame.font.Font(None, max(1, round(30 * scale)))
		self.body_font = pygame.font.Font(None, max(1, round(24 * scale)))
		self.small_font = pygame.font.Font(None, max(1, round(20 * scale)))
		self.mode_rects = [self._rect(250, 172 + index * 82, 330, 66) for index in range(len(MODE_OPTIONS))]
		self.skin_rects = [self._rect(610, 172 + index * 82, 155, 66) for index in range(len(SKIN_OPTIONS))]
		self.start_rect = self._rect(250, 488, 330, 54)

	def _rect(self, x, y, width, height):
		return pygame.Rect(
			self.offset[0] + round(x * self.ui_scale),
			self.offset[1] + round(y * self.ui_scale),
			round(width * self.ui_scale),
			round(height * self.ui_scale),
		)

	def _pos(self, x, y):
		return self.offset[0] + round(x * self.ui_scale), self.offset[1] + round(y * self.ui_scale)

	def handle_event(self, event):
		if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
			return "quit"
		if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
			return None
		self._update_layout(pygame.display.get_surface())
		mouse_pos = event.pos
		for index, rect in enumerate(self.mode_rects):
			if rect.collidepoint(mouse_pos):
				return ("vote_mode", MODE_OPTIONS[index])
		if self.is_host and self.start_rect.collidepoint(mouse_pos):
			return "start_game"
		return None

	def draw(self, screen, lobby_state):
		self._update_layout(screen)
		screen.fill(BACKGROUND)
		self._draw_background_details(screen)
		self._draw_header(screen, lobby_state)
		self._draw_roster(screen, lobby_state)
		self._draw_modes(screen, lobby_state)
		##self._draw_skins(screen)
		self._draw_footer(screen, lobby_state)

	def _draw_background_details(self, screen):
		grid_step = max(1, round(48 * self.ui_scale))
		for y in range(self.offset[1], screen.get_height(), grid_step):
			pygame.draw.line(screen, (24, 27, 34), (0, y), (screen.get_width(), y), 1)
		pygame.draw.polygon(screen, (30, 25, 28), [self._pos(0, 0), self._pos(240, 0), self._pos(0, 240)])
		pygame.draw.polygon(screen, (35, 25, 25), [self._pos(800, 600), self._pos(590, 600), self._pos(800, 390)])

	def _draw_header(self, screen, lobby_state):
		accent = self._rect(34, 35, 7, 54)
		pygame.draw.rect(screen, RED_BRIGHT, accent)
		title = self.title_font.render("DROP POD // LOBBY", True, TEXT)
		screen.blit(title, self._pos(57, 34))
		subtitle = self.small_font.render("ASSEMBLE YOUR SQUAD BEFORE THE RAIN BEGINS", True, AMBER)
		screen.blit(subtitle, self._pos(59, 73))
		count = len(lobby_state.get("players", []))
		count_text = self.body_font.render(f"{count}/5 OPERATORS READY", True, TEXT)
		count_position = self._pos(800, 50)
		screen.blit(count_text, (count_position[0] - count_text.get_width(), count_position[1]))

	def _draw_roster(self, screen, lobby_state):
		panel = self._rect(34, 128, 190, 372)
		self._panel(screen, panel)
		heading = self.heading_font.render("SQUAD", True, TEXT)
		screen.blit(heading, self._pos(52, 146))
		players = lobby_state.get("players", [])
		for index, player_id in enumerate(players):
			row = self._rect(50, 194 + index * 55, 158, 40)
			pygame.draw.rect(screen, RED if player_id == self.player_id else PANEL_LIGHT, row)
			name = "HOST" if player_id == 0 else f"PLAYER {player_id + 1}"
			if player_id == self.player_id:
				name += "  (YOU)"
			text = self.small_font.render(name, True, TEXT)
			screen.blit(text, self._pos(60, 205 + index * 55))
		if not players:
			text = self.small_font.render("SEARCHING...", True, MUTED)
			screen.blit(text, self._pos(52, 198))

	def _draw_modes(self, screen, lobby_state):
		heading = self.heading_font.render("SELECT PLAYMODE", True, TEXT)
		screen.blit(heading, self._pos(250, 128))
		votes = lobby_state.get("votes", {})
		selected = lobby_state.get("selected_mode", MODE_OPTIONS[0])
		for index, (rect, mode) in enumerate(zip(self.mode_rects, MODE_OPTIONS)):
			is_selected = mode == selected
			self._panel(screen, rect, selected=is_selected)
			number = self.heading_font.render(f"0{index + 1}", True, AMBER if is_selected else MUTED)
			screen.blit(number, self._pos(266, 190 + index * 82))
			label = self.body_font.render(mode.upper(), True, TEXT)
			screen.blit(label, self._pos(320, 184 + index * 82))
			vote_count = sum(1 for value in votes.values() if value == mode)
			vote_label = self.small_font.render(f"{vote_count} VOTE" if vote_count == 1 else f"{vote_count} VOTES", True, AMBER if is_selected else MUTED)
			screen.blit(vote_label, self._pos(320, 210 + index * 82))

	def _draw_skins(self, screen, lobby_state):
		heading = self.heading_font.render("OPERATOR SKINS", True, DISABLED)
		screen.blit(heading, self._pos(610, 128))
		for rect, skin in zip(self.skin_rects, SKIN_OPTIONS):
			self._panel(screen, rect, disabled=True)
			label = self.small_font.render(skin.upper(), True, DISABLED)
			screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))

	def _draw_footer(self, screen, lobby_state):
		if self.is_host:
			self._panel(screen, self.start_rect, selected=True)
			label = self.body_font.render("START EXPEDITION", True, TEXT)
			screen.blit(label, (self.start_rect.centerx - label.get_width() // 2, self.start_rect.centery - label.get_height() // 2))
		else:
			label = self.body_font.render("WAITING FOR HOST TO DEPLOY...", True, AMBER)
			screen.blit(label, self._pos(250, 506))
		selected = lobby_state.get("selected_mode", MODE_OPTIONS[0])
		status = self.small_font.render(f"CURRENT PLAYMODE: {selected.upper()}  //  VOTE TO CHANGE THE DROP", True, MUTED)
		screen.blit(status, self._pos(34, 552))

	def _panel(self, screen, rect, selected=False, disabled=False):
		fill = (71, 39, 38) if selected else PANEL
		border = RED_BRIGHT if selected else (65, 68, 76)
		if disabled:
			fill = (24, 26, 31)
			border = (53, 55, 61)
		pygame.draw.rect(screen, fill, rect)
		pygame.draw.rect(screen, border, rect, 2)

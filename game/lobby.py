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


class LobbyView:
	def __init__(self, player_id, is_host):
		self.player_id = player_id
		self.is_host = is_host
		self.title_font = pygame.font.Font(None, 42)
		self.heading_font = pygame.font.Font(None, 30)
		self.body_font = pygame.font.Font(None, 24)
		self.small_font = pygame.font.Font(None, 20)
		self.mode_rects = [pygame.Rect(250, 172 + index * 82, 330, 66) for index in range(len(MODE_OPTIONS))]
		self.skin_rects = [pygame.Rect(610, 172 + index * 82, 155, 66) for index in range(len(SKIN_OPTIONS))]
		self.start_rect = pygame.Rect(250, 488, 330, 54)

	def handle_event(self, event):
		if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
			return "quit"
		if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
			return None
		for index, rect in enumerate(self.mode_rects):
			if rect.collidepoint(event.pos):
				return ("vote_mode", MODE_OPTIONS[index])
		if self.is_host and self.start_rect.collidepoint(event.pos):
			return "start_game"
		return None

	def draw(self, screen, lobby_state):
		screen.fill(BACKGROUND)
		self._draw_background_details(screen)
		self._draw_header(screen, lobby_state)
		self._draw_roster(screen, lobby_state)
		self._draw_modes(screen, lobby_state)
		##self._draw_skins(screen)
		self._draw_footer(screen, lobby_state)

	def _draw_background_details(self, screen):
		for y in range(0, screen.get_height(), 48):
			pygame.draw.line(screen, (24, 27, 34), (0, y), (screen.get_width(), y), 1)
		pygame.draw.polygon(screen, (30, 25, 28), [(0, 0), (240, 0), (0, 240)])
		pygame.draw.polygon(screen, (35, 25, 25), [(800, 600), (590, 600), (800, 390)])

	def _draw_header(self, screen, lobby_state):
		accent = pygame.Rect(34, 35, 7, 54)
		pygame.draw.rect(screen, RED_BRIGHT, accent)
		title = self.title_font.render("DROP POD // LOBBY", True, TEXT)
		screen.blit(title, (57, 34))
		subtitle = self.small_font.render("ASSEMBLE YOUR SQUAD BEFORE THE RAIN BEGINS", True, AMBER)
		screen.blit(subtitle, (59, 73))
		count = len(lobby_state.get("players", []))
		count_text = self.body_font.render(f"{count}/5 OPERATORS READY", True, TEXT)
		screen.blit(count_text, (screen.get_width() - count_text.get_width() - 35, 50))

	def _draw_roster(self, screen, lobby_state):
		panel = pygame.Rect(34, 128, 190, 372)
		self._panel(screen, panel)
		heading = self.heading_font.render("SQUAD", True, TEXT)
		screen.blit(heading, (panel.x + 18, panel.y + 18))
		players = lobby_state.get("players", [])
		for index, player_id in enumerate(players):
			y = panel.y + 66 + index * 55
			pygame.draw.rect(screen, RED if player_id == self.player_id else PANEL_LIGHT, (panel.x + 16, y, 158, 40))
			name = "HOST" if player_id == 0 else f"PLAYER {player_id + 1}"
			if player_id == self.player_id:
				name += "  (YOU)"
			text = self.small_font.render(name, True, TEXT)
			screen.blit(text, (panel.x + 26, y + 11))
		if not players:
			text = self.small_font.render("SEARCHING...", True, MUTED)
			screen.blit(text, (panel.x + 18, panel.y + 70))

	def _draw_modes(self, screen, lobby_state):
		heading = self.heading_font.render("SELECT PLAYMODE", True, TEXT)
		screen.blit(heading, (250, 128))
		votes = lobby_state.get("votes", {})
		selected = lobby_state.get("selected_mode", MODE_OPTIONS[0])
		for index, (rect, mode) in enumerate(zip(self.mode_rects, MODE_OPTIONS)):
			is_selected = mode == selected
			self._panel(screen, rect, selected=is_selected)
			number = self.heading_font.render(f"0{index + 1}", True, AMBER if is_selected else MUTED)
			screen.blit(number, (rect.x + 16, rect.y + 18))
			label = self.body_font.render(mode.upper(), True, TEXT)
			screen.blit(label, (rect.x + 70, rect.y + 12))
			vote_count = sum(1 for value in votes.values() if value == mode)
			vote_label = self.small_font.render(f"{vote_count} VOTE" if vote_count == 1 else f"{vote_count} VOTES", True, AMBER if is_selected else MUTED)
			screen.blit(vote_label, (rect.x + 70, rect.y + 38))

	def _draw_skins(self, screen, lobby_state):
		heading = self.heading_font.render("OPERATOR SKINS", True, DISABLED)
		screen.blit(heading, (610, 128))
		for rect, skin in zip(self.skin_rects, SKIN_OPTIONS):
			self._panel(screen, rect, disabled=True)
			label = self.small_font.render(skin.upper(), True, DISABLED)
			screen.blit(label, (rect.centerx - label.get_width() / 2, rect.centery - label.get_height() / 2))

	def _draw_footer(self, screen, lobby_state):
		if self.is_host:
			self._panel(screen, self.start_rect, selected=True)
			label = self.body_font.render("START EXPEDITION", True, TEXT)
			screen.blit(label, (self.start_rect.centerx - label.get_width() / 2, self.start_rect.centery - label.get_height() / 2))
		else:
			label = self.body_font.render("WAITING FOR HOST TO DEPLOY...", True, AMBER)
			screen.blit(label, (250, 506))
		selected = lobby_state.get("selected_mode", MODE_OPTIONS[0])
		status = self.small_font.render(f"CURRENT PLAYMODE: {selected.upper()}  //  VOTE TO CHANGE THE DROP", True, MUTED)
		screen.blit(status, (34, 552))

	def _panel(self, screen, rect, selected=False, disabled=False):
		fill = (71, 39, 38) if selected else PANEL
		border = RED_BRIGHT if selected else (65, 68, 76)
		if disabled:
			fill = (24, 26, 31)
			border = (53, 55, 61)
		pygame.draw.rect(screen, fill, rect)
		pygame.draw.rect(screen, border, rect, 2)

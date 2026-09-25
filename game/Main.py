import argparse

import pygame

from GameClient import client_game
from GameServer import host_game
from intro import run_intro
from menu import run_start_menu_window


INTRO_WIDTH, INTRO_HEIGHT = 1200, 900
SKIP_INTRO = True


def main():
	parser = argparse.ArgumentParser(description="A small LAN multiplayer Pygame demo")
	mode = parser.add_mutually_exclusive_group()
	mode.add_argument("--host", action="store_true", help="start the authoritative LAN server")
	mode.add_argument("--connect", metavar="ADDRESS", help="connect to a host on the LAN")
	parser.add_argument("--port", type=int, default=5000, help="TCP port (default: 5000)")
	args = parser.parse_args()
	if args.host:
		host_game(args.port)
	elif args.connect:
		client_game(args.connect, args.port)
	else:
		if not SKIP_INTRO:
			pygame.init()
			intro_window = pygame.display.set_mode((INTRO_WIDTH, INTRO_HEIGHT))
			pygame.display.set_caption("Raccoon Game Intro")
			try:
				if not run_intro(intro_window):
					return
			finally:
				pygame.quit()
		run_start_menu_window()


if __name__ == "__main__":
	main()
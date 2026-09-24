import argparse

from GameClient import client_game
from GameServer import host_game
from menu import run_start_menu_window


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
		run_start_menu_window()


if __name__ == "__main__":
	main()
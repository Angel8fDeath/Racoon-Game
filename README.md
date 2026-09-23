# Racoon-Game

## Run locally

Install the Pygame community edition, which includes prebuilt packages:

```bash
python -m pip install pygame-ce
python game.py --host
```

The package is imported in code as `pygame`. A local desktop display is required
to show the game window; headless development containers cannot display it.

## Play over LAN

The host computer runs the authoritative game server and can also play as player 1
when it has a graphical desktop. In a headless environment, `--host` runs the
server without a window and desktop clients can still connect.
Players 2-5 connect to the host computer's local IP address. Everyone must use
the same TCP port (the default is `5000`).

On the host:

```bash
python game.py --host
```

On each other computer, replace `192.168.1.10` with the host computer's LAN address:

```bash
python game.py --connect 192.168.1.10
```

Allow Python through the host firewall for TCP port 5000 if clients cannot connect.
Press Escape to leave the game; the host can press Escape to stop it.
import pygame


def main():
	pygame.init()
	window = pygame.display.set_mode((800, 600))
	pygame.display.set_caption("Arrow Key Character")
	clock = pygame.time.Clock()

	character = pygame.Rect(375, 275, 50, 50)
	speed = 5
	running = True

	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

		keys = pygame.key.get_pressed()
		if keys[pygame.K_LEFT]:
			character.x -= speed
		if keys[pygame.K_RIGHT]:
			character.x += speed
		if keys[pygame.K_UP]:
			character.y -= speed
		if keys[pygame.K_DOWN]:
			character.y += speed

		character.clamp_ip(window.get_rect())

		window.fill((30, 35, 50))
		pygame.draw.rect(window, (80, 190, 120), character)
		pygame.display.flip()
		clock.tick(60)

	pygame.quit()
    

if __name__ == "__main__":
	main()

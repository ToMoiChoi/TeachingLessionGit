import pygame
import sys
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from game_engine import GameEngine

pygame.init()
pygame.font.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Cyber Escape")

engine = GameEngine(screen)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # Gọi phương thức save_progress từ engine trước khi thoát
            if hasattr(engine, 'save_progress'):
                engine.save_progress()
            pygame.quit()
            sys.exit()
        engine.handle_event(event)

    engine.update_and_render()
    engine.clock.tick(FPS)
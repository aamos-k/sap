#!/usr/bin/env python3
"""Cave exploration game — entry point."""
import sys
import random
import pygame
from game.world import World
from rendering.renderer import Renderer
from input.handler import InputHandler

SCREEN_W, SCREEN_H = 1280, 720
FPS   = 60
TITLE = "Cave Crawler"


def run(seed: int | None = None) -> None:
    if seed is None:
        seed = random.randrange(0, 2 ** 31)

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    world    = World(seed=seed)
    renderer = Renderer(screen, world)
    handler  = InputHandler(world, renderer.hud)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            restart = handler.process_event(event)
            if restart:
                seed  = random.randrange(0, 2 ** 31)
                world    = World(seed=seed)
                renderer = Renderer(screen, world)
                handler  = InputHandler(world, renderer.hud)
                break

        world.tick()
        renderer.draw_frame()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=TITLE)
    parser.add_argument("--seed", type=int, default=None,
                        help="Cave generation seed (random if omitted)")
    args = parser.parse_args()
    run(seed=args.seed)

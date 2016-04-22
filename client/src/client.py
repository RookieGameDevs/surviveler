from contextlib import ContextDecorator
import sdl2 as sdl


class sdl2context(ContextDecorator):
    def __enter__(self):
        sdl.SDL_Init(sdl.SDL_INIT_VIDEO)
        return self

    def __exit__(self, *exc):
        sdl.SDL_Quit()
        return False


class Client:
    def __init__(self, win_width, win_height, connection):
        self.window = sdl.SDL_CreateWindow(
            b"Surviveler",
            sdl.SDL_WINDOWPOS_CENTERED,
            sdl.SDL_WINDOWPOS_CENTERED,
            win_width,
            win_height,
            sdl.SDL_WINDOW_SHOWN)

        self.connection = connection

    def start(self):
        # sdl.SDL_Delay(5000)
        while True:
            data = self.connection.read() or None
            if data:
                print(data)
            else:
                from time import sleep
                sleep(0.5)

    def quit(self):
        sdl.SDL_DestroyWindow(self.window)

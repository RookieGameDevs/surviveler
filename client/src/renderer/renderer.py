import sdl2 as sdl


class Renderer:

    def __init__(self, width, height, depth=24):
        self.window = sdl.SDL_CreateWindow(
            b"Surviveler",
            sdl.SDL_WINDOWPOS_CENTERED,
            sdl.SDL_WINDOWPOS_CENTERED,
            width,
            height,
            sdl.SDL_WINDOW_SHOWN | sdl.SDL_WINDOW_OPENGL)

    def render(self):
        pass

    def shutdown(self):
        sdl.SDL_DestroyWindow(self.window)

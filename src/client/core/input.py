from core.events import KeyEvent
from core.events import MouseClickEvent
from core.events import MouseMoveEvent
from events import send_event
import ctypes
import sdl2 as sdl
import sdl2.ext as sdl_ext


class InputManager:
    """User input manager.

    This class processes user events coming from input devices (mouse, keyboard,
    joypad, etc.) and deserializes them into actual game events (`Event` class
    derivatives).
    """

    def process_input(self):
        """Process buffered input and dispatch resulting events."""
        events = sdl_ext.get_events()
        for evt in events:
            if evt.type in {sdl.SDL_KEYDOWN, sdl.SDL_KEYUP}:
                key_event = evt.key
                send_event(KeyEvent(
                    sdl.keyboard.SDL_GetKeyName(key_event.keysym.sym).decode('utf8'),
                    KeyEvent.State.down if evt.type == sdl.SDL_KEYDOWN else KeyEvent.State.up))

            elif evt.type in {sdl.SDL_MOUSEMOTION}:
                mouse_motion = evt.motion
                send_event(MouseMoveEvent(mouse_motion.x, mouse_motion.y))

            elif evt.type in {sdl.SDL_MOUSEBUTTONDOWN, sdl.SDL_MOUSEBUTTONUP}:
                mouse_event = evt.button

                if mouse_event.button == sdl.SDL_BUTTON_LEFT:
                    button = MouseClickEvent.Button.left
                elif mouse_event.button == sdl.SDL_BUTTON_RIGHT:
                    button = MouseClickEvent.Button.right
                else:
                    button = MouseClickEvent.Button.unknown

                if evt.type == sdl.SDL_MOUSEBUTTONDOWN:
                    state = MouseClickEvent.State.down
                else:
                    state = MouseClickEvent.State.up

                send_event(MouseClickEvent(
                    mouse_event.x,
                    mouse_event.y,
                    button,
                    state))

    @property
    def mouse_position(self):
        """Current mouse position in screen coordinates.

        :returns: Current mouse position in screen coordinates.
        :rtype: tuple
        """
        x, y = ctypes.c_int(0), ctypes.c_int(0)
        sdl.SDL_GetMouseState(ctypes.byref(x), ctypes.byref(y))
        return (x.value, y.value)

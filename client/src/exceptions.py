class ConfigError(Exception):
    """Missing or invalid configuration entry."""
    pass


class SDLError(Exception):
    """Generic SDL error."""
    pass


class OpenGLError(Exception):
    """Generic OpenGL error."""
    pass

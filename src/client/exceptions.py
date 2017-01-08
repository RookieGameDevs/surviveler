class ConfigError(Exception):
    """Missing or invalid configuration entry."""


class SDLError(Exception):
    """Generic SDL error."""


class OpenGLError(Exception):
    """Generic OpenGL error."""


class ShaderError(Exception):
    """Shader compile/link/access error."""


class ResourceError(Exception):
    """Resource loading error."""

class ConfigError(Exception):
    """Missing or invalid configuration entry."""


class SDLError(Exception):
    """Generic SDL error."""


class OpenGLError(Exception):
    """Generic OpenGL error."""


class ShaderError(Exception):
    """Shader compile/link error."""


class UniformError(Exception):
    """Uniform value initialization error."""

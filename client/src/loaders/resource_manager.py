from functools import partial
from loaders import load_obj
from utils import as_utf8
import json
import logging
import os


LOG = logging.getLogger(__name__)

DATAFILE = 'data.json'


class ResourceHandlerAlreadyExists(Exception):
    """Exception raised when there's already an existing extension handler for
    the given extension.
    """
    def __init__(self, ext):
        """Constructor.

        :param ext: The resource extension
        :type ext: str
        """
        super(ResourceHandlerAlreadyExists, self).__init__(
            'Handler for resources {} already exist'.format(ext))


class Resource(dict):

    def __init__(self, r_path, data):
        """Constructor.

        :param r_path: The resource path
        :type r_path: str

        :param data: The resource data
        :type data: dict
        """
        self.r_path = r_path
        self.data = data

        self.resources = {}

    def __repr__(self):
        """Print the proper representation of the resource."""
        return '<Resource({})>'.format(self.r_path)


class ResourceManager:

    #: Mapping of the various resource handlers
    __RESOURCE_HANDLERS = {}

    def __init__(self, conf):
        """Constructor.

        :param conf: The game configuration object
        :type conf: :class:`configparser.SectionProxy`
        """
        # TODO: find a proper way to define reliable relative paths here.
        self.r_path = os.path.abspath(conf['ResourceLocation'])
        self.cache = {}

    def norm_path(self, path):
        """Normalizes the given path relative to the resource location
        configuration.

        :param path: The path to be normalized
        :type path: str

        :return: The normalized path (real fs path)
        :rtype: str
        """
        if os.path.isabs(path):
            # FIXME: posix only. BAD.
            path = path[1:]
        return os.path.join(self.r_path, path)

    def get(self, path):
        """Gets a resource, loading it lazily in case it's not available.

        :param path: The resource relative path
        :type path: str

        :return: The required resource
        :rtype: :class:`Resource`
        """
        res = self.cache.get(path)
        if not res:
            abspath = self.norm_path(path)
            if os.path.isdir(abspath):
                res = self.load_package(path)
            else:
                res = self.load(path)

            self.cache[path] = res
        return res

    def load_package(self, package):
        """Loads the specified resource package.

        :param package: The package to be loaded
        :type package: str

        :return: The loaded resource
        :rtype: :class:`Resource`
        """
        LOG.info('Loading package {}'.format(package))
        datafile = os.path.join(package, DATAFILE)
        data = json.load(open(self.norm_path(datafile), 'r'))

        # Create the bare resource structure
        res = Resource(package, data)

        # Parse the package data.json file and load linked resources
        for name, path in data.get('resources', {}).items():
            r = self.get(os.path.join(package, path))
            res[name] = r.data

        return res

    def load(self, resource):
        """Loads the specified resource.

        :param resource: The resource to be loaded
        :type resource: str

        :return: The loaded resource
        :rtype: :class:`Resource`
        """
        LOG.info('Loading resource {}'.format(resource))
        _, ext = os.path.splitext(resource)
        load = self.get_loader(ext)

        # NOTE: we need to pass the directory name of the current resource
        # object, to calculate eventual relative linked objects.
        res = Resource(resource, load(
            fp=open(self.norm_path(resource), 'rb'),
            cwd=os.path.dirname(resource)))

        return res

    def get_loader(self, ext):
        """Returns the appropriate loader function based on the given extension.

        :param ext: The file extension
        :type ext: str

        :return: The loader function
        :rtype: function
        """
        return partial(ResourceManager.__RESOURCE_HANDLERS[ext], manager=self)

    @classmethod
    def resource_handler(cls, *ext):
        """Registers a resource handler.

        :param ext: The file extension
        :type ext: str
        """
        if ext in cls.__RESOURCE_HANDLERS:
            raise ResourceHandlerAlreadyExists(ext)

        def wrap(f):
            for e in ext:
                cls.__RESOURCE_HANDLERS[e] = f
            return f
        return wrap


@ResourceManager.resource_handler('.json')
def load_data(manager, fp, cwd):
    """Loader for json files.

    :param manager: The resource manager
    :type manager: :class:`loaders.ResourceManager`

    :param fp: The file pointer
    :type fp: File

    :param cwd: The current working directory
    :type cwd: str

    :return: A dictionary containing the loaded data
    :rtype: dict
    """
    return json.loads(as_utf8(fp.read()))


@ResourceManager.resource_handler('.obj')
def load_mesh(manager, fp, cwd):
    """Loader for obj files.

    :param manager: The resource manager
    :type manager: :class:`loaders.ResourceManager`

    :param fp: The file pointer
    :type fp: File

    :param cwd: The current working directory
    :type cwd: str

    :return: The resulting mesh object
    :rtype: :class:`renderer.Mesh`
    """
    from renderer import Mesh
    v, n, u, i = load_obj(as_utf8(fp.read()))
    return Mesh(v, i, n, u)


@ResourceManager.resource_handler('.vert')
def load_vertex(manager, fp, cwd):
    """Loader for vert files.

    TODO: define the object that is going to be returned by this function.

    :param manager: The resource manager
    :type manager: :class:`loaders.ResourceManager`

    :param fp: The file pointer
    :type fp: File

    :param cwd: The current working directory
    :type cwd: str

    :return: The resulting vert object
    :rtype: TBD
    """
    from renderer import ShaderSource
    from OpenGL.GL import GL_VERTEX_SHADER
    return ShaderSource.load_and_compile(fp.read(), GL_VERTEX_SHADER)


@ResourceManager.resource_handler('.frag')
def load_fragment(manager, fp, cwd):
    """Loader for frag files.

    TODO: define the object that is going to be returned by this function.

    :param manager: The resource manager
    :type manager: :class:`loaders.ResourceManager`

    :param fp: The file pointer
    :type fp: File

    :param cwd: The current working directory
    :type cwd: str

    :return: The resulting frag object
    :rtype: TBD
    """
    from renderer import ShaderSource
    from OpenGL.GL import GL_FRAGMENT_SHADER
    return ShaderSource.load_and_compile(fp.read(), GL_FRAGMENT_SHADER)


@ResourceManager.resource_handler('.shader')
def load_shader(manager, fp, cwd):
    """Loader for shader files.

    The shader file is just a desriptive wrapper around the vert/frag/geom files

    :param manager: The resource manager
    :type manager: :class:`loaders.ResourceManager`

    :param fp: The file pointer
    :type fp: File

    :param cwd: The current working directory
    :type cwd: str

    :return: The resulting shader program object
    :rtype: :class:`renderer.Shader`
    """
    from renderer import Shader

    shader_data = json.loads(as_utf8(fp.read()))
    shaders = []
    for r in shader_data.get('shaders', []):
        res = manager.get(os.path.join(cwd, r))
        shaders.append(res.data)

    return Shader.from_glsl(shaders, shader_data.get('params'))


@ResourceManager.resource_handler('.png', '.jpg')
def load_image(manager, fp, cwd):
    """Loader for image files.

    :param manager: The resource manager
    :type manager: :class:`loaders.ResourceManager`

    :param fp: The file pointer
    :type fp: File

    :param cwd: The current working directory
    :type cwd: str

    :return: The opened image
    :rtype: :class:`PIL.Image`
    """
    from PIL import Image
    img = Image.open(fp)
    return img


@ResourceManager.resource_handler('.ttf')
def load_font(manager, fp, cwd):
    """Loader for font files.

    :param manager: The resource manager
    :type manager: :class:`loaders.ResourceManager`

    :param fp: The file pointer
    :type fp: File

    :param cwd: The current working directory
    :type cwd: str

    :return: Simply the bytes read from file
    :rtype: :class:`sdl2.SDL_RWops.`
    """
    from io import BytesIO
    from sdl2 import rw_from_object
    content = fp.read()
    return rw_from_object(BytesIO(content))


@ResourceManager.resource_handler('.bmp')
def load_bitmap(manager, fp, cwd):
    """Loader for bitmaps.

    :param manager: The resource manager
    :type manager: :class:`loaders.ResourceManager`

    :param fp: The file pointer
    :type fp: File

    :param cwd: The current working directory
    :type cwd: str

    :return: Simply the bytes read from file
    :rtype: :class:`sdl2.SDL_RWops.`
    """
    from PIL import Image
    img = Image.open(fp)
    size = img.size
    img_data = img.tobytes()
    matrix = []
    for y in range(size[1]):
        matrix.append([])
        for x in range(size[0]):
            matrix[y].append(1 if img_data[y * size[0] + x] else 0)
    return matrix

from exceptions import ResourceError
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
        self.userdata = {}

        self.resources = {}

    def __bool__(self):
        """Boolean operator for Resources"""
        return bool(self.data or super().__bool__(self))

    def __repr__(self):
        """Print the proper representation of the resource."""
        return '<Resource({})>'.format(self.r_path)


class Package(Resource):
    """Override of the Resource class used to discern which resource is a
    package and which is not."""

    def __repr__(self):
        """Print the proper representation of the resource."""
        return '<Package({})>'.format(self.r_path)


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

        :returns: The normalized path (real fs path)
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

        :returns: The required resource
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

        :returns: The loaded resource
        :rtype: :class:`Resource`
        """
        LOG.info('Loading package {}'.format(package))
        datafile = os.path.join(package, DATAFILE)
        data = json.load(open(self.norm_path(datafile), 'r'))

        # Create the bare resource structure
        res = Package(package, data)

        # Parse the package data.json file and load linked resources
        for name, path in data.get('resources', {}).items():
            r = self.get(os.path.join(package, path))
            if isinstance(r, Package):
                res[name] = r
            else:
                res[name] = r.data

        return res

    def load(self, resource):
        """Loads the specified resource.

        :param resource: The resource to be loaded
        :type resource: str

        :returns: The loaded resource
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

        :returns: The loader function
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

    :returns: A dictionary containing the loaded data
    :rtype: dict
    """
    return json.loads(as_utf8(fp.read()))


@ResourceManager.resource_handler('.obj')
def load_obj_mesh(manager, fp, cwd):
    """Loader for obj meshes.

    :param manager: The resource manager
    :type manager: :class:`loaders.ResourceManager`

    :param fp: The file pointer
    :type fp: File

    :param cwd: The current working directory
    :type cwd: str

    :returns: The resulting mesh object
    :rtype: :class:`renderer.Mesh`
    """
    from renderlib.mesh import Mesh
    v, n, u, i = load_obj(as_utf8(fp.read()))
    return Mesh(v, i, n, u)


@ResourceManager.resource_handler('.png', '.jpg', '.jpeg')
def load_image(manager, fp, cwd):
    """Loader for image files.

    :param manager: The resource manager
    :type manager: :class:`loaders.ResourceManager`

    :param fp: The file pointer
    :type fp: File

    :param cwd: The current working directory
    :type cwd: str

    :returns: The loaded image.
    :rtype: :class:`renderlib.image.Image`
    """
    from renderlib.image import Image
    try:
        codec = {
            '.png': Image.Codec.PNG,
            '.jpeg': Image.Codec.JPEG,
            '.jpg': Image.Codec.JPEG,
        }[os.path.splitext(fp.name)[-1]]
    except (IndexError, KeyError):
        raise ResourceError('unsupported image type')
    return Image.from_buffer(fp.read(), codec)


@ResourceManager.resource_handler('.ttf')
def load_font(manager, fp, cwd):
    """Loader for font files.

    :param manager: The resource manager
    :type manager: :class:`loaders.ResourceManager`

    :param fp: The file pointer
    :type fp: File

    :param cwd: The current working directory
    :type cwd: str

    :returns: Font loader.
    :rtype: :class:
    """
    from renderlib.font import Font
    class FontLoader:
        """Auxiliary class which generates actual Font objects for requested
        sizes and caches them."""
        def __init__(self, data):
            self.data = data
            self.cache = {}

        def get_size(self, pt):
            if pt not in self.cache:
                self.cache[pt] = Font.from_buffer(self.data, pt)
            return self.cache[pt]

    return FontLoader(fp.read())


@ResourceManager.resource_handler('.bmp')
def load_bitmap(manager, fp, cwd):
    """Loader for bitmaps.

    :param manager: The resource manager
    :type manager: :class:`loaders.ResourceManager`

    :param fp: The file pointer
    :type fp: File

    :param cwd: The current working directory
    :type cwd: str

    :returns: Loaded bitmap as 2D byte matrix.
    :rtype: :class:`PIL.Image`
    """
    from PIL import Image
    img = Image.open(fp)
    size = img.size
    img_data = img.convert('L').tobytes()
    matrix = []
    for y in range(size[1]):
        matrix.append([])
        for x in range(size[0]):
            matrix[y].append(1 if img_data[y * size[0] + x] else 0)
    return matrix


@ResourceManager.resource_handler('.mesh')
def load_mesh(manager, fp, cwd):
    """Loader for mesh files.

    :param manager: The resource manager
    :type manager: :class:`loaders.ResourceManager`

    :param fp: The file pointer
    :type fp: File

    :param cwd: The current working directory
    :type cwd: str

    :returns: The loaded mesh.
    :rtype: :class:`renderlib.mesh.Mesh`
    """
    from renderlib.mesh import Mesh
    return Mesh.from_buffer(fp.read())

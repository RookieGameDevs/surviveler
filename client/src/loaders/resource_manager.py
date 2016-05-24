from functools import partial
import json
import os


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

    def get_file(self, filename):
        """Gets the file pointer to the given filename.

        :param filename: Filename to be opened (to be normalized)
        :type filename: str

        :return: The file pointer
        :rtype: File
        """
        fname = self.norm_path(filename)
        return open(fname, 'r')

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
        _, ext = os.path.splitext(resource)
        load = self.get_loader(ext)

        # NOTE: we need to pass the directory name of the current resource
        # object, to calculate eventual relative linked objects.
        res = Resource(resource, load(
            fp=open(self.norm_path(resource), 'r'),
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
    def resource_handler(cls, ext):
        """Registers a resource handler.

        :param ext: The file extension
        :type ext: str
        """
        if ext in cls.__RESOURCE_HANDLERS:
            raise ResourceHandlerAlreadyExists(ext)

        def wrap(f):
            cls.__RESOURCE_HANDLERS[ext] = f
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
    return json.load(fp)


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
    # TODO: use the obj_loader to load the obj data, create the Mesh object and
    # return it.
    return {'mesh': fp.read()}


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
    # TODO: read and compile the .vert file returning something that can be
    # linked in another step.
    return {'vert': fp.read()}


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
    # TODO: read and compile the .frag file returning something that can be
    # linked in another step.
    return {'frag': fp.read()}


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
    shader_data = json.load(fp)
    shaders = {}
    for r in shader_data.get('shaders', []):
        res = manager.get(os.path.join(cwd, r))
        shaders[r] = res.data

    # TODO: in shaders we have the map filename => compiled shader file: now we
    # need to link the compiled shaders and return the shader program. Knowing
    # the filename will help us understanding the type of shader file we are
    # linking.
    return {'shader': shaders}

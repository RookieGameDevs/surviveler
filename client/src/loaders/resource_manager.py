from functools import partial
import json
import os


DATAFILE = 'data.json'


class Resource:
    def __init__(self, r_mgr, r_path, data=None):
        """Constructor.

        :param r_mgr: The resource manager
        :type r_mgr: :class:`ResourceManager`

        :param r_path: The resource path
        :type r_path: str

        :param data: Optional data (for resource modules)
        :type data: dict
        """
        self.r_mgr = r_mgr
        self.r_path = r_path

        # Load the content
        self.load(data)

    def load(self, data=None):
        """Loads the resource data.

        The resource can be a resource module: in this case data will contains
        the module metadata, otherwise it's a resource object (and data will be
        None).

        Resource modules will cause the resource manager to load all the related
        resource objects. The name defined in the module's own data.json will be
        used as attribute names for that relevant data.

        :param data: Optional module data
        :type data: dict
        """
        if data:
            # This is a resource module. Set the given data as data and load all
            # the linked resources. Each resource object can be referenced from
            # the resource module with the name with which it's identified in
            # the data.json file.
            self.data = data
            for name, path in data.get('resources', {}).items():
                r = self.r_mgr.get(os.path.join(self.r_path, path))
                setattr(self, name, r.data)
        else:
            # This is a resource item. Use the appropriate loader to load the
            # relevant data and set self.data as the resulting value.
            _, ext = os.path.splitext(self.r_path)
            load = self.r_mgr.get_loader(ext)

            # NOTE: Politely ask the resource manager to get the resource file.
            f = self.r_mgr.get_file(self.r_path)

            # NOTE: we need to pass the directory name of the current resource
            # object, to calculate eventual relative linked objects.
            self.data = load(f, os.path.dirname(self.r_path))

    def __repr__(self):
        """Print the proper representation of the resource."""
        return '<Resource({})>'.format(self.r_path)


class ResourceManager:
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
                # Resource group load the data json
                datafile = os.path.join(path, DATAFILE)
                res = Resource(
                    self, path,
                    data=json.load(open(self.norm_path(datafile), 'r')))
            else:
                res = Resource(self, path)

            self.cache[path] = res
        return res

    def get_loader(self, ext):
        """Returns the appropriate loader function based on the given extension.

        :param ext: The file extension
        :type ext: string

        :return: The loader function
        :rtype: function
        """
        loader = {
            '.json': self.load_data,
            '.obj': self.load_mesh,
            '.shader': self.load_shader,
            '.vert': self.load_vertex,
            '.frag': self.load_fragment,
        }[ext]

        return loader

    def load_data(self, f, cwd):
        """Loader for json files.

        :param f: The file pointer
        :type f: File

        :param cwd: The current working directory
        :type cwd: str

        :return: A dictionary containing the loaded data
        :rtype: dict
        """
        return json.load(f)

    def load_mesh(self, f, cwd):
        """Loader for obj files.

        :param f: The file pointer
        :type f: File

        :param cwd: The current working directory
        :type cwd: str

        :return: The resulting mesh object
        :rtype: :class:`renderer.Mesh`
        """
        # TODO: use the obj_loader to load the obj data, create the Mesh object and
        # return it.
        return {'mesh': f.read()}

    def load_vertex(self, f, cwd):
        """Loader for vert files.

        TODO: define the object that is going to be returned by this function.

        :param f: The file pointer
        :type f: File

        :param cwd: The current working directory
        :type cwd: str

        :return: The resulting vert object
        :rtype: TBD
        """
        # TODO: read and compile the .vert file returning something that can be
        # linked in another step.
        return {'vert': f.read()}

    def load_fragment(self, f, cwd):
        """Loader for frag files.

        TODO: define the object that is going to be returned by this function.

        :param f: The file pointer
        :type f: File

        :param cwd: The current working directory
        :type cwd: str

        :return: The resulting frag object
        :rtype: TBD
        """
        # TODO: read and compile the .frag file returning something that can be
        # linked in another step.
        return {'frag': f.read()}

    def load_shader(self, f, cwd):
        """Loader for shader files.

        The shader file is just a desriptive wrapper around the vert/frag/geom files

        :param f: The file pointer
        :type f: File

        :param cwd: The current working directory
        :type cwd: str

        :return: The resulting shader program object
        :rtype: :class:`renderer.Shader`
        """
        shader_data = json.load(f)
        shaders = {}
        for r in shader_data.get('shaders', []):
            res = self.get(os.path.join(cwd, r))
            shaders[r] = res.data

        # TODO: in shaders we have the map filename => compiled shader file: now we
        # need to link the compiled shaders and return the shader program. Knowing
        # the filename will help us understanding the type of shader file we are
        # linking.
        return {'shader': shaders}

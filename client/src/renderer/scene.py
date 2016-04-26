from matlib import mat4


class Scene:

    def __init__(self):
        self.root = RootNode()

    def render(self, rndr):
        self.root.render(rndr, mat4())


class AbstractSceneNode:

    def __init__(self):
        self.children = []
        self.transform = mat4()

    def render(self, rndr, transform):
        raise NotImplementedError

    def get_children(self):
        return self.children

    def add_child(self, node):
        self.children.append(node)

    def remove_child(self, node):
        try:
            self.children.remove(node)
        except ValueError:
            pass


class RootNode(AbstractSceneNode):

    def render(self, rndr, transform):

        def render_all(node, parent_transform):
            node.render(rndr, node.transform * parent_transform)

            for child in node.get_children():
                render_all(child, node.transform)

        for child in self.get_children():
            render_all(child, self.transform)


class GeometryNode(AbstractSceneNode):

    def __init__(self, mesh, shader, params=None):
        super(GeometryNode, self).__init__()
        self.mesh = mesh
        self.shader = shader
        self.params = params or {}

    def render(self, rndr, transform):
        self.params['transform'] = transform
        self.shader.use(self.params)
        self.mesh.render(rndr)

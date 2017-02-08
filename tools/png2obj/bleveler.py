"""
Add-on to create level mesh based on png.
"""
import bpy
from bpy.props import CollectionProperty, StringProperty

bl_info = {
    'name': 'png2obj',
    'category': 'Import-Export',
    'author': 'Iacopo Marmorini <iacopomarmorini@gmail.com>',
    'version': (1, 0),
    'blender': (2, 7, 8),
    'location': 'View3D > Object > Move4 Object',
    'description': 'Create a mesh from a bitmap',
    'warning': '',
    'wiki_url': '',
    'tracker_url': '',
}

bpy.types.Scene.MyString = StringProperty(name='file path',
    attr='custompath',  # this a variable that will set or get from the scene
    description='simple file path string',
    maxlen=1024,
    default='')  # this set the text


bpy.types.Scene.MyPath = StringProperty(name='file path',
    attr='custompath',  # this a variable that will set or get from the scene
    description='simple file path',
    maxlen=1024,
    subtype='FILE_PATH',
    default='')  # this set the text


class VIEW3D_PT_custompathmenupanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'Level loader'

    def draw(self, context):
        layout = self.layout
        # text
        layout.label(text='png loader')

        # print(dir(bpy.context.scene))
        # operator button
        # OBJECT_OT_CustomButton => object.CustomButton
        layout.operator('object.custombutton')

        self.layout.prop(context.scene, 'MyPath')

        # prop is a variable to to set or get name of the variable.
        layout.prop(context.scene, 'MyString')
        # print(dir(context.scene)) # this will display the list that you should able to see
        # operator button
        # OBJECT_OT_CustomPath => object.png2obj
        layout.operator('object.png2obj')


class OBJECT_OT_custombutton(bpy.types.Operator):
    bl_idname = 'object.custombutton'
    bl_label = 'Do it'
    __doc__ = 'Simple Custom Button'

    def invoke(self, context, event):
        print('Custom Button pressed......')
        print('I should act on {}'.format(context.scene.MyString))

        wall_width = 3

        # Load the png to obtain verts and edges

        # ============== Create edges ======================
        verts = [
            (0, 0, 0), (2, 0, 0), (2, 1, 0), (0, 1, 0),
            (-3, -3, 0), (3, -3, 0), (3, 3, 0), (-3, 3, 0),
        ]
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
        ]
        faces = []

        mesh_data = bpy.data.meshes.new("cube_mesh_data")
        mesh_data.from_pydata(verts, edges, faces)
        mesh_data.update()

        obj = bpy.data.objects.new("My_Object", mesh_data)

        scene = bpy.context.scene
        scene.objects.link(obj)

        # select/active
        obj.select = True
        scene.objects.active = obj

        # Switch to edit mode
        bpy.ops.object.editmode_toggle()

        # bpy.ops.mesh.select_all(action='TOGGLE')
        bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={'value': (0, 0, wall_width)})

        # Fill upper horizontal wall surfaces (triangulate)
        bpy.ops.mesh.fill()
        # ==================================================

        return{'FINISHED'}


class OBJECT_OT_custompath(bpy.types.Operator):
    bl_idname = 'object.png2obj'
    bl_label = 'Load level image'
    __doc__ = 'This will create a mesh'

    filename_ext = '.png'
    filter_glob = StringProperty(default='*.png', options={'HIDDEN'})

    # This can be look into the one of the export or import python file.
    # Need to set a path so so we can get the file name and path
    filepath = StringProperty(
        name='File Path',
        description='Filepath used for importing png files',
        maxlen=1024,
        default='')
    files = CollectionProperty(
        name='File Path',
        type=bpy.types.OperatorFileListElement,
        )

    def execute(self, context):
        #set the string path fo the file here.
        #this is a variable created from the top to start it
        bpy.context.scene.MyString = self.properties.filepath

        print('*************SELECTED FILES ***********')
        for file in self.files:
            print(file.name)

        print('FILEPATH %s' % self.properties.filepath)  # display the file name and current path
        return {'FINISHED'}

    def draw(self, context):
        self.layout.operator('file.select_all_toggle')

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


def register():
    bpy.utils.register_class(VIEW3D_PT_custompathmenupanel)
    bpy.utils.register_class(OBJECT_OT_custombutton)
    bpy.utils.register_class(OBJECT_OT_custompath)
    print('register')


def unregister():
    bpy.utils.register_class(VIEW3D_PT_custompathmenupanel)
    bpy.utils.register_class(OBJECT_OT_custombutton)
    bpy.utils.register_class(OBJECT_OT_custompath)
    print('unregister')

if __name__ == '__main__':
    register()

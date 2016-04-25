from itertools import count
from message import Message
from message import MessageField
from message import MessageType
from message_handlers import get_handlers
from message_handlers import handler
from renderer import GeometryNode
from renderer import Mesh
from renderer import Scene
from renderer import Shader
from utils import tstamp
import logging


LOG = logging.getLogger(__name__)

TRIANGLE_VERTICES = [
    +0.0, +0.3, 0.0,
    -0.3, -0.3, 0.0,
    +0.3, -0.3, 0.0,
]

TRIANGLE_INDICES = [
    0,
    1,
    2,
]


class Client:
    """Client class"""

    def __init__(self, renderer, proxy):
        self.renderer = renderer
        self.proxy = proxy

        self.sync_counter = count()
        self.syncing = {}
        self.delta = None

        triangle = Mesh(TRIANGLE_VERTICES, TRIANGLE_INDICES)
        shader = Shader.from_glsl(
            'data/shaders/simple.vert',
            'data/shaders/simple.frag')

        self.scene = Scene()
        self.scene.root.add_child(GeometryNode(triangle, shader))

    @handler(MessageType.pong)
    def pong_handler(self, msg):
        if self.syncing:
            now = tstamp()
            initial = self.syncing.pop(msg.data[MessageField.id])

            self.delta = now - msg.data[MessageField.timestamp] + (now - initial) / 2

            LOG.info('Synced time with server: delta={}'.format(self.delta))

    @handler(MessageType.gamestate)
    def update_gamestate(self, msg):
        LOG.debug('Processing and updating gamestate')

    def process_message(self, msg):
        """Processes a message received from the server.

        :param msg: the message to be processed
        :type msg: :class:`message.Message`
        """
        LOG.info('Processing message: {} {}'.format(msg, msg.data))
        for func in get_handlers(msg.msgtype):
            func(self, msg)

    def sync(self):
        """Tries to guess the local delta with the server timestamps.

        Uses a message of type MessageType.ping with a random id to sync with
        the server clock guessing the lag related to ping.
        """
        LOG.info('Syncing time with server')
        sync_id = next(self.sync_counter)
        self.syncing[sync_id] = tstamp()
        msg = Message(MessageType.ping, {MessageField.id: sync_id})
        self.proxy.push(msg)

    def start(self):
        """Client main loop.

        Polls the MessageProxy and processes each message received from the
        server, renders the scene.
        """
        self.sync()
        t = tstamp()
        while True:
            if tstamp() - t > 1000:
                self.sync()
                t = tstamp()
            for msg in self.proxy.poll():
                self.process_message(msg)

            self.renderer.render(self.scene)

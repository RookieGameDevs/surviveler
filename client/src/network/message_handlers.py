from collections import defaultdict
from functools import partial
import logging


LOG = logging.getLogger(__name__)

# Dictionary containing the various handlers for the message types.
__MESSAGE_HANDLERS = defaultdict(list)


def message_handler(msgtype):
    """Decorator for received message handlers.

    :param msgtype: the type of the message
    :type msgtype: :enum:`message.MessageType`
    """
    def wrap(f):
        __MESSAGE_HANDLERS[msgtype].append(f)
        return f
    return wrap


def get_message_handlers(msgtype):
    """Returns all the handlers for a specific msgtype.

    :param msgtype: the type of the message
    :type msgtype: :enum:`message.MessageType`

    :return: handlers for the given message
    :rtype: list
    """
    from client import Client
    return map(
        lambda f: partial(f, Client.get_instance()),
        __MESSAGE_HANDLERS[msgtype])

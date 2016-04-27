from collections import defaultdict
import logging


LOG = logging.getLogger(__name__)

# Dictionary containing the various handlers for the message types.
__MESSAGE_HANDLERS = defaultdict(list)


def handler(msgtype):
    """Decorator for received message handlers.

    :param msgtype: the type of the message
    :type msgtype: :enum:`message.MessageType`
    """
    def wrap(f):
        __MESSAGE_HANDLERS[msgtype].append(f)
        return f
    return wrap


def get_handlers(msgtype):
    """Yields all the handlers for a specific msgtype.

    :param msgtype: the type of the message
    :type msgtype: :enum:`message.MessageType`

    :return: handler for the given message
    :rtype: callable
    """
    for h in __MESSAGE_HANDLERS[msgtype]:
        yield h

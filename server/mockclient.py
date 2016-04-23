from __future__ import print_function

import socket
import sys, os
import datetime
import time
import struct
import zlib
from io import BytesIO

from msgpack import Packer, Unpacker

# ZLib compression level
ZLIB_COMP_LVL = 6


# Client Identifier (should be provided by the server)
CLIENT_ID = 34


def timestamp():
    """miliseconds"""
    return int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)


# Example of client->server msg
class MsgA(object):

    # random example msgtype id
    MsgTypeId = 23

    def __init__(self, i, s):
        # an integer
        self.i = i
        # a string
        self.s = s

    def msgpack(self):
        """Return the message pack buffer version of itself
        """
        # this is just an example and the packer should not:
        # - reside here
        # - nor be recreated each time we want to pack a message
        packer = Packer()
        return packer.pack({'TheInteger': self.i, 'TheString': self.s})


class SurvClient(object):
    """Surviveler Game Protocol Client class
    """

    def __init__(self, host, port):
        self.server_addr = (host, port)

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # print('connecting to %s port %s' % self.server_addr)
        self.sock.connect(self.server_addr)

    def send(self, msg):

        buf = msg.msgpack()
        pkt = self._forge_packet(buf, msg.MsgTypeId)
        self.sock.sendall(pkt)

    def _forge_packet(self, buf, msgtypeid):
        """Forge a generic core packet from a msgpack buffer
            buf: msgpack'ed buffer to send
        """
        pkt = bytearray()

        # prepend buffer with its length, computed as follow:
        # NO: - 16b/2B integer packet length
        # - 64b/8B timestamp
        # - ?B msgpack buffer
        # - 32b/4B checksum
        length = struct.pack('!H', 8 + 2 + 2 + len(buf))

        # add 16 bits packet length
        pkt.extend(length)

        # add 64 bits timestamp (unsigned)
        pkt.extend(struct.pack('!Q', timestamp()))

        # add 16 bits Client Id (unsigned)
        pkt.extend(struct.pack('!H', CLIENT_ID))

        # add 16 bits msg type Id (unsigned)
        pkt.extend(struct.pack('!H', msgtypeid))

        # add msgpack buffer
        pkt.extend(bytes(buf))

        print ('packet: ', pkt)
        return pkt


    # receive message pack packet
    def receive_msgpack(self):
        try:
            unpacker = Unpacker()
            while True:
                buf = self.sock.recv(1024**2)
                if not buf:
                    break
                unpacker.feed(buf)
                for o in unpacker:
                    print(o)
        except Exception as e:
            pass
            print("exception in receive_msg: ", e)

    def receive_msg(self):
        try:
            buf = self.sock.recv(2)
            length = struct.unpack('!H', buf)[0]
            print ("receive_msg, length: ", length)

            buf = self.sock.recv(8)
            timestamp = struct.unpack('!Q', buf)[0]
            print ("receive_msg, timestamp: ", timestamp)

            buf = self.sock.recv(2)
            xpos = struct.unpack('!H', buf)[0]
            print ("receive_msg, xpos: ", xpos)

            buf = self.sock.recv(2)
            ypos = struct.unpack('!H', buf)[0]
            print ("receive_msg, ypos: ", ypos)


            # buf = self.sock.recv(length-8)
            # print ("receive_helloworld, buf: ", buf)
            if not buf:
                return
            print(buf)
        except Exception as e:
            pass
            print("exception in receive_helloworld: ", e)

    def close(self):
        if self.sock is not None:
            # print('closing socket')
            self.sock.close()
            self.sock = None

    __del__ = close


if __name__ == '__main__':
    try:
        client = SurvClient('localhost', 1234)
        client.connect()

        # create msg of type MsgA
        a = MsgA(8, 'hello')

        while True:
            client.send(a)
            client.receive_msg()
            # client.receive_msg()
            time.sleep(1)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(e, exc_type, fname, exc_tb.tb_lineno)

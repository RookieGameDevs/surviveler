from __future__ import print_function

import socket
import sys, os
import datetime
import time
import struct
import zlib
from io import BytesIO

import msgpack
from msgpack import Packer, Unpacker

# ZLib compression level
ZLIB_COMP_LVL = 6


# Client Identifier (should be provided by the server)
CLIENT_ID = 34


def timestamp():
    """miliseconds"""
    return int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1000)


class Ping(object):

    # random example msgtype id
    MsgTypeId = 0

    def __init__(self, i, s):
        self.Id = i
        self.Tstamp = s

    def msgpack(self):
        """Return the message pack buffer version of itself
        """
        packer = Packer()
        return packer.pack({'Id': self.Id, 'Tstamp': self.Tstamp})


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
        pkt = self._forge_packet(msg.MsgTypeId, buf)
        self.sock.sendall(pkt)

    def _forge_packet(self, msgtypeid, payload):
        """Forge a generic core packet from a msgpack buffer
        """
        pkt = bytearray()

        # add unisgned 16 bits Msg Type
        pkt.extend(struct.pack('!H', msgtypeid))

        # add payload length (32 bits unsigned)
        length = len(payload)
        pkt.extend(struct.pack('!I', length))

        # add msgpack buffer
        pkt.extend(struct.pack('!' + str(length) + 'p', payload))

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
            timestamp = struct.unpack('!q', buf)[0]
            print ("receive_msg, timestamp: ", timestamp)

            buf = self.sock.recv(2)
            xpos = struct.unpack('!H', buf)[0]
            print ("receive_msg, xpos: ", xpos)

            unpacker = Unpacker()
            buf = self.sock.recv(2)
            ypos = struct.unpack('!H', buf)[0]
            print ("receive_msg, ypos: ", ypos)
            if not buf:
                return
            print(buf)
        except Exception as e:
            pass
            print("exception in receive_msg: ", e)

    def receive_msgpack(self):
        try:
            buf = self.sock.recv(2)
            length = struct.unpack('!H', buf)[0]
            print ("receive_msgpack, msg type: ", length)

            buf = self.sock.recv(4)
            length = struct.unpack('!i', buf)[0]
            print ("receive_msgpack, payload length: ", length)

            # buf = self.sock.recv(8)
            # timestamp = struct.unpack('!Q', buf)[0]
            # print ("receive_msgpack, timestamp: ", timestamp)

            buf = self.sock.recv(length)
            buf = struct.unpack('!' + str(length) + 'p', buf)[0]
            unpacker = Unpacker()
            unpacker.feed(buf)
            for o in unpacker:
                print (o)
        except Exception as e:
            pass
            print("exception in receive_msgpack: ", e)

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
        a = Ping(8, 12345678)

        while True:
            client.send(a)
            client.receive_msgpack()
            time.sleep(1)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(e, exc_type, fname, exc_tb.tb_lineno)

from ctypes import *
import socket
import struct


class IP(Structure):
    _fields_ = [
        ("ihl",                 c_ubyte, 4),    # char 4 bit
        ("version",             c_ubyte, 4),    # char 4 bit
        ("tos",                 c_ubyte, 8),    # char 1 byte
        ("len",                 c_ushort, 16),  # short 2 byte
        ("id",                  c_ushort, 16),  # short 2 byte
        ("offset",              c_ushort, 16),  # short 2 byte
        ("ttl",                 c_ubyte, 8),    # char 1 byte
        ("protocol_num",        c_ubyte, 8),    # char 1 byte
        ("sum",                 c_ushort, 16),  # short 2 byte
        ("src",                 c_uint32, 32),  # int 4 byte
        ("dst",                 c_uint32, 32),  # int 4 byte
    ]

    def __new__(cls, socket_buffer=None):
        """принимает в качестве первого аргумента ссылку на класс и затем создает и возвращает объект этого класса,
         а тот уже передается в метод __init__."""
        return cls.from_buffer_copy(socket_buffer)

    def __init__(self, socket_buffer=None):
        # human readable IP addersses
        self.src_address = socket.inet_ntoa(struct.pack("L", self.src))
        self.dst_address = socket.inet_ntoa(struct.pack("<L", self.dst))
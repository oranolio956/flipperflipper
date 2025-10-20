#!/usr/bin/env python3
# Decoded from Configuration/st_encryption.py
# Original was obfuscated with exec(SEC(INFO(...)))


import base64
from Crypto import Random
from Crypto.Cipher import AES

abbrev = '1V3=XUaR20c0W'
NWA = base64.b64decode('V3FwbXBaVnViOUhucFBLa1ZDRU4yWjR2blJ0OUQ0U0E=')

def encrypt(raw):
    iv = Random.new().read( AES.block_size )
    cipher = AES.new(NWA, AES.MODE_CFB, iv )
    return (base64.b64encode( iv + cipher.encrypt( raw ) ) )

def decrypt(enc):
    enc = base64.b64decode(enc)
    iv = enc[:16]
    cipher = AES.new(NWA, AES.MODE_CFB, iv )
    return cipher.decrypt( enc[16:] )

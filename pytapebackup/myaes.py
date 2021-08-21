import bz2
import os
import sys
import random
import struct
import shutil
from base64 import b64decode, b64encode
import time
PYVER = sys.version_info[0]

BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s : s[:-ord(s[len(s)-1:])]

import base64
try:
    from Crypto.Cipher import AES
    from Crypto import Random
except:
    from crypto.Cipher import AES
    from crypto import Random

class AESText:
    def __init__( self, key ):
        if len(key) > 32:
            self.key = key[:32]
        else:
            self.key = key

    def encrypt( self, raw ):
        raw = pad(raw)
        iv = Random.new().read( AES.block_size )
        cipher = AES.new( self.key, AES.MODE_CBC, iv )
        return base64.b64encode( iv + cipher.encrypt( raw ) )

    def decrypt( self, enc ):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv )
        return unpad(cipher.decrypt( enc[16:] ))


class MyAES:
    """
    AES file encrypt/decrypt class.
    File compressed with bzip2 before encryption.
    """
    def __init__(self, key_, compression = True):
        """
        Key must be 256 bit. If the provided key is longer 
        than 256 bit, first 256 bit is used.
        """
        if len(key_) > 32:
            key_ = key_[:32]
        self.key_ = key_
        self.compression_ = compression


    def encrypt(self, input_file, output_file=None, block_size=1048576, remove_source=True, max_file_size=25000000):
        if PYVER == 3:
            iv = bytes([random.randint(0, 0xFF) for i in range(16)])
        else:
            iv = Random.new().read(16)
        encryptor = AES.new(self.key_, AES.MODE_CBC, iv)
        compressor = bz2.BZ2Compressor()
        if output_file is None:
            output_file = input_file + ".enc"
        outp = open(output_file, "wb")
        # ilk 50 byte iv ve dosya gercek boyu icin
        outp.write(bytes([0x20 for u in range(34)]))
        outp.write(iv)
        finc = 1
        file_size = os.path.getsize(input_file)
        part = bytes([])
        with open(input_file, 'rb') as inp:
            while True:
                block = inp.read(block_size)
                if not block:
                    break
                compressed = compressor.compress(block)
                if compressed:
                    part = part + compressed
                    if len(part) > block_size:
                        filesize = outp.tell()
                        if filesize > max_file_size:
                            outp.close()
                            outp = open( "%s-%d" % (output_file , finc), "wb")
                            finc += 1
                        outp.write(encryptor.encrypt(part[:block_size]))
                        part = part[block_size:]

            remaining = part + compressor.flush()
            lastpartlen = len(remaining)
            if len(remaining) % 16 != 0:
                if PYVER == 3:
                    remaining += bytes([0x20 for i in range(16 - lastpartlen % 16)])
                else:
                    remaining += " " * (16 - lastpartlen % 16)

            outp.write(encryptor.encrypt(remaining))
            if finc == 1: # dosya boyu max_file_size degerini asmamis
                outp.seek(0)
            else:
                outp.close()
                outp = open(output_file, "r+b")
                outp.seek(0)
            outp.write(struct.pack('<Q', file_size))
            outp.close()

            if finc > 1:
                shutil.move("%s-%d" % (output_file , finc), "%s-%dE" % (output_file , finc))

        if remove_source is True:
            os.remove(input_file)


    def decrypt(self, input_file, output_file=None, block_size= 1048576, remove_source = False):
        if output_file is None:
            output_file = os.path.splitext(input_file)[0]

        with open(input_file, "rb") as gr:
            real_file_size = struct.unpack('<Q', gr.read(struct.calcsize('Q')))[0]
            gr.seek(34)
            iv = gr.read(16)
            decryptor = AES.new(self.key_, AES.MODE_CBC, iv)
            decompressor = bz2.BZ2Decompressor()
            i=0
            with open(output_file, "wb") as ck:
                try:
                    while True:
                        part = gr.read(block_size)
                        part_length = len(part)
                        if part_length == 0:
                            break
                        ck.write(decompressor.decompress(decryptor.decrypt(part)))
                    ck.truncate(real_file_size)
                except:
                    return False
        if remove_source is True:
            os.remove(input_file)
        return True 


if __name__ == "__main__":
    anahtar = "1" * 64
    s = MyAES(anahtar, compression=False)
    s.encrypt("testfile")
    s.decrypt("testfile.enc", "deneme")

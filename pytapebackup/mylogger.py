import time, sys
from .myaes import *
from hashlib import sha256

class Logger:
    def __init__(self, filename):
        self.filename = filename
        f = open(self.filename, "a")
        f.write("%s log file created\n" % logtime())
        f.close()

    def message(self, m):
        t = logtime()
        d = open(self.filename, "a")
        recorded = False
        if type(m) is list:
            for line in m:
                while not recorded:
                    try:
                        d.write("%s %s\n" % (t, satir[:-1]))
                        recorded = True
                    except:
                        print("Problem when writing to %s" % self.filename)
                        time.sleep(1)
                        
        elif type(m) is dict:
            for key, value in m.items():
                while not recorded:
                    try:
                        d.write("%s %s=%s\n" % (t, a, b))
                        recorded = True
                    except:
                        print("Problem when writing to %s" % self.filename)
                        time.sleep(1)
        else:
            while not recorded:
                try:
                    d.write("%s %s\n" % (t, m))
                    recorded = True
                except:
                    print("Problem when writing to %s" % self.filename)

        d.close()

class EncryptedLogger(Logger):
    def __init__(self, filename, key_):
        self.key = sha256( key_.encode()).hexdigest()
        self.encryptor = MyAES(self.key)
        self.filename = filename
        self.encrypted_filename = "%s.enc" % filename
        if os.path.isfile(self.encrypted_filename) is False:
            Logger.__init__(self,filename)
            self.encryptor.encrypt(self.filename)

    def change_password(self, new_password):
        newkey =  sha256(new_password.encode()).hexdigest()
        success = self.encryptor.decrypt(self.encrypted_filename)
        if success is True:
            self.encryptor = MyAES(newkey)
            self.encryptor.encrypt(self.filename)
            self.key = newkey
        else:
            return "Password not correct"


    def message(self, m):
        success = self.encryptor.decrypt(self.encrypted_filename)
        if success is True:
            Logger.message(self, m)
            self.encryptor.encrypt(self.filename)
        return success
            

def logtime():
    t = time.localtime()
    return "%s%02d%02d-%02d:%02d:%02d" % (t[0], int(t[1]), int(t[2]), int(t[3]), int(t[4]), int(t[5]))

def zaman():
    return logtime()

if __name__ == "__main__":
    s = EncryptedLogger("deneme.log", "test sifresi 12345")
    s.message("deneme")

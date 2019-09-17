import socket
import threading
import time


##############
# base class #
##############

class esp8266conn:
    ''' basic TCP setup '''

    def __init__(self, **kw):
        self.ip = kw.get('ip', '127.0.0.1')
        self.port = kw.get('port', 5005)
        self.buf_size = kw.get('buf_size', 1024)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


###############################
# class for simple operations #
###############################

class esp8266ops(esp8266conn):
    ''' 
    some util funcs
    of these, only open() and close() will open/close the connection
    it's your responsibility to do it at a higher level
    '''

    def __init__(self, **kw):
        esp8266conn.__init__(self, **kw)

    def open(self):
        self.s.connect((self.ip, self.port))

    def close(self):
        self.s.close()

    def send(self, data):
        self.s.send(data)

    def recv(self, **kw):
        return self.s.recv(kw.get('buf_size', self.buf_size))


########################
# for operating pulley #
########################

class pulley(esp8266ops):

    def __init__(self, **kw):
        esp8266ops.__init__(self, **kw)

    def getcurrentloc(self, **kw):
        self.s.bind((self.ip, self.port))
        self.s.listen(1)
        c, a = self.s.accept()
        while 1:
            c.send("CURRLOC?")
            data = c.recv(kw.get('buf_size', self.buf_size))
            c.close()
            break
        return data

    def requestmovement(self, dest, **kw):
        self.s.bind((self.ip, self.port))
        self.s.listen(1)
        c, a = self.s.accept()
        while 1:
            c.send(f"{dest}-REQMVMT")
            c.close()
            break
        return data


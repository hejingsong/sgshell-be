#! /usr/bin/env python
# -*- coding:utf-8 -*-


class BaseSocket(object):

    def __init__(self, sock=None):
        self.sock = sock

    def fileno(self):
        return self.sock.fileno()

    def onRead(self, ioLoop):
        pass

    def onWrite(self, ioLoop):
        pass

    def close(self):
        self.sock = None

    def shutdown(self, how):
        self.sock.shutdown(how)

#! /usr/bin/env python
# -*- coding:utf-8 -*-

import select


class IOLoop(object):
    E_READ = 0x01
    E_WRITE = 0x02
    E_ALL = E_READ | E_WRITE

    def __init__(self):
        self.fd2Obj = {}
        self.lstRead = []
        self.lstWrite = []
        self.run = True
        self.timeout = 0.2

    def addEvent(self, sock, events):
        if not (events & self.E_ALL):
            return

        fd = sock.fileno()
        if events & self.E_READ:
            self.lstRead.append(fd)

        if events & self.E_WRITE:
            self.lstWrite.append(fd)

        self.fd2Obj[fd] = sock

    def delEvent(self, sock, events):
        if not (events & self.E_ALL):
            return

        fd = sock.fileno()
        if not fd in self.fd2Obj:
            return

        if (events & self.E_READ) and (fd in self.lstRead):
            self.lstRead.remove(fd)

        if (events & self.E_WRITE) and (fd in self.lstWrite):
            self.lstWrite.remove(fd)

        self.fd2Obj.pop(fd)
    
    def stop(self):
        self.run = False

    def loop(self):
        while(self.run):
            rLst, wLst, _ = select.select(
                self.lstRead, self.lstWrite, [], self.timeout)

            for r in rLst:
                o = self.fd2Obj.get(r, None)
                if not o:
                    continue
                o.onRead(self)

            for w in wLst:
                o = self.fd2Obj.get(w, None)
                if not o:
                    continue
                o.onWrite(self)

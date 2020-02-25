#! /usr/bin/env python
# -*- coding:utf-8 -*-

import sgProto

import logger
import ioloop
import server

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345


def main():
    log = logger.Logger()
    log.init()

    sgProto.parseFromFile('./proto/sgshell.proto')

    ioLoop = ioloop.IOLoop()

    srv = server.Server(SERVER_HOST, SERVER_PORT)
    srv.init()

    ioLoop.addEvent(srv, ioLoop.E_READ)

    log.getLogger('main').info('server is running.')

    ioLoop.loop()


if __name__ == '__main__':
    main()

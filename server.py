#! /usr/bin/env python
# -*- coding:utf-8 -*-

import socket
import base64
import hashlib

import proxy
import logger
import basesocket


class Server(basesocket.BaseSocket):

    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    def __init__(self, host, port):
        super(Server, self).__init__()
        self.host = host
        self.port = port
        self.connNum = 0
        self.maxConnNum = 2

    def init(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)

    def onRead(self, ioLoop):
        clt, cltInfo = self.sock.accept()
        if self.connNum >= self.maxConnNum:
            clt.close()
            return

        if not self.handshake(clt):
            logger.getLogger('Server').info(
                'client %s:%s connect but is not websocket protocol.', *cltInfo)
            return

        self.connNum += 1
        pxy = proxy.Proxy(clt)
        ioLoop.addEvent(pxy, ioLoop.E_READ)
        logger.getLogger('Server').info(
            'websocket client %s:%s is connect. server is gone.', *cltInfo)

    def handshake(self, clt):
        buffer = clt.recv(4096)
        if not buffer:
            return False
        headerInfo = {}
        lines = buffer.split(b"\r\n")
        for line in lines:
            kv = line.split(b':')
            if len(kv) != 2:
                continue
            k = kv[0].lower().decode()
            headerInfo[k] = kv[1].strip().decode()

        if headerInfo.get('connection', '') != 'Upgrade':
            return False
        if headerInfo.get('upgrade', '') != 'websocket':
            return False
        if not headerInfo.get('sec-websocket-key', None):
            return False

        secKey = headerInfo['sec-websocket-key']
        magicString = secKey + self.GUID
        sha1 = hashlib.sha1(magicString.encode()).digest()
        secAccept = base64.b64encode(sha1)

        response = "HTTP/1.1 101 Switching Protocols\r\n"\
            "Upgrade: websocket\r\n"\
            "Connection: Upgrade\r\n"\
            'Sec-WebSocket-Accept:' + secAccept.decode() + "\r\n\r\n"

        clt.sendall(response.encode())
        return True

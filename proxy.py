#! /usr/bin/env python
# -*- coding:utf-8 -*-

import socket

import ssh
import logger
import basesocket
import utils.encoder

PROTO_LOGIN = 1
PROTO_SESSION = 3
PROTO_LOGOUT = 4
PROTO_RESIZE = 5


class Proxy(basesocket.BaseSocket):

    WEBSOCKET_OPCODE_TEXT = 0x01
    WEBSOCKET_OPCODE_BINARY = 0x02
    WEBSOCKET_OPCODE_CLOSE = 0x08
    WEBSOCKET_OPECODE_PING = 0x09
    WEBSOCKET_OPECODE_PONG = 0x0A

    PROTO_MAP = {
        PROTO_LOGIN: 'login',
        PROTO_SESSION: 'session',
        PROTO_RESIZE: 'resize',
        PROTO_LOGOUT: 'logout'
    }

    def __init__(self, sock):
        super(Proxy, self).__init__(sock)
        self.opcode = 0
        self.pong = False
        self.remainData = b''
        self.sshs = {}
        self.encoder = utils.encoder.Encoder()

    def close(self, ioLoop):
        ioLoop.delEvent(self, ioLoop.E_ALL)
        super(Proxy, self).close()
        ioLoop.stop()

    def onRead(self, ioLoop):
        buffer = self.sock.recv(1024)
        if not buffer:
            self.close(ioLoop)
            return

        buffer = self.remainData + buffer
        result = self.parseData(buffer)
        if result is False:
            self.close(ioLoop)
            return

        if self.pong:
            self.pong = False
            self.sendData(result, self.WEBSOCKET_OPECODE_PONG)
        else:
            proIdx, data = self.encoder.decode(result)
            response = self.do(ioLoop, proIdx, data)
            if not response:
                return
            self.sendData(response)

    def sendClose(self):
        self.sendData(b'', self.WEBSOCKET_OPCODE_CLOSE)

    def sendPong(self, data=b''):
        self.sendData(data, self.WEBSOCKET_OPECODE_PONG)

    def sendPing(self, data=b''):
        self.sendData(data, self.WEBSOCKET_OPECODE_PING)

    def parseData(self, data):
        header = 0
        maskKey = 0
        headerLen = 0
        payloadLen = 0
        payloadData = []

        # TODO: 添加FIN位判断
        header = data[0]
        if ((header & 0x0f) == self.WEBSOCKET_OPCODE_CLOSE):
            self.sendClose()
            return False

        if ((header & 0x0f) == self.WEBSOCKET_OPECODE_PING):
            self.pong = True

        pay = data[1]
        mask = pay & 0x80
        if not mask:
            return False
        payloadLen = pay & 0x7f

        headerLen = 2
        if payloadLen == 126:
            payloadLen = data[2] << 8 | data[3]
            headerLen += 2
        elif payloadLen == 127:
            payloadLen = data[2] << 56 | data[3] << 48 | data[4] << 40 \
                | data[5] << 32 | data[6] << 24 | data[7] << 16 | data[8] << 8 | data[9]
            headerLen += 8
        maskKey = data[headerLen: headerLen + 4]
        headerLen += 4

        dataLen = len(data)
        remainLen = dataLen - headerLen
        if remainLen < payloadLen:
            remainData = self.sock.recv(payloadLen - remainLen)
            data += remainData

        data = data[headerLen: headerLen + payloadLen]
        for i, d in enumerate(data):
            c = d ^ maskKey[i % 4]
            payloadData.append(c)

        self.opcode = header & 0x0f
        self.remainData = data[headerLen + payloadLen:]
        return bytes(payloadData)

    def sendData(self, data: bytes, opcode=0):
        dataLen = len(data)
        header = 0x82 | self.opcode
        if opcode:
            header |= opcode

        payloadLen = 0
        extendPayloadLens = []
        payloadData = data
        headerLst = [header]

        if dataLen <= 125:
            payloadLen = dataLen
        elif dataLen <= 65535:
            payloadLen = 126
            extendPayloadLens.append((dataLen >> 8) & 0xff)
            extendPayloadLens.append((dataLen) & 0xff)
        elif dataLen <= 2 ** 64 - 1:
            payloadLen = 127
            extendPayloadLens.append((dataLen >> 56) & 0xff)
            extendPayloadLens.append((dataLen >> 48) & 0xff)
            extendPayloadLens.append((dataLen >> 40) & 0xff)
            extendPayloadLens.append((dataLen >> 32) & 0xff)
            extendPayloadLens.append((dataLen >> 24) & 0xff)
            extendPayloadLens.append((dataLen >> 16) & 0xff)
            extendPayloadLens.append((dataLen >> 8) & 0xff)
            extendPayloadLens.append((dataLen) & 0xff)

        headerLst.append(payloadLen)
        if (extendPayloadLens):
            headerLst.extend(extendPayloadLens)

        headerData = bytes(headerLst)
        result = headerData + payloadData
        self.sock.sendall(result)

    def do(self, ioLoop, proIdx, data):
        funName = self.PROTO_MAP.get(proIdx, None)
        if not funName:
            logger.getLogger('Proxy').error(
                'can\'t found protocol id: %s', proIdx)
            return
        fun = getattr(self, funName)
        return fun(ioLoop, data)

    def login(self, ioLoop, data):
        termId = data['termId']
        oSsh = ssh.Ssh(None, self, data)
        ret = oSsh.login()
        if ret:
            return self.encoder.encode('loginResponse', {'code': -1, 'termId': termId, 'msg': ret})
        ioLoop.addEvent(oSsh, ioLoop.E_READ)
        self.sshs[termId] = oSsh
        return self.encoder.encode('loginResponse', {'code': 0, 'termId': termId})

    def session(self, ioLoop, data):
        termId = data['termId']
        msg = data['msg']
        oSsh = self.sshs.get(termId, None)
        if not oSsh:
            logger.getLogger('Proxy').error(
                'session can\'t found. termId: %s', termId)
            return
        oSsh.session(msg, ioLoop)

    def logout(self, ioLoop, data):
        termId = data['termId']
        oSsh = self.sshs.get(termId, None)
        if not oSsh:
            logger.getLogger('Proxy').error(
                'session can\'t found. termId: %s', termId)
            return
        oSsh.logout(ioLoop)
        self.sshs.pop(termId)

    def resize(self, ioLoop, data):
        row = data['row']
        col = data['col']
        for _, oSsh in self.sshs.items():
            oSsh.resize(col, row)

    # call by ssh
    def sshLogout(self, termId, ioLoop):
        data = self.encoder.encode('logout', {'termId': termId})
        self.sendData(data)
        self.sshs.pop(termId)

    # call by ssh
    def sshSession(self, termId, msg, ioLoop):
        data = self.encoder.encode('session', {'termId': termId, 'msg': msg})
        self.sendData(data)

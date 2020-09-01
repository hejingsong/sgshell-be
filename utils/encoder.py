#! /usr/bin/env python
# -*- coding:utf-8 -*-

import sgProto

import utils.singleton as singleton

@singleton.Singleton
class Encoder(object):

    def init(self, protoFile):
        sgProto.parseFile(protoFile)

    def encode(self, protoName, data):
        code = sgProto.encode(protoName, data)
        return sgProto.pack(code)

    def decode(self, code):
        data = sgProto.unpack(code)
        return sgProto.decode(data)

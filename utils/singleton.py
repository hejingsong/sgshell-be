#! /usr/bin/env python
# -*- coding:utf-8 -*-

def Singleton(cls):
    _instance = {}

    def warpper(*args, **kwargs):
        clsName = cls.__name__
        if not clsName in _instance:
            o = cls(*args, **kwargs)
            _instance[clsName] = o
        return  _instance[clsName]

    return warpper

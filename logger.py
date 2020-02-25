#! /usr/bin/env python
# -*- coding:utf-8 -*-

import os
import time
import logging
import utils.singleton as singleton


@singleton.Singleton
class Logger(object):

    def __init__(self):
        self.handler = None
        self.formatter = None
        self.logPath = './log'
        self.filename = ''
        self.level = logging.INFO
        self.loggerMap = {}

    def init(self):
        self.createPath()

        filenameFormat = self.logPath + '/%Y-%m-%d.log'
        self.filename = time.strftime(filenameFormat)
        self.handler = logging.FileHandler(self.filename, 'a+')
        self.formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            '%H:%M:%S')
        self.handler.setFormatter(self.formatter)

    def getLogger(self, name):
        logger = logging.getLogger(name)
        if not name in self.loggerMap:
            logger.addHandler(self.handler)
            logger.setLevel(level=self.level)
            self.loggerMap[name] = True
        return logger

    def createPath(self):
        if os.path.exists(self.logPath):
            return
        os.mkdir(self.logPath)


def getLogger(name):
    log = Logger()
    return log.getLogger(name)

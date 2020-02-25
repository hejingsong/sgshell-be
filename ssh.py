import re
import json
import socket
import paramiko

import basesocket


class Ssh(basesocket.BaseSocket):
    TYPE_PASSWORD = 1
    TYPE_PUBLIC_KEY = 2

    def __init__(self, sock, proxy, config):
        super(Ssh, self).__init__(sock)
        self.termId = config['termId']
        self.host = config['host']
        self.port = config['port']
        self.user = config['user']
        self.passwd = config['passwd']
        self.row = config['row']
        self.col = config['col']
        self.loginType = config.get('type', self.TYPE_PASSWORD)
        self.key = config.get('key', None)
        self.proxy = proxy
        self.clt = None
        self.chan = None

    def destory(self):
        try:
            self.chan.close()
            self.clt.close()
        except:
            pass

    def onRead(self, ioLoop):
        data = self.read()
        if not data:
            self.noticeLogout(ioLoop)
        else:
            self.proxy.sshSession(self.termId, data, ioLoop)

    def login(self):
        ret = ''
        try:
            self.clt = paramiko.client.SSHClient()
            self.clt.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            keyFileName = None if self.loginType == self.TYPE_PASSWORD else self.key
            self.clt.connect(
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.passwd,
                key_filename=keyFileName,
                timeout=1.5
            )
            self.chan = self.clt.invoke_shell(
                term='xterm',
                width=self.col,
                height=self.row
            )
            self.sock = self.chan
        except socket.error as e:
            ret = str(e)
        except paramiko.BadHostKeyException as e:
            ret = str(e)
        except paramiko.AuthenticationException as e:
            ret = str(e)
        except paramiko.SSHException as e:
            ret = str(e)
        return ret

    def logout(self, ioLoop):
        ioLoop.delEvent(self, ioLoop.E_ALL)
        self.session('logout\n', ioLoop)
        self.destory()

    def noticeLogout(self, ioLoop):
        ioLoop.delEvent(self, ioLoop.E_ALL)
        self.proxy.sshLogout(self.termId, ioLoop)
        self.destory()

    def session(self, msg, ioLoop):
        try:
            self.chan.send(msg)
        except OSError:
            self.noticeLogout(ioLoop)

    def resize(self, cols, rows):
        self.chan.resize_pty(width=cols, height=rows)

    def read(self):
        try:
            return self.chan.recv(1024)
        except socket.timeout:
            pass
        return None

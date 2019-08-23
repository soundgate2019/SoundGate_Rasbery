# ------------------------------------------------------------------------
#
#  This file is part of the Chirp Connect Python SDK.
#  For full information on usage and licensing, see https://chirp.io
#
#  Copyright (c) 2011-2018, Asio Ltd.
#  All rights reserved.
#
# ------------------------------------------------------------------------

__title__ = 'chirp'
__version__ = '3.4.6'
__author__ = 'Asio Ltd.'
__license__ = 'License :: Other/Proprietary License'
__copyright__ = 'Copyright 2011-2019, Asio Ltd.'


from ctypes import CDLL, RTLD_GLOBAL
import ctypes.util
import os
import platform
import subprocess

if platform.system() == 'Linux':
    # Explicitly load libgcc as ctypes on RPi doesn't dynamically link it.
    gcc = CDLL(ctypes.util.find_library('gcc_s'), mode=RTLD_GLOBAL)

# ------------------------------------------------------------------------
# Locate the libchirp-connect-shared library from the libraries subdirectory
# To install, download the appropriate Chirp Connect library for your
# operating system and place in the chirpsdk/libraries subdirectory.
# ------------------------------------------------------------------------
try:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if platform.system() == 'Darwin':
        library_path = os.path.join(dir_path, 'libraries', 'darwin', 'libchirp-connect-shared.dylib')
    elif platform.system() == 'Linux':
        if os.uname()[4].startswith('arm'):
            cpuinfo = subprocess.check_output(['cat', '/proc/cpuinfo']).decode()
            if 'neon' in cpuinfo:
                library_path = os.path.join(dir_path, 'libraries', 'rpi7', 'libchirp-connect-shared.so')
            else:
                library_path = os.path.join(dir_path, 'libraries', 'rpi6', 'libchirp-connect-shared.so')
        else:
            library_path = os.path.join(dir_path, 'libraries', 'linux', 'libchirp-connect-shared.so')
    elif platform.system() == 'Windows':
        if platform.architecture()[0] == '32bit':
            library_path = os.path.join(dir_path, 'libraries', 'win32', 'libchirp-connect-shared.dll')
        elif platform.architecture()[0] == '64bit':
            library_path = os.path.join(dir_path, 'libraries', 'win64', 'libchirp-connect-shared.dll')
    else:
        raise RuntimeError('The Chirp Python SDK is not configured for %s platforms. ' \
                           'Please contact contact@chirp.io for custom builds' % platform.system())
    libconnect = CDLL(library_path)
except OSError:
    library_path = ctypes.util.find_library('chirp-connect-shared')
    if not library_path:
        raise Exception("Couldn't find libchirp-connect-shared. Please install the Chirp C SDK.")
    libconnect = CDLL(library_path)

from .connect import *
from _connect import (
    CHIRP_CONNECT_STATE_STOPPED,
    CHIRP_CONNECT_STATE_PAUSED,
    CHIRP_CONNECT_STATE_RUNNING,
    CHIRP_CONNECT_STATE_SENDING,
    CHIRP_CONNECT_STATE_RECEIVING,
    CHIRP_CONNECT_STATE_NOT_CREATED,
    CHIRP_SDK_BUFFER_SIZE
)
from .exceptions import *

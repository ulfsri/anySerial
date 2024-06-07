# SPDX-FileCopyrightText: 2024-present GraysonBellamy <grayson.bellamy@ul.org>
#
# SPDX-License-Identifier: MIT

import os
import sys
from typing import Optional
from .linux import LinuxSerialStream
from .darwin import DarwinSerialStream
from .bsd import BSDSerialStream
from .posix import PosixSerialStream
SerialStream : Optional[type[LinuxSerialStream | DarwinSerialStream | BSDSerialStream | PosixSerialStream]] = None

if os.name == "posix":
    plat = sys.platform.lower()
    if plat.startswith("linux"):
        SerialStream = LinuxSerialStream
    elif plat.startswith("darwin"):
        SerialStream = DarwinSerialStream
    elif any(plat.startswith(term) for term in ["bsd", "freebsd", "netbsd", "openbsd"]):
        SerialStream = BSDSerialStream
    else:
        SerialStream = PosixSerialStream
else:
    raise NotImplementedError(f"Platform '{os.name}' not supported")

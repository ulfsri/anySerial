# SPDX-FileCopyrightText: 2024-present GraysonBellamy <grayson.bellamy@ul.org>
#
# SPDX-License-Identifier: MIT

import os
import sys

if os.name == "posix":
    plat = sys.platform.lower()
    if plat.startswith("linux"):
        from .linux import LinuxSerialStream as SerialStream
    elif plat.startswith("darwin"):
        from .darwin import DarwinSerialStream as SerialStream
    elif any(plat.startswith(term) for term in ["bsd", "freebsd", "netbsd", "openbsd"]):
        from .bsd import BSDSerialStream as SerialStream
    else:
        from .posix import PosixSerialStream as SerialStream
else:
    raise NotImplementedError(f"Platform '{os.name}' not supported")
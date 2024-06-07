# SPDX-FileCopyrightText: 2024-present GraysonBellamy <grayson.bellamy@ul.org>
#
# Parts of this file are based on the Python serial library by Chris Liechti (C) 2001-2020 Chris Liechti <cliechti@gmx.net> licensed under the BSD 3-Clause License
# and trio_pyserial by Jörn Heissler (C) 2020 Jörn Heissler licensed under the BSD 3-Clause License
#
# SPDX-License-Identifier: MIT

import array
import fcntl
import os


from .posix import PosixSerialStream


class DarwinSerialStream(PosixSerialStream):
    """
    Darwin specific constants and functions
    """

    IOSSIOSPEED = 0x80045402  # _IOW('T', 2, speed_t)
    osx_version = int(os.uname().release.split(".")[0])

    # Tiger or above can support arbitrary serial speeds
    if osx_version >= 8:

        def _set_special_baudrate(self, baudrate: int) -> None:
            """
            Set custom baudrate
            """
            self._baudrate = baudrate
            # use IOKit-specific call to set up high speeds
            buf = array.array("i", [self._baudrate])
            fcntl.ioctl(self.fd, self.IOSSIOSPEED, buf, 1)

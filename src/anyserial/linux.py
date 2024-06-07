# SPDX-FileCopyrightText: 2024-present GraysonBellamy <grayson.bellamy@ul.org>
#
# Parts of this file are based on the Python serial library by Chris Liechti (C) 2001-2020 Chris Liechti <cliechti@gmx.net> licensed under the BSD 3-Clause License
# and trio_pyserial by Jörn Heissler (C) 2020 Jörn Heissler licensed under the BSD 3-Clause License
#
# SPDX-License-Identifier: MIT

import array
import fcntl
import termios


from .posix import PosixSerialStream


class LinuxSerialStream(PosixSerialStream):
    """
    Linux specific constants and functions
    """

    # Extra termios flags
    CMSPAR = 0o10000000000  # Use "stick" (mark/space) parity

    # Baudrate ioctls
    TCGETS2 = 0x802C542A
    TCSETS2 = 0x402C542B
    BAUDRATE_OFFSET = 9
    BOTHER = 0o010000

    BAUDRATE_CONSTANTS = {
        0: 0o000000,  # hang up
        50: 0o000001,
        75: 0o000002,
        110: 0o000003,
        134: 0o000004,
        150: 0o000005,
        200: 0o000006,
        300: 0o000007,
        600: 0o000010,
        1200: 0o000011,
        1800: 0o000012,
        2400: 0o000013,
        4800: 0o000014,
        9600: 0o000015,
        19200: 0o000016,
        38400: 0o000017,
        57600: 0o010001,
        115200: 0o010002,
        230400: 0o010003,
        460800: 0o010004,
        500000: 0o010005,
        576000: 0o010006,
        921600: 0o010007,
        1000000: 0o010010,
        1152000: 0o010011,
        1500000: 0o010012,
        2000000: 0o010013,
        2500000: 0o010014,
        3000000: 0o010015,
        3500000: 0o010016,
        4000000: 0o010017,
    }

    def _set_special_baudrate(self, baudrate: int) -> None:
        """
        Set custom baudrate
        """
        self._baudrate = baudrate
        # right size is 44 on x86_64, allow for some growth
        buf = array.array("i", [0] * 64)
        try:
            # get serial_struct
            fcntl.ioctl(self.fd, self.TCGETS2, buf)

            # set custom speed
            buf[2] &= ~termios.CBAUD
            buf[2] |= self.BOTHER
            buf[self.BAUDRATE_OFFSET] = buf[self.BAUDRATE_OFFSET + 1] = self._baudrate

            # set serial_struct
            assert fcntl.ioctl(self.fd, self.TCSETS2, buf) == 0
            fcntl.ioctl(self.fd, self.TCGETS2, buf)
            if buf[9] != self._baudrate or buf[10] != self._baudrate:
                raise ValueError(f"failed. speed is {buf[9]} {buf[10]}")
        except IOError as ex:
            raise ValueError(f"Failed to set custom baud rate {self._baudrate}: {ex!s}")

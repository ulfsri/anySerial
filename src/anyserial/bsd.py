# SPDX-FileCopyrightText: 2024-present GraysonBellamy <grayson.bellamy@ul.org>
#
# Parts of this file are based on the Python serial library by Chris Liechti (C) 2001-2020 Chris Liechti <cliechti@gmx.net> licensed under the BSD 3-Clause License
# and trio_pyserial by Jörn Heissler (C) 2020 Jörn Heissler licensed under the BSD 3-Clause License
#
# SPDX-License-Identifier: MIT

from .posix import PosixSerialStream


class ReturnBaudrate:
    def __getitem__(self, key: int) -> int:
        return key


class BSDSerialStream(PosixSerialStream):
    """
    BSD specific constants and functions
    """

    # Only tested on FreeBSD:
    # The baud rate may be passed in as a literal value.
    BAUDRATE_CONSTANTS = ReturnBaudrate()

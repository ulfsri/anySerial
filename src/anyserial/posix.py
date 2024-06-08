# SPDX-FileCopyrightText: 2024-present GraysonBellamy <grayson.bellamy@ul.org>
#
# Parts of this file are based on the Python serial library by Chris Liechti (C) 2001-2020 Chris Liechti <cliechti@gmx.net> licensed under the BSD 3-Clause License
# and trio_pyserial by Jörn Heissler (C) 2020 Jörn Heissler licensed under the BSD 3-Clause License
#
# SPDX-License-Identifier: MIT

import fcntl
import anyio
import os
import socket
import termios
from struct import pack, unpack
from typing import Dict, Optional

import anyio.lowlevel
from anyio import ClosedResourceError

from .abstract import AbstractSerialStream, Parity, StopBits, FlowControl

TIOCMGET = getattr(termios, "TIOCMGET", 0x5415)
TIOCMBIS = getattr(termios, "TIOCMBIS", 0x5416)
TIOCMBIC = getattr(termios, "TIOCMBIC", 0x5417)
BUF_ZERO = pack("I", 0)

BIT_RTS = getattr(termios, "TIOCM_RTS", 0x004)
BIT_CTS = getattr(termios, "TIOCM_CTS", 0x020)

TIOCINQ = getattr(termios, "TIOCINQ", getattr(termios, "FIONREAD", 0x541B))
TIOCM_ZERO = pack("I", 0)


class PosixSerialStream(AbstractSerialStream):
    CMSPAR = 0
    BAUDRATE_CONSTANTS: Dict[int, int] = {}
    BOTHER: Optional[int] = None
    _fd: Optional[int] = None
    _hangup_on_close: bool = True

    @property
    def fd(self) -> int:
        if self._fd is None:
            raise ClosedResourceError("File descriptor is closed")
        return self._fd

    def in_waiting(self) -> int:
        """
        Return the number of bytes currently in the input buffer.
        """
        s = fcntl.ioctl(self.fd, TIOCINQ, TIOCM_ZERO)
        return unpack("I", s)[0]

    async def aclose(self) -> None:
        self._close()

    async def aopen(self) -> None:
        if self._fd is not None:
            raise ValueError("File descriptor is already open")
        try:
            self._fd = os.open(self._port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        except OSError as ex:
            raise ValueError(f"Failed to open port: {self._port}") from ex
        try:
            self._configure_port()
        except BaseException:
            self._close()
            raise

    def _close(self) -> None:
        if self._fd is None:
            return

        fd = self._fd
        self._fd = None
        os.close(fd)

    async def discard_input(self) -> None:
        termios.tcflush(self.fd, termios.TCIFLUSH)

    async def send_eof(self) -> None:
        pass

    async def discard_output(self) -> None:
        termios.tcflush(self.fd, termios.TCOFLUSH)

    async def send_break(self, duration: float = 0.25) -> None:
        termios.tcsendbreak(self.fd, int(duration * 4))

    async def _send(self, data: memoryview) -> int:
        # Need to rewrite this so we don't have to create socket each time. Trio supports passing in file descriptor directly but anyio does not.
        # await anyio.wait_socket_writable(self.fd)
        return os.write(self.fd, data)

    async def _recv(self, max_bytes: int) -> bytes:
        # Need to rewrite this so we don't have to create socket each time. Trio supports passing in file descriptor directly but anyio does not.
        await anyio.wait_socket_readable(self.fd)
        return os.read(self.fd, max_bytes)

    async def get_cts(self) -> bool:
        return self._get_bit(BIT_CTS)

    async def get_rts(self) -> bool:
        return self._get_bit(BIT_RTS)

    async def set_rts(self, value: bool) -> None:
        self._set_bit(BIT_RTS, value)

    async def get_hangup(self) -> bool:
        return self._hangup_on_close

    async def set_hangup(self, value: bool) -> None:
        self._hangup_on_close = value
        self._configure_port()

    def _set_bit(self, bit: int, value: bool) -> None:
        fcntl.ioctl(self.fd, TIOCMBIS if value else TIOCMBIC, pack("I", bit))

    def _get_bit(self, bit: int) -> bool:
        return bool(unpack("I", fcntl.ioctl(self.fd, TIOCMGET, BUF_ZERO))[0] & bit)

    def _configure_port(self, force_update: bool = False) -> None:
        try:
            fd = self.fd
        except ClosedResourceError:
            return

        if self._exclusive:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                raise ValueError("Port is already open by another process")
        else:
            fcntl.flock(fd, fcntl.LOCK_UN)

        try:
            orig_attrs = termios.tcgetattr(fd)
            iflag, oflag, cflag, lflag, ispeed, ospeed, cc = orig_attrs
        except termios.error as ex:
            raise ValueError("Failed to get port attributes") from ex

        cflag |= termios.CLOCAL | termios.CREAD
        lflag &= ~(
            termios.ICANON
            | termios.ECHO
            | termios.ECHOE
            | termios.ECHOK
            | termios.ECHONL
            | termios.ISIG
            | termios.IEXTEN
        )

        for flag in ("ECHOCTL", "ECHOKE"):
            if hasattr(termios, flag):
                lflag &= ~getattr(termios, flag)

        oflag &= ~(termios.OPOST | termios.ONLCR | termios.OCRNL)
        iflag &= ~(termios.INLCR | termios.IGNCR | termios.ICRNL | termios.IGNBRK)

        if hasattr(termios, "IUCLC"):
            iflag &= ~termios.IUCLC

        if hasattr(termios, "PARMRK"):
            iflag &= ~termios.PARMRK

        custom_baud = False
        try:
            ispeed = ospeed = getattr(
                termios, f"B{self._baudrate}"
            )  # See if it's a supported baud rate
        except AttributeError:
            try:
                ispeed = ospeed = self.BAUDRATE_CONSTANTS[self._baudrate]
            except KeyError:
                if self.BOTHER:
                    ispeed = ospeed = self.BOTHER
                else:
                    ispeed = ospeed = termios.B38400

                custom_baud = True

        cflag &= ~termios.CSIZE
        try:
            cflag |= getattr(termios, f"CS{self._bytesize}")
        except AttributeError as ex:
            raise ValueError("Invalid byte size") from ex

        if self._stopbits == StopBits.ONE:
            cflag &= ~termios.CSTOPB
        elif self._stopbits == StopBits.TWO:
            cflag |= termios.CSTOPB
        elif self._stopbits == StopBits.ONE_POINT_FIVE:
            cflag |= termios.CSTOPB
        else:
            raise ValueError("Invalid stop bits")

        iflag &= ~(termios.INPCK | termios.ISTRIP)
        if self._parity == Parity.NONE:
            cflag &= ~(termios.PARENB | termios.PARODD | self.CMSPAR)
        elif self._parity == Parity.ODD:
            cflag &= ~self.CMSPAR
            cflag |= termios.PARENB | termios.PARODD
        elif self._parity == Parity.EVEN:
            cflag &= ~(termios.PARODD | self.CMSPAR)
            cflag |= termios.PARENB
        elif self._parity == Parity.MARK and self.CMSPAR:
            cflag |= termios.PARENB | self.CMSPAR | termios.PARODD
        elif self._parity == Parity.SPACE and self.CMSPAR:
            cflag |= termios.PARENB | self.CMSPAR
            cflag &= ~termios.PARODD
        else:
            raise ValueError("Invalid parity")

        if hasattr(termios, "IXANY"):
            if self._flowcontrol == FlowControl.XON_XOFF:
                iflag |= termios.IXON | termios.IXOFF
            else:
                iflag &= ~(termios.IXON | termios.IXOFF | termios.IXANY)
        else:
            if self._flowcontrol == FlowControl.XON_XOFF:
                iflag |= termios.IXON | termios.IXOFF
            else:
                iflag &= ~(termios.IXON | termios.IXOFF)

        if hasattr(termios, "CRTSCTS"):
            if self._flowcontrol == FlowControl.RTS_CTS:
                cflag |= termios.CRTSCTS
            else:
                cflag &= ~termios.CRTSCTS
        elif hasattr(termios, "CNEW_RTSCTS"):
            if self._flowcontrol == FlowControl.RTS_CTS:
                cflag |= termios.CNEW_RTSCTS
            else:
                cflag &= ~termios.CNEW_RTSCTS

        if self._hangup_on_close:
            cflag |= termios.HUPCL
        else:
            cflag &= ~termios.HUPCL

        new_attrs = [iflag, oflag, cflag, lflag, ispeed, ospeed, cc]

        if force_update or new_attrs != orig_attrs:
            termios.tcsetattr(fd, termios.TCSANOW, new_attrs)
        if custom_baud:
            self._set_special_baudrate(self._baudrate)

    def _set_special_baudrate(self, baudrate: int) -> None:
        raise NotImplementedError(
            "Custom baud rates are not supported on this platform"
        )

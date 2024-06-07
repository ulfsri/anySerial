# SPDX-FileCopyrightText: 2024-present GraysonBellamy <grayson.bellamy@ul.org>
#
# Parts of this file are based on the Python serial library by Chris Liechti (C) 2001-2020 Chris Liechti <cliechti@gmx.net> licensed under the BSD 3-Clause License
# and trio_pyserial by Jörn Heissler (C) 2020 Jörn Heissler licensed under the BSD 3-Clause License
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from enum import Enum, auto
import anyio
from anyio.abc import ByteStream
from anyio import ResourceGuard
from typing import Self


class Parity(Enum):
    NONE = auto()
    ODD = auto()
    EVEN = auto()
    MARK = auto()
    SPACE = auto()


class StopBits(Enum):
    ONE = auto()
    ONE_POINT_FIVE = auto()
    TWO = auto()


class FlowControl(Enum):
    NONE = auto()
    XON_XOFF = auto()
    RTS_CTS = auto()
    DTR_DSR = auto()


class AbstractSerialStream(ByteStream, ABC):
    _port: str
    _baudrate: int
    _exclusive: bool
    _bytesize: int
    _parity: Parity
    _stopbits: StopBits
    _flowcontrol: FlowControl
    _recv_resource_guard: ResourceGuard
    _send_resource_guard: ResourceGuard

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        exclusive: bool = False,
        bytesize: int = 8,
        parity: Parity = Parity.NONE,
        stopbits: StopBits = StopBits.ONE,
        flowcontrol: FlowControl = FlowControl.NONE,
    ) -> None:
        super().__init__()

        self._port = port
        self._baudrate = baudrate
        self._exclusive = exclusive
        self._bytesize = bytesize
        self._parity = parity
        self._stopbits = stopbits
        self._flowcontrol = flowcontrol
        self._recv_resource_guard = ResourceGuard(
            "Another task is already receiving data from this serial port"
        )
        self._send_resource_guard = ResourceGuard(
            "Another task is already sending data to this serial port"
        )

    async def __aenter__(self) -> Self:
        await self.aopen()
        return self

    def __del__(self) -> None:
        self._close()

    @property
    def port(self) -> str:
        return self._port

    @abstractmethod
    async def aopen(self) -> None:
        pass

    @abstractmethod
    async def aclose(self) -> None:
        pass

    @abstractmethod
    def _close(self) -> None:
        pass

    @abstractmethod
    async def discard_input(self) -> None:
        pass

    @abstractmethod
    async def discard_output(self) -> None:
        pass

    @abstractmethod
    async def send_break(self, duration: float = 0.25) -> None:
        pass

    async def recieve_some(self, max_bytes: int) -> bytes:
        with self._recv_resource_guard:
            return await self._recv(max_bytes)

    async def send_all(self, data: bytes) -> None:
        with self._send_resource_guard:
            with memoryview(data) as data:
                if not data:
                    await anyio.lowlevel.checkpoint()
                total_sent = 0
                while total_sent < len(data):
                    with data[total_sent:] as remaining_data:
                        sent = await self._send(remaining_data)
                        total_sent += sent

    # @abstractmethod
    # async def get_flow_control(self) -> FlowControl:
    #     pass

    # @abstractmethod
    # async def set_flow_control(self, flow_control: FlowControl) -> None:
    #     pass

    async def receive(self, max_bytes: int = 1) -> bytes:
        return await self._recv(max_bytes)
    
    async def send(self, data: bytes) -> None:
        await self._send(memoryview(data))
        return

    @abstractmethod
    async def _recv(self, max_bytes: int) -> bytes:
        pass

    @abstractmethod
    async def _send(self, data: memoryview) -> int:
        pass

    # @abstractmethod
    # async def _wait_writable(self) -> None:
    #     pass

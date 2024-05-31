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
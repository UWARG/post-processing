"""
Groundside scripts to receive GPS location messages
FTP Documentation: https://mavlink.io/en/services/ftp.html
"""

import enum
import struct
import sys


from pymavlink import mavutil

# connection params
CONNECTION_ADDRESS = "tcp:127.0.0.1:14550"
TIMEOUT = 5.0
DELAY_TIME = 1.0
FILE_PATH = b"/@ROMFS/locations.txt"
CHUNK_SIZE = 239  # Max data size per chunk
MAX_PAYLOAD_SIZE = 239  # Max payload size for FTP commands

# file path to read from
# 1. start up connection on mission planner
# 2. mavlink and establish write tcp connection
# 3. config menu -> MAVFtp -> simulation drone file paths

seq_num = 0


class Opcode(enum.IntEnum):
    """
    Opcodes for FTP commands
    """

    NONE = 0
    TERMINATE_SESSION = 1
    RESET_SESSION = 2
    LIST_DIRECTORY = 3
    OPEN_FILE_RO = 4
    READ_FILE = 5
    CREATE_FILE = 6
    WRITE_FILE = 7
    REMOVE_FILE = 8
    CREATE_DIRECTORY = 9
    REMOVE_DIRECTORY = 10
    OPEN_FILE_WO = 11
    TRUNCATE_FILE = 12
    RENAME = 13
    CALC_FILE_CRC32 = 14
    BURST_READ_FILE = 15
    # Drone responses
    ACK_RESPONSE = 128
    NAK_RESPONSE = 129


class NakErrorCode(enum.IntEnum):
    """
    Error codes for FTP commands
    """

    NONE = 0  # No Error
    FAIL = 1  # Unknown failure
    FAIL_ERRNO = 2  # Command failed, Err number sent back in PayloadHeader.data[1]
    INVALID_DATA_SIZE = 3  # Payload size is invalid
    INVALID_SESSION = 4  # Session is not currently open
    NO_SESSIONS_AVAILABLE = 5  # All available sessions are in use
    EOF = 6  # Offset past end of file for ListDirectory and ReadFile commands
    UNKNOWN_CMD = 7  # Unknown command / Opcode
    FILE_EXISTS = 8  # File/Directory already exists
    FILE_PROTECTED = 9  # File/Directory is write protected
    FILE_NOT_FOUND = 10  # File/Directory is not found


class FTPMessage:
    """
    FTP Payload structure and converter to bytes
        seq_num (int): Sequence number. | index 0-1 | range 0-65535.
        session (int): Session ID. | index 2 | range 0-255.
        opcode (Opcode): FTP command opcode | index 3 | range 0-255.
        size (int): Size of the payload. | index 4 | range 0-255.
        req_opcode (Opcode): Requested opcode. | index 5 | range 0-255.
        offset (int): Offset in the file. | index 8-11.
        data (bytes): Payload data. | index 12-251.
    """

    def __init__(
        self,
        seq_num: int,
        session: int,
        opcode: Opcode,
        size: int,
        req_opcode: Opcode,
        offset: int,
        data: bytes,
    ) -> None:
        # Validate input parameters
        if not (0 <= seq_num <= 65535):
            raise ValueError("seq_num must be in range 0-65535")
        if not (0 <= session <= 255):
            raise ValueError("session must be in range 0-255")
        if not isinstance(opcode, Opcode):
            raise TypeError("opcode must be an instance of Opcode")
        if not (0 <= size <= 255):
            raise ValueError("size must be in range 0-255")
        if not isinstance(req_opcode, Opcode):
            raise TypeError("req_opcode must be an instance of Opcode")
        if not (0 <= offset <= 0xFFFFFFFF):
            raise ValueError("offset must be in range 0-4294967295 (32-bit unsigned int)")
        if not isinstance(data, bytes):
            raise TypeError("payload must be of type bytes")
        if len(data) > MAX_PAYLOAD_SIZE:
            raise ValueError(f"Payload size exceeds {MAX_PAYLOAD_SIZE} bytes")

        self.seq_num = seq_num
        self.session = session
        self.opcode = opcode
        self.size = size
        self.req_opcode = req_opcode
        self.offset = offset
        self.data = data

    @classmethod
    def from_bytes(cls, response_payload: bytes) -> "FTPMessage":
        """
        Create FTPMessage instance from raw bytes
        """
        seq_num = struct.unpack("<H", response_payload[0:2])[0]
        session = response_payload[2]
        opcode = Opcode(response_payload[3])
        size = response_payload[4]
        req_opcode = Opcode(response_payload[5])
        offset = struct.unpack("<I", response_payload[8:12])[0]
        data = response_payload[12 : 12 + size]

        return cls(seq_num, session, opcode, size, req_opcode, offset, data)

    def to_bytes(self) -> bytearray:
        ftp_payload = bytearray(251)
        ftp_payload[0:2] = struct.pack("<H", self.seq_num)
        ftp_payload[2] = self.session
        ftp_payload[3] = self.opcode
        ftp_payload[4] = self.size
        ftp_payload[5] = self.req_opcode
        ftp_payload[6] = 0  # burst_complete
        ftp_payload[7] = 0  # padding
        ftp_payload[8:12] = struct.pack("<I", self.offset)
        ftp_payload[12 : 12 + len(self.data)] = self.data
        return ftp_payload

    def send_ftp_command(self, connection: mavutil.mavlink_connection) -> None:
        """
        Send an FTP command to the vehicle.
        """

        payload = self.to_bytes()

        connection.mav.file_transfer_protocol_send(
            target_network=0,
            target_system=connection.target_system,
            target_component=connection.target_component,
            payload=payload,
        )


def receive_ftp_message(seq_num: int, timeout: float) -> Tuple[bool, FTPMessage]:
    """
    Receive an FTP message from the vehicle for read command
    """
    response = vehicle.recv_match(
        type="FILE_TRANSFER_PROTOCOL", blocking=True, timeout=timeout
    )  # Wait for ACK response from drone

    if response is None:
        # No response received
        print("ERROR: NO RESPONSE RECEIVED")
        return False, None

    return_payload = FTPMessage.from_bytes(response_payload)

    if return_payload.seq_num != seq_num + 1:
        print("ERROR: Sequence number mismatch")
        return False, return_payload

    if return_payload.opcode != Opcode.ACK_RESPONSE:  # Check for error - NAK Response
        error = NakErrorCode(return_payload.data[0])
        print("ERROR CODE: {error}, ERROR MESSAGE: {error.name}")

        if error == NakErrorCode.FAIL_ERRNO:
            # Err number sent back in PayloadHeader.data[1] for FAIL_ERRNO
            err_num = return_payload.payload[1]
            print(f"ERROR: Command failed with file-system error number {err_num}")
        return False, return_payload
    return True, return_payload


vehicle = mavutil.mavlink_connection(CONNECTION_ADDRESS, baud=57600)
vehicle.wait_heartbeat()
print("heartbeat received")
if vehicle:
    print("CONNECTED...")
else:
    print("DISCONNECTED...")

ftp_payload = FTPMessage(
    seq_num=seq_num,
    session=0,
    opcode=Opcode.OPEN_FILE_RO,
    size=len(FILE_PATH),
    req_opcode=Opcode.NONE,
    offset=0,
    data=FILE_PATH,
)

# open file for reading session
ftp_payload.send_ftp_command(vehicle)

read_done, response_payload = receive_ftp_message(seq_num, TIMEOUT)

if not read_done:
    # No response received
    sys.exit()

# If drone receives a message with the same seq_num then it assumes ACK/NAK response was lost and resends the message
seq_num = response_payload.seq_num + 1

# placeholder for file data in chunks
file_data = b""
offset = 0
file_size = struct.unpack("<I", response_payload.data)[0]

if read_done and response_payload.size == 4:
    chunk_read_done = True
    # read file in chunks until NAK response with EOF is received
    while chunk_read_done:
        ftp_payload = FTPMessage(
            seq_num=seq_num,
            session=response_payload.session,
            opcode=Opcode.READ_FILE,
            size=CHUNK_SIZE,
            req_opcode=Opcode.NONE,
            offset=offset,
            data=b"",
        )
        ftp_payload.send_ftp_command(vehicle)

        chunk_read_done, chunk_response_payload = receive_ftp_message(seq_num, TIMEOUT)

        seq_num = chunk_response_payload.seq_num + 1
        chunk_data = chunk_response_payload.data
        file_data += chunk_data
        offset += len(chunk_data)

# print entire file data
print(file_data.decode("utf-8", errors="ignore"), end="")

# Terminate read session
ftp_payload = FTPMessage(
    seq_num=seq_num,
    session=response_payload.session,
    opcode=Opcode.TERMINATE_SESSION,
    size=0,
    req_opcode=Opcode.NONE,
    offset=0,
    payload=b"",
)

ftp_payload.send_ftp_command(vehicle)
print("\nEND OF FILE")

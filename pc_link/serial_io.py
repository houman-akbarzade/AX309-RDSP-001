"""PC serial-port adapter using the same S02/R1 codec as software tests.

Can connect to CP2102GM once FPGA firmware exists. Not tested on AX309.
"""
from __future__ import annotations
from collections import deque
import time
from .codec import PacketError, Frame, StreamParser, Type
from .session import PCSession
from .arq import ReliableEndpoint, RetryExhausted


class UARTStream:
    def __init__(self, port_like):
        self.io = port_like
        self.parser = StreamParser()
        self.received = deque()
        self.bytes_written = 0

    def write(self, wire: bytes) -> None:
        n = self.io.write(wire)
        if n != len(wire):
            raise OSError(f"short UART write {n}/{len(wire)} bytes")
        self.bytes_written += n

    def read_frame(self, wait_s: float) -> Frame | None:
        deadline = time.monotonic() + wait_s
        while time.monotonic() < deadline:
            if self.received:
                return self.received.popleft()
            # Physical serial port must have short, bounded read timeout.
            chunk = self.io.read(256)
            if chunk:
                self.received.extend(self.parser.feed(chunk))
        if self.received:
            return self.received.popleft()
        self.parser.reset_partial()  # timeout rejects incomplete frame
        return None


def connect_serial_port(port: str, baud: int = 115200) -> UARTStream:
    """Optional runtime dependency: pyserial. No port is opened by import."""
    try:
        import serial
    except ImportError as exc:
        raise RuntimeError("Install pyserial on the host PC") from exc
    device = serial.Serial(port=port, baudrate=baud, bytesize=serial.EIGHTBITS,
                           parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                           timeout=0.05, rtscts=False, xonxoff=False)
    device.reset_input_buffer()
    device.reset_output_buffer()
    return UARTStream(device)


def handshake(uart: UARTStream, pc: PCSession, wait_s: float = 2.0) -> None:
    uart.write(pc.start())
    while pc.state != "ACTIVE":
        inbound = uart.read_frame(wait_s)
        if inbound is None:
            uart.write(pc.timeout())  # identical HELLO/ACTIVATE bytes on retry
            continue
        if inbound.type != Type.SESSION_CONTROL:
            continue
        out = pc.receive(inbound.encode())
        if out is not None:
            uart.write(out)
    if pc.activation_count != 1:
        raise PacketError("handshake activation count invalid")


def send_stop_and_wait(uart: UARTStream, ep: ReliableEndpoint,
                       kind: Type, payload: bytes, apply=None,
                       wait_s: float = 2.0) -> None:
    """Send one reliable application frame and wait for exact ACK.

    This does not automatically decide CPI_ABORT on exhausted retries:
    terminal disposition belongs to the higher-level CPI controller.
    """
    uart.write(ep.send(kind, payload))
    while ep.outstanding is not None:
        f = uart.read_frame(wait_s)
        if f is None:
            uart.write(ep.timeout())
            continue
        reply = ep.receive(f, apply)
        for packet in reply.replies:
            uart.write(packet)
    return None

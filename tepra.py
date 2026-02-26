# 2026, modified by ekspla to use with CPython/Bleak.
# This is a modified version based on [tepra-lite-esp32](https://github.com/puhitaku/tepra-lite-esp32)

import binascii
from bleak import BleakScanner, BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
import time
import asyncio
from typing import Optional, Tuple

min_width = 84
height = 64  # px
AWAIT_NEW_DATA = bytearray(b'AwaitNewData')
TARGET_NAME = ('LR30', 'TepraBLE')


def new_logger(name):
    def _log(fmt, *o):
        print('[{:08.3f}] {}'.format(time.time(), name), fmt.format(*o))
    return _log


def hexstr(b: bytearray):
    return str(binascii.hexlify(bytes(b)))


def p(*b):
    return bytearray(bytes(b))


class Tepra:
    def __init__(self):
        # Service and characteristics
        #self._battery_chr = '0x2A19'
        #self._print_svc = '0000FFF0-0000-1000-8000-00805F9B34FB'
        self._tx = '0000FFF2-0000-1000-8000-00805F9B34FB'
        self._rx = '0000FFF1-0000-1000-8000-00805F9B34FB'
        self.notification_data = bytearray()
        self._log = new_logger('TEPRA  :')

    def create_notification_handler(self):
        async def notification_handler(sender: BleakGATTCharacteristic, data: bytearray):
            self.notification_data = data

        return notification_handler

    async def start_notify(self, client: BleakClient, uuid: BleakGATTCharacteristic):
        try:
            await client.start_notify(uuid, self.create_notification_handler())
        except Exception as e:
            self._log('Failed to start notifications: {}', e)

    async def discover_device(self):
        self._log('Scanning for Bluetooth devices...')
        async with BleakScanner() as scanner:
            async def lookup_device():
                async for bd, ad in scanner.advertisement_data():
                    #print(f' {bd!r} with {ad!r}')
                    found = (bd.name or '').startswith(TARGET_NAME) or (ad.local_name or '').startswith(TARGET_NAME)
                    if found: return bd
            try:
                device = await asyncio.wait_for(lookup_device(), timeout=30)
            except asyncio.TimeoutError:
                return None
            self._log('Found {}', device)
            return device

    async def write(
        self, client: BleakClient, tx_data: bytearray, delay: float = 0.1
    ) -> bool:
        """Write without response"""
        try:
            await client.write_gatt_char(self._tx, tx_data, False)
        except Exception as e:
            self._log('Failed to write tx_data to characteristic: {}', e)
            return False
        await asyncio.sleep(delay)
        return True

    async def write_wait_notification(
        self, client: BleakClient, tx_data: bytearray, delay: float = 0.1
    ) -> Optional[bytearray]:
        """Write without response and wait for a notification"""
        self.notification_data == AWAIT_NEW_DATA
        await self.write(client, tx_data, delay)
        rx_data = await self.wait_notification()
        return rx_data

    async def wait_notification(self) -> Optional[bytearray]:
        """Wait for a notification from the characteristic"""
        async def check_notification():
            while self.notification_data == AWAIT_NEW_DATA:
                await asyncio.sleep(0.01)
        try:
            await asyncio.wait_for(check_notification(), timeout=10)
        except asyncio.TimeoutError:
            self._log('Timeout in awaiting notification.')
            return None
        return self.notification_data

    async def get_ready(self, client: BleakClient, depth: int = 0) -> bool:
        recv = None
        recv = await self.write_wait_notification(client, p(0xF0, 0x5A), 0.1)

        if recv is None:
            return False
        self._log('Recv: {}', hexstr(recv))

        if depth < -3 or depth > 3:
            raise ValueError('invalid depth: {}'.format(depth))

        d = 0x10 - depth if depth < 0 else 0x00 + depth
        self._log('Depth: {} ({:02x})', depth, d)

        recv = await self.write_wait_notification(client, p(0xF0, 0x5B, d, 0x06), 0.05)

        if recv is None:
            return False
        self._log('Recv: {}', hexstr(recv))

        return True

    async def print_lr30(self, client: BleakClient, b: bytes, d: int) -> Tuple[bool, str]:
        ret = await self._print(client, b, d)
        return ret

    async def _print(self, client: BleakClient, b: bytes, d: int) -> Tuple[bool, str]:
        if len(b) % 16 != 0:
            return False, 'insufficient length, image data length must be aligned to 16'

        # Get ready
        recv = await self.get_ready(client, depth=d)
        self._log('Get ready: {}', recv)
        if recv is None:
            return False, 'failed to get ready'

        i = 1
        err = ''

        for ofs in range(0, len(b) - 1, 16):
            self.notification_data = AWAIT_NEW_DATA
            # Print until EOF
            # The stream returns 16 bytes or shorter bytes if there are no body to read
            buf = bytearray(
                (
                    0xF0,
                    0x5C,
                    b[ofs + 6],
                    b[ofs + 7],
                    b[ofs + 4],
                    b[ofs + 5],
                    b[ofs + 2],
                    b[ofs + 3],
                    b[ofs + 0],
                    b[ofs + 1],
                    b[ofs + 14],
                    b[ofs + 15],
                    b[ofs + 12],
                    b[ofs + 13],
                    b[ofs + 10],
                    b[ofs + 11],
                    b[ofs + 8],
                    b[ofs + 9],
                )
            )

            await self.write(client, buf, 0.05)

            if i % 6 == 0:
                self._log('Wait for a notification...')
                await self.wait_notification()
            else:
                await asyncio.sleep(0.02)

            i += 1

        # End sending lines
        rx_data = await self.write_wait_notification(client, p(0xF0, 0x5D, 0x00), 0.05)
        log_data = hexstr(rx_data) if rx_data is not None else 'None'
        self._log('End sending lines: {}', log_data)

        self._log('Waiting for the print to finish...')
        done = False
        while not done:
            rx_data = await self.write_wait_notification(client, p(0xF0, 0x5E), 0.05)
            if rx_data is None: return False, 'received an invalid reply: None'
            elif len(rx_data) < 4:
                self._log('Received an invalid reply: {}', hexstr(rx_data))
                return False, 'received an invalid reply: ' + hexstr(rx_data)
            done = rx_data[2] != 0x01

        self._log('Done!')
        return True, err

    async def run(self, depth: int, encoded: bytes):
        device = await self.discover_device()
        if not device:
            self._log('TEPRA Lite was not found.')
            return

        async with BleakClient(device.address, timeout=60.0) as client:
            if client.is_connected:
                self._log('Connected to {}', device.name)
                await asyncio.sleep(1)

                # indication=False, notification=True
                # Notifications are stopped automatically on disconnect.
                await self.start_notify(client, self._rx)

                # Print labels here.
                success, reason = await self.print_lr30(client, b=encoded, d=depth)
                if not success:
                    self._log('Failed to print: {}', reason)
                self._log('Disconnected.')

            else:
                self._log('Failed to connect to TEPRA Lite.')

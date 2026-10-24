"""Connect to Anker BLE devices: confer, subscribe, telemetry."""

from __future__ import annotations

import asyncio
from datetime import datetime
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from bleak import BleakClient
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from cryptography.hazmat.primitives.asymmetric.ec import (
    ECDH,
    SECP256R1,
    EllipticCurvePublicKey,
    derive_private_key,
)

from .frame import Frame, parse_tlv, split_frame, tlv_to_str
from .scan import DiscoveredDevice, describe_gatt_targets
from .uuids import UUID_FAMILIES, match_uuid_family, normalize_uuid

log = logging.getLogger(__name__)

PRIVATE_KEY_HEX = "7dfbea61cd95cee49c458ad7419e817f1ade9a66136de3c7d5787af1458e39f4"
BASE_TIMESTAMP_HEX = "42ad8c69"

NEGOTIATION_COMMANDS = {
    0: bytes.fromhex(
        "ff0936000300010001a10442ad8c69a22462326463306231372d623735642d346162662d626136652d656337633939376332336537b9"
    ),
    1: bytes.fromhex(
        "ff093d000300010003a10442ad8c69a22462326463306231372d623735642d346162662d626136652d656337633939376332336537a30120a40200f064"
    ),
    2: bytes.fromhex(
        "ff0936000300010029a10442ad8c69a22462326463306231372d623735642d346162662d626136652d65633763393937633233653791"
    ),
    3: bytes.fromhex(
        "ff0940000300010005a10443ad8c69a22462326463306231372d623735642d346162662d626136652d656337633939376332336537a30120a40200f0a50140fa"
    ),
    4: bytes.fromhex(
        "ff094c000300010021a140060ea168f232aedb37fb2d120c49180329ac72ab5ec3eb8fd30a2f252dc5e151dabccd9b1dc1e288704ca760a0d8c918e5c94823a1f609a4bf07fb4c33ee219085"
    ),
    5: bytes.fromhex(
        "ff095a000300014022580bc0532a53c739adf3da7b994a7b5f221bcc16bab6392c215cb4faaf41d9d58e2c81c016e474c78eed5569147cb74a1f22ca2b3fad2e209dbbcfbdaca352034a6c479f055f68581b5f1e22348809f526"
    ),
}

NEGOTIATION_REPLIES = {
    "0801": 1,
    "0803": 2,
    "0829": 3,
    "0805": 4,
    "0821": 5,
}

SESSION_PATTERNS = {"03000f", "03010f", "030111"}
TELEMETRY_CMDS = {"4300", "c402", "c405", "c421", "c900", "0300"}
CMD_SUBSCRIBE = bytes.fromhex("4200")
SUBSCRIBE_PAYLOAD = bytes.fromhex("a10121")


@dataclass
class DeviceIdentity:
    product_name: str | None = None
    firmware: str | None = None
    serial: str | None = None
    mac_or_id: str | None = None
    raw: dict[str, bytes] = field(default_factory=dict)


@dataclass
class SessionSnapshot:
    identity: DeviceIdentity
    telemetry: dict[str, bytes]
    telemetry_cmd: str | None = None
    notifications: int = 0


class AnkerBleClient:
    """Connect + ECDH confer + optional MagGo/Prime-style subscribe."""

    def __init__(
        self,
        target: BLEDevice | DiscoveredDevice | str,
        *,
        family: str | None = None,
        adapter: str | None = None,
    ) -> None:
        if isinstance(target, DiscoveredDevice):
            self._device = target.device
            self.address = target.address
            self.name = target.name
            self.family = family or target.family
        elif isinstance(target, BLEDevice):
            self._device = target
            self.address = target.address
            self.name = target.name
            self.family = family
        else:
            self._device = None
            self.address = target
            self.name = None
            self.family = family

        self._adapter = adapter
        self._client: BleakClient | None = None
        self.write_uuid: str | None = None
        self.notify_uuid: str | None = None
        self.service_uuid: str | None = None
        self._shared_secret: bytes | None = None
        self._negotiation_timestamp: float | None = None
        self._last_packet_at: float | None = None
        self._notifications: list[bytes] = []
        self._frame_queue: asyncio.Queue[Frame] = asyncio.Queue()
        self._on_frame: Callable[[Frame], None] | None = None
        self._notify_started = False
        self.identity = DeviceIdentity()
        self.telemetry: dict[str, bytes] = {}
        self.telemetry_cmd: str | None = None
        self.telemetry_map = {}

    @property
    def connected(self) -> bool:
        return bool(self._client and self._client.is_connected)

    @property
    def negotiated(self) -> bool:
        return self.connected and self._shared_secret is not None

    async def connect(self, timeout: float = 20.0) -> None:
        kwargs: dict = {"timeout": timeout}
        if self._adapter:
            kwargs["adapter"] = self._adapter
        address_or_device = self._device or self.address
        self._client = BleakClient(address_or_device, **kwargs)
        log.info("connecting to %s (%s)…", self.address, self.name)
        await self._client.connect()
        await self._resolve_characteristics()
        log.info(
            "connected  family=%s  write=%s  notify=%s",
            self.family or "?",
            self.write_uuid,
            self.notify_uuid,
        )

    async def disconnect(self) -> None:
        if self._client and self._client.is_connected:
            try:
                if self.notify_uuid and self._notify_started:
                    await self._client.stop_notify(self.notify_uuid)
            except BleakError:
                pass
            await self._client.disconnect()
        self._shared_secret = None
        self._notify_started = False
        log.info("disconnected from %s", self.address)

    async def _resolve_characteristics(self) -> None:
        assert self._client is not None
        services = self._client.services
        discovered = [normalize_uuid(s.uuid) for s in services]

        family = self.family or match_uuid_family(discovered)
        if family is None:
            write_uuids = {
                normalize_uuid(c.uuid)
                for s in services
                for c in s.characteristics
            }
            for key, uuids in UUID_FAMILIES.items():
                if normalize_uuid(uuids["write"]) in write_uuids:
                    family = key
                    break
        if family is None:
            family = "8C85"

        self.family = family
        targets = describe_gatt_targets(family)
        assert targets is not None
        self.service_uuid = targets["service"]
        self.write_uuid = targets["write"]
        self.notify_uuid = targets["notify"]

        char_uuids = {
            normalize_uuid(c.uuid): c
            for s in services
            for c in s.characteristics
        }
        if normalize_uuid(self.write_uuid) not in char_uuids:
            for char in char_uuids.values():
                props = set(char.properties)
                if "write" in props or "write-without-response" in props:
                    self.write_uuid = char.uuid
                    break
        if normalize_uuid(self.notify_uuid) not in char_uuids:
            for char in char_uuids.values():
                if "notify" in char.properties or "indicate" in char.properties:
                    self.notify_uuid = char.uuid
                    break

    def list_gatt(self) -> list[str]:
        assert self._client is not None
        lines: list[str] = []
        for service in self._client.services:
            lines.append(f"SERVICE {service.uuid}")
            for char in service.characteristics:
                props = ",".join(char.properties)
                lines.append(f"  CHAR  {char.uuid}  [{props}]")
        return lines

    async def start_notifications(self) -> None:
        assert self._client and self.notify_uuid
        if self._notify_started:
            return
        await self._client.start_notify(self.notify_uuid, self._on_notify)
        self._notify_started = True
        log.info("subscribed to %s", self.notify_uuid)

    def _on_notify(self, _handle: int, data: bytearray) -> None:
        packet = bytes(data)
        self._last_packet_at = time.time()
        self._notifications.append(packet)
        log.debug("notify %d bytes: %s", len(packet), packet.hex())
        if not packet.startswith(b"\xff\x09"):
            return
        try:
            frame: Frame = split_frame(packet)
        except Exception:
            log.exception("failed to parse FF09 notification")
            return
        log.info(
            "frame pattern=%s cmd=%s payload_len=%d",
            frame.pattern.hex(),
            frame.cmd.hex(),
            len(frame.payload),
        )
        if self._on_frame:
            self._on_frame(frame)
        self._handle_session_frame(frame)
        self._frame_queue.put_nowait(frame)

    def _handle_session_frame(self, frame: Frame) -> None:
        if frame.pattern.hex() not in SESSION_PATTERNS:
            return
        if not self._shared_secret:
            return
        cmd = frame.cmd.hex()
        payload = frame.payload
        candidates = [payload]
        # Solix multi-fragment telemetry sometimes prefixes a fragment byte
        if payload and (len(payload) - 1) % 16 == 0:
            candidates.append(payload[1:])
        for body in candidates:
            try:
                plain = self.decrypt(body)
                params: dict[str, bytes] = parse_tlv(plain)
                self.telemetry = params
                self.telemetry_cmd = cmd
                log.info("telemetry cmd=%s tlv=%s", cmd, tlv_to_str(params))
                try:

                    from .telemetry import parse_telemetry_fixed
                    telemetry = parse_telemetry_fixed(params)
                    if cmd == '4300':
                        print(datetime.now())
                        print(telemetry)
                    self.telemetry_map[frame] = telemetry
                except Exception:
                    pass
                return
            except Exception:
                continue
        log.debug("could not decrypt session frame cmd=%s len=%d",
                  cmd, len(payload))

    async def write_raw(self, data: bytes, response: bool = False) -> None:
        assert self._client and self.write_uuid
        await self._client.write_gatt_char(self.write_uuid, data, response=response)
        log.debug("wrote %d bytes to %s", len(data), self.write_uuid)

    def _complete_ecdh(self, payload: bytes) -> None:
        params = parse_tlv(payload)
        if "a1" not in params:
            log.warning("ECDH stage missing a1 public key: %s",
                        tlv_to_str(params))
            return
        device_pub = b"\x04" + params["a1"]
        private_value = int(PRIVATE_KEY_HEX, 16)
        private_key = derive_private_key(private_value, SECP256R1())
        public_key = EllipticCurvePublicKey.from_encoded_point(
            SECP256R1(), device_pub)
        self._shared_secret = private_key.exchange(ECDH(), public_key)
        log.info(
            "ECDH ok  key=%s…  iv=%s…",
            self._shared_secret[:4].hex(),
            self._shared_secret[16:20].hex(),
        )

    def _capture_identity(self, payload: bytes) -> None:
        params = parse_tlv(payload)
        self.identity.raw = params

        def _ascii(key: str) -> str | None:
            raw = params.get(key)
            if not raw:
                return None
            try:
                return raw.decode("ascii", errors="ignore").strip("\x00") or None
            except Exception:
                return None

        self.identity.product_name = _ascii("a2")
        self.identity.firmware = _ascii("a3")
        self.identity.serial = _ascii("a4")
        # a5 often mixes MAC bytes + SN suffix
        if "a5" in params and len(params["a5"]) >= 6:
            mac = params["a5"][:6]
            self.identity.mac_or_id = ":".join(f"{b:02X}" for b in mac)
        log.info(
            "identity product=%r fw=%r sn=%r",
            self.identity.product_name,
            self.identity.firmware,
            self.identity.serial,
        )

    async def start_confer(self, timeout: float = 60.0) -> bool:
        if not self.connected:
            raise RuntimeError("not connected")

        self._shared_secret = None
        self.telemetry = {}
        self._notifications.clear()
        while not self._frame_queue.empty():
            self._frame_queue.get_nowait()

        await self.start_notifications()
        log.info("starting confer (stage 0)")
        await self.write_raw(NEGOTIATION_COMMANDS[0])

        deadline = time.time() + timeout
        last_kick = time.time()
        while time.time() < deadline:
            if self._shared_secret is not None:
                await asyncio.sleep(0.5)
                log.info("confer complete")
                return True

            try:
                frame = await asyncio.wait_for(self._frame_queue.get(), timeout=1.0)
            except TimeoutError:
                silent = self._last_packet_at is None and time.time() - last_kick > 10
                stalled = (
                    self._last_packet_at is not None
                    and time.time() - self._last_packet_at > 15
                )
                if silent or stalled:
                    log.warning("no negotiation progress — resending stage 0")
                    await self.write_raw(NEGOTIATION_COMMANDS[0])
                    last_kick = time.time()
                continue

            if frame.pattern.hex() != "030001":
                continue

            cmd = frame.cmd.hex()
            stage = NEGOTIATION_REPLIES.get(cmd)
            if stage is None:
                log.warning("unexpected negotiation cmd=%s", cmd)
                continue

            if cmd == "0829":
                self._negotiation_timestamp = time.time()
                self._capture_identity(frame.payload)
            if cmd == "0821":
                self._complete_ecdh(frame.payload)

            log.info("negotiation reply cmd=%s -> send stage %d", cmd, stage)
            await self.write_raw(NEGOTIATION_COMMANDS[stage])

        log.error("confer timed out")
        return False

    def decrypt(self, payload: bytes) -> bytes:
        if not self._shared_secret:
            raise RuntimeError("no session key")
        data = payload
        # CBC length trick: if len % 16 == 15, prepend is handled by caller sometimes
        if len(data) % 16 != 0:
            raise ValueError(
                f"ciphertext length {len(data)} not multiple of 16")
        cipher = AES.new(
            self._shared_secret[:16], AES.MODE_CBC, iv=self._shared_secret[16:]
        )
        return unpad(cipher.decrypt(data), 16)

    def encrypt(self, payload: bytes) -> bytes:
        if not self._shared_secret:
            raise RuntimeError("no session key")
        cipher = AES.new(
            self._shared_secret[:16], AES.MODE_CBC, iv=self._shared_secret[16:]
        )
        return cipher.encrypt(pad(payload, 16))

    def _rolling_timestamp(self) -> bytes:
        if self._negotiation_timestamp is None:
            self._negotiation_timestamp = time.time()
        elapsed = int(time.time() - self._negotiation_timestamp)
        base = int.from_bytes(bytes.fromhex(BASE_TIMESTAMP_HEX), "little")
        return (base + elapsed).to_bytes(4, "little")

    async def send_command(self, cmd: bytes, payload: bytes) -> None:
        """Send encrypted session command with rolling timestamp (Solix path)."""
        if not self.negotiated:
            raise RuntimeError("not negotiated")
        stamped = payload + bytes.fromhex("fe0503") + self._rolling_timestamp()
        encrypted = self.encrypt(stamped)
        packet = Frame(
            pattern=bytes.fromhex("03000f"),
            cmd=cmd,
            payload=encrypted,
        ).build()
        await self.write_raw(packet)

    async def subscribe_telemetry(self) -> None:
        """Ask MagGo/Prime-style devices to start streaming telemetry."""
        log.info("sending telemetry subscribe (4200)")
        await self.send_command(CMD_SUBSCRIBE, SUBSCRIBE_PAYLOAD)

    async def listen(self, seconds: float = 10.0) -> list[bytes]:
        if not self.connected:
            raise RuntimeError("not connected")
        start_len = len(self._notifications)
        try:
            await self.start_notifications()
        except BleakError:
            pass
        await asyncio.sleep(seconds)
        return self._notifications[start_len:]

    async def poll_session(
        self,
        *,
        listen_seconds: float = 8.0,
        subscribe: bool = True,
        confer_timeout: float = 60.0,
    ) -> SessionSnapshot:
        """Connect → confer → optional subscribe → collect telemetry → disconnect."""
        already = self.connected
        if not already:
            await self.connect()
        try:
            ok = await self.start_confer(timeout=confer_timeout)
            if not ok:
                raise RuntimeError("confer failed")
            if subscribe:
                await self.subscribe_telemetry()
            await self.listen(listen_seconds)
            return SessionSnapshot(
                identity=self.identity,
                telemetry=dict(self.telemetry),
                telemetry_cmd=self.telemetry_cmd,
                notifications=len(self._notifications),
            )
        finally:
            if not already:
                await self.disconnect()

import nest_asyncio
import asyncio
from bleak import BleakScanner, BleakClient

nest_asyncio.apply()

# UUIDs and Globals
CHARACTERISTIC_UUID_NOTIF = "1A2B"  # Notify characteristic
CHARACTERISTIC_UUID_RXTX  = "DEAD"  # Read/Write characteristic
client = None  # Global client variable

async def notification_handler(sender, data):
    """Handles notifications from the server."""
    print(f"Notification from {sender}: {data.decode('utf-8')}")

async def connect_to_device(device_name="NimBLE-Arduino"):  #ilo_BLE_(name)  #ilo_BLE_default
    """Scan and connect to the BLE device."""
    global client
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover()

    for device in devices:
        if device.name == device_name:
            print(f"Found device: {device.name} ({device.address})")
            client = BleakClient(device.address)
            await client.connect()
            if client.is_connected:
                print("Connected to the ESP32 BLE server.")
                return True
            else:
                print("Failed to connect to the ESP32 BLE server.")
                return False

    print("ESP32 device not found.")
    return False


async def read_characteristic():
    """Read the value of the RXTX characteristic."""
    global client
    if not client or not client.is_connected:
        print("No active BLE connection.")
        return None

    print(f"Reading '{CHARACTERISTIC_UUID_RXTX}' characteristic...")
    value = await client.read_gatt_char(CHARACTERISTIC_UUID_RXTX)
    print(f"Value: {value.decode('utf-8')}")
    return value


async def write_characteristic(data):
    """Write data to the RXTX characteristic."""
    global client
    if not client or not client.is_connected:
        print("No active BLE connection.")
        return False

    print(f"Writing to '{CHARACTERISTIC_UUID_RXTX}' characteristic...")
    await client.write_gatt_char(CHARACTERISTIC_UUID_RXTX, data)
    print("Value written.")
    return True


async def start_notifications():
    """Start notifications for the NOTIF characteristic."""
    global client
    if not client or not client.is_connected:
        print("No active BLE connection.")
        return False

    print(f"Subscribing to notifications from '{CHARACTERISTIC_UUID_NOTIF}' characteristic...")
    await client.start_notify(CHARACTERISTIC_UUID_NOTIF, notification_handler)
    return True


async def stop_notifications():
    """Stop notifications for the NOTIF characteristic."""
    global client
    if not client or not client.is_connected:
        print("No active BLE connection.")
        return False

    print(f"Stopping notifications for '{CHARACTERISTIC_UUID_NOTIF}' characteristic...")
    await client.stop_notify(CHARACTERISTIC_UUID_NOTIF)
    return True


async def check_ble_connection():
    """Check if the BLE device is connected."""
    global client
    return client.is_connected if client else False


async def main():
    global client
    # Connect to the BLE device
    if not await connect_to_device():
        return

    try:
        # Read the RXTX characteristic
        await read_characteristic()

        # Write to the RXTX characteristic
        await write_characteristic(b"Hello ESP32!")

        # Start notifications from the NOTIF characteristic
        await start_notifications()

        # Keep the connection alive and listen for notifications
        await asyncio.sleep(30)

        # Stop notifications
        await stop_notifications()
    finally:
        print("Disconnecting...")
        if client:
            await client.disconnect()


# Run the event loop
asyncio.run(main())

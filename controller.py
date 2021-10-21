import asyncio
import tkinter as tk
from typing import Union
from bleak import discover, BleakClient

from utils import *


class Controller:
    def __init__(self, client: BleakClient):
        self.client = client

        self.battery: Union[BatteryState, None] = None
        self.temperature: Union[float, None] = None
        self.setting_temperature: Union[float, None] = None
        self.state: Union[State, None] = None
        self.color: Union[Color, None] = None
        self.temperature_scale = TemperatureScale.Celsius

        self.running = False

        self.gui: Union[tk.Frame, None] = None

    async def start(self):
        self.running = True

        # write value to turn off Ember's bluetooth led
        await self.client.write_gatt_char(Request.TemperatureScale.as_uuid,
                                          await self.client.read_gatt_char(Request.TemperatureScale.as_uuid))

        await self.client.start_notify(Request.Notification.as_uuid, self.notify_callback())

        await asyncio.gather(self.set_schedule(), self.initial_fetch_values())

    async def start_with_gui(self, frame: tk.Frame):
        self.running = True

        self.gui = frame

        await self.client.start_notify(Request.Notification.as_uuid, self.notify_callback())
        await self.client.write_gatt_char(Request.TemperatureScale.as_uuid,
                                          await self.client.read_gatt_char(Request.TemperatureScale.as_uuid))

        await asyncio.gather(self.set_schedule(), self.initial_fetch_values(True))

    async def fetch_battery_state(self):
        value = await self.client.read_gatt_char(Request.Battery.as_uuid)
        self.battery = parse_battery(value)

    async def fetch_temperature(self):
        value = await self.client.read_gatt_char(Request.Temperature.as_uuid)
        self.temperature = decode_temperature(value)

    async def fetch_setting_temperature(self):
        value = await self.client.read_gatt_char(Request.SettingTemperature.as_uuid)
        self.setting_temperature = decode_temperature(value)

    async def set_setting_temperature(self, value: float):
        await self.client.write_gatt_char(Request.SettingTemperature.as_uuid, encode_temperature(value))
        self.setting_temperature = value

    async def fetch_state(self):
        value = await self.client.read_gatt_char(Request.State.as_uuid)
        self.state = State(value[0])

    async def fetch_color(self):
        value = await self.client.read_gatt_char(Request.LightColor.as_uuid)
        self.color = parse_color(value)

    async def set_color(self, color: Color):
        await self.client.write_gatt_char(Request.LightColor.as_uuid, color.as_bytearray)
        self.color = color

    async def fetch_temperature_scale(self):
        value = await self.client.read_gatt_char(Request.TemperatureScale.as_uuid)
        self.temperature_scale = TemperatureScale(value[0])

    async def set_temperature_scale(self, scale: TemperatureScale):
        await self.client.write_gatt_char(Request.TemperatureScale.as_uuid, scale.as_bytearray)
        self.temperature_scale = scale

    async def set_schedule(self):
        while True:
            if not self.running:
                break
            await self.fetch_state()
            await self.fetch_setting_temperature()
            await asyncio.sleep(1)

    async def initial_fetch_values(self, run_updater=False):
        await self.fetch_state()
        await self.fetch_color()
        await self.fetch_temperature_scale()
        await self.fetch_setting_temperature()
        await self.fetch_temperature()
        await self.fetch_battery_state()

        async def updater():
            while self.running and self.gui.alive:
                self.gui.update_()
                self.gui.update()
                await asyncio.sleep(1 / 15)
            await self.quit()

        if run_updater:
            await asyncio.gather(updater())

    async def quit(self):
        print('quitting...')
        self.running = False
        await self.client.disconnect()

    def notify_callback(self):
        async def callback(_: int, data: bytearray) -> None:
            if not self.running:
                return await self.client.stop_notify(Request.Notification.as_uuid)
            notification = NotificationValue(data[0])
            print(notification)

            if (notification is NotificationValue.BatteryChargeChange or
                    notification is NotificationValue.OnCoaster or
                    notification is NotificationValue.OffCoaster):
                await self.fetch_battery_state()

            elif (notification is NotificationValue.TemperatureChange or
                  notification is NotificationValue.HeatingStateChange):
                await self.fetch_temperature()

        return callback

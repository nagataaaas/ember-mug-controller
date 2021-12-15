import asyncio
import tkinter as tk
from typing import Union
from bleak import discover, BleakClient
from bleak.exc import BleakError
from datetime import datetime, timedelta
from plyer import notification
from functools import wraps
from warnings import warn
from utils import *


def ble_error_catch(func):
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_inner(self, *args, **kwargs):
            try:
                return await func(self, *args, **kwargs)
            except (RuntimeError, BleakError):
                warn(f"'{func.__name__}' was failed because of Bluetooth error.")
        return async_inner

    else:
        @wraps(func)
        def inner(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except (RuntimeError, BleakError):
                warn(f"'{func.__name__}' was failed because of Bluetooth error.")
        return inner


class Controller:
    notify_interval = 180  # won't notify until after 180 seconds from last notification

    def __init__(self, client: BleakClient, notify_when_complete=False):
        self.client = client

        self.battery: Union[BatteryState, None] = None
        self.temperature: Union[float, None] = None
        self.setting_temperature: Union[float, None] = None
        self.state: Union[State, None] = None
        self.color: Union[Color, None] = None
        self.temperature_scale = TemperatureScale.Celsius

        self.notify_when_complete = notify_when_complete
        self.last_notify: Union[datetime, None] = None

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

    def notify(self):
        last = self.last_notify
        self.last_notify = datetime.now()
        if last is not None and last > datetime.now() - timedelta(seconds=self.notify_interval):
            return

        if self.temperature_scale == TemperatureScale.Celsius:
            temp = '{}°C'.format(self.setting_temperature)
        else:
            temp = '{}°F'.format(int(TemperatureConversion.c2f(self.setting_temperature)))
        notification.notify(title='Your Drink is Waiting For You!',
                            message='Your drink is waiting for you to drink!. It\'s nice and warm {}!'.format(temp),
                            app_name='Ember Mug Controller')

    @ble_error_catch
    async def fetch_battery_state(self):
        value = await self.client.read_gatt_char(Request.Battery.as_uuid)
        self.battery = parse_battery(value)

    @ble_error_catch
    async def fetch_temperature(self):
        value = await self.client.read_gatt_char(Request.Temperature.as_uuid)
        self.temperature = decode_temperature(value)

    @ble_error_catch
    async def fetch_setting_temperature(self):
        value = await self.client.read_gatt_char(Request.SettingTemperature.as_uuid)
        self.setting_temperature = decode_temperature(value)

    @ble_error_catch
    async def set_setting_temperature(self, value: float):
        await self.client.write_gatt_char(Request.SettingTemperature.as_uuid, encode_temperature(value))
        self.setting_temperature = value

    @ble_error_catch
    async def fetch_state(self):
        value = await self.client.read_gatt_char(Request.State.as_uuid)
        state = State(value[0])
        if state == State.Poured:
            await self.set_setting_temperature(max(self.setting_temperature, 50.0))
        if state == State.Keeping and self.state != State.Keeping and self.notify_when_complete:
            self.notify()
        self.state = state

    @ble_error_catch
    async def fetch_color(self):
        value = await self.client.read_gatt_char(Request.LightColor.as_uuid)
        self.color = parse_color(value)

    @ble_error_catch
    async def set_color(self, color: Color):
        await self.client.write_gatt_char(Request.LightColor.as_uuid, color.as_bytearray)
        self.color = color

    @ble_error_catch
    async def fetch_temperature_scale(self):
        value = await self.client.read_gatt_char(Request.TemperatureScale.as_uuid)
        self.temperature_scale = TemperatureScale(value[0])

    @ble_error_catch
    async def set_temperature_scale(self, scale: TemperatureScale):
        await self.client.write_gatt_char(Request.TemperatureScale.as_uuid, scale.as_bytearray)
        self.temperature_scale = scale

    @ble_error_catch
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
        @ble_error_catch
        async def callback(_: int, data: bytearray) -> None:
            if not self.running:
                return await self.client.stop_notify(Request.Notification.as_uuid)
            notification = NotificationValue(data[0])

            if (notification is NotificationValue.BatteryChargeChange or
                    notification is NotificationValue.OnCoaster or
                    notification is NotificationValue.OffCoaster):
                await self.fetch_battery_state()

            elif (notification is NotificationValue.TemperatureChange or
                  notification is NotificationValue.HeatingStateChange):
                await self.fetch_temperature()

        return callback

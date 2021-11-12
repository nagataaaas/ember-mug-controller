from enum import IntEnum, Enum

CharacteristicBase = 'FC5400{:02x}-236C-4C94-8FA9-944A3E5353FA'
EMBER_MANUFACTURER_CODE = b'\x81'


class Temperature:
    def __init__(self, value: float, scale: str = 'celsius'):
        # Ember uses celsius for internal processing
        self.value = value
        self.scale = scale

    @classmethod
    def from_fahrenheit(cls, fahrenheit: float):
        return cls(fahrenheit, 'fahrenheit')

    @classmethod
    def from_celsius(cls, celsius: float):
        return cls(celsius)

    def to_fahrenheit(self):
        if self.scale == 'fahrenheit':
            return self
        return Temperature(TemperatureConversion.c2f(self.value), 'fahrenheit')

    def to_celsius(self):
        if self.scale == 'celsius':
            return self
        return Temperature(TemperatureConversion.f2c(self.value), 'celsius')

    def __repr__(self):
        return 'Temperature(value={!r}, scale={!r})'.format(self.value, self.scale)


class TemperatureConversion:
    @staticmethod
    def f2c(fahrenheit: float) -> float:
        return (fahrenheit - 32) * 5 / 9

    @staticmethod
    def c2f(celsius: float) -> float:
        return (celsius * 9 / 5) + 32


class Character:
    def __init__(self, characteristics: int, readable: bool = False, writable: bool = False, notify: bool = False):
        self.characteristics = characteristics
        self.readable = readable
        self.writable = writable
        self.notify = notify

    @property
    def as_uuid(self) -> str:
        return CharacteristicBase.format(self.characteristics)

    def __repr__(self):
        return 'Character(characteristics={!r}, readable={!r}, ' \
               'writable={!r}, notify={!r})'.format(self.characteristics,
                                                    self.readable,
                                                    self.writable,
                                                    self.notify)


class NotificationValue(IntEnum):
    BatteryChargeChange = 0x01
    OnCoaster = 0x02
    OffCoaster = 0x03

    TemperatureChange = 0x05
    Poured = 0x07  # maybe
    HeatingStateChange = 0x08


class State(Enum):
    Accept = 0x00  # maybe
    Empty = 0x01
    Poured = 0x02  # maybe
    Off = 0x03
    Cooling = 0x04
    Heating = 0x05
    Keeping = 0x06
    FinishDrinking = 0x07  # maybe


class TemperatureScale(IntEnum):
    Celsius = 0
    Fahrenheit = 1

    @property
    def as_bytearray(self) -> bytearray:
        return bytearray.fromhex('{:02}'.format(self.value))


class Color:
    def __init__(self, r: int, g: int, b: int, a: int = 255):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    @property
    def as_bytearray(self) -> bytearray:
        return bytearray([self.r, self.g, self.b, self.a])

    @property
    def as_rgb(self) -> str:
        return '#{:02x}{:02x}{:02x}'.format(self.r, self.g, self.b)

    @property
    def as_rgba(self) -> str:
        return '#{:02x}{:02x}{:02x}{:02x}'.format(self.r, self.g, self.b, self.a)

    def __repr__(self):
        return 'Color(r={!r}, g={!r}, b={!r}, a={!r})'.format(self.r, self.g, self.b, self.a)


class Request:
    Temperature = Character(0x02, readable=True)
    SettingTemperature = Character(0x03, readable=True, writable=True)
    TemperatureScale = Character(0x04, readable=True, writable=True)
    Battery = Character(0x07, readable=True)
    Notification = Character(0x12, notify=True)

    State = Character(0x08, readable=True)

    LightColor = Character(0x14, readable=True, writable=True)  # 0xrrggbbaa


class BatteryState:
    def __init__(self, battery_charge: int, is_charging: bool):
        self.battery_charge = battery_charge
        self.is_charging = is_charging

    def __repr__(self):
        return 'BatteryState(battery_charge={!r}, is_charging={!r})'.format(self.battery_charge, self.is_charging)


def decode_temperature(value: bytearray) -> float:
    return int.from_bytes(value, byteorder='little') / 100


def encode_temperature(value: float) -> bytearray:
    return bytearray(round(value*100).to_bytes(length=2, byteorder='little'))


def parse_battery(value: bytearray) -> BatteryState:
    battery = value[0]
    is_charging = bool(value[1])
    return BatteryState(battery, is_charging)


def parse_color(value: bytearray) -> Color:
    return Color(*value)


if __name__ == '__main__':
    print(decode_temperature(bytearray(b'\x92\t')))
    print(encode_temperature(24.5))
    print(Color(0, 0, 255, 255).as_bytearray)
    print(TemperatureScale.Celsius.as_bytearray)

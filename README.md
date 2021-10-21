# Ember Mug Controller

controller implemented in `controller.py`.

```python
import asyncio
from controller import Controller

from Bleak import BleakClient

async with BleakClient('EMBER ADDRESS') as client:
    control = Controller(client)
    await control.start()
```

to use controller.

# GUI
`$ python main.py` to run GUI. Make sure you installed all requirements using `$ pip install -r requirements.txt`.

> Note: Only tested on Windows11

![demo](https://github.com/nagataaaas/ember-mug-controller/blob/main/static/asset/screenshot1.png?raw=true)

## On Title Bar...
- Click '°C' or '°F' to toggle Celsius and Fahrenheit
- Click '📎' to toggle topmost(Force to being in the front).

## On Body...
- Click LED on mug to choose LED color.
- The illustration on the mug changes depending on its state.
- Click Heat and Ice icon to change setting temperature.
- Current Temperature(upper) and Setting Temperature(Bottom).
- Show current State(Empty, Off, Heating, Keeping, etc.).

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
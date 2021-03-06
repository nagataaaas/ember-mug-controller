from utils import *
import tkinter as tk
import asyncio
from bleak import discover, BleakClient
from controller import Controller
from gui import Application


async def main():
    devices = await discover()
    for d in devices:
        if EMBER_MANUFACTURER_CODE in d.metadata.get('manufacturer_data', {}):
            user_input = input('Device {!r} found. Is this ember mug? Y/N [Y]: '.format(d.name)) or 'y'
            if user_input.lower() == 'y':
                ember = d
                break
    else:
        print('Ember mug is not found. Exiting...')
        return

    async with BleakClient(ember.address) as client:
        x = client.is_connected
        print("Connected: {0}".format(x))
        try:
            # await client.pair()
            cont = Controller(client, True)
            root = tk.Tk()
            root.protocol("WM_DELETE_WINDOW", lambda: asyncio.gather(cont.quit()))
            root.title('Ember Mug Controller')
            gui = Application(cont, master=root)
            await cont.start_with_gui(gui)
        except Exception as e:
            import traceback
            traceback.print_exc()
            await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())

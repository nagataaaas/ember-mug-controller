import asyncio
import tkinter as tk
from utils import Color, State, BatteryState, TemperatureScale, TemperatureConversion
from PIL import ImageTk

from tkcolorpicker import askcolor

ORANGE = '#ffba2e'
DORANGE = '#b28220'
GRAY = '#555555'


class Application(tk.Frame):
    def __init__(self, controller: 'Controller', master=None):
        super().__init__(master)

        self.master = master
        self.master.overrideredirect(True)  # turns off title bar, geometry
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        self.master.geometry('500x355+{}+{}'.format(screen_width - 500, screen_height - 335 - 100))
        self.master.configure(bg=ORANGE)
        self.master.resizable(False, False)
        self.topmost = False  # only to know if root is minimized

        self.controller = controller
        self.pack()
        self.create_widgets()

        self.prev_state = State.Empty

        self.prev_battery = BatteryState(100, False)

        self.alive = True

        self.temperature_scale = TemperatureScale.Celsius

    def close(self):
        print('called')
        self.alive = False
        self.master.destroy()
        print('destroy')

    def create_widgets(self):
        # title bar

        def temperature_scale():
            if self.controller.temperature_scale == TemperatureScale.Celsius:
                asyncio.gather(self.controller.set_temperature_scale(TemperatureScale.Fahrenheit))
                self.temperature_scale_button.config(text=" °F ")
            else:
                asyncio.gather(self.controller.set_temperature_scale(TemperatureScale.Celsius))
                self.temperature_scale_button.config(text=" °C ")

        def topmost():
            if self.topmost:
                self.topmost = False
                self.master.attributes("-topmost", False)
                self.topmost_button['bg'] = ORANGE
            else:
                self.topmost = True
                self.master.attributes("-topmost", True)
                self.topmost_button['bg'] = DORANGE

        def get_pos(event):
            xwin = self.master.winfo_x()
            ywin = self.master.winfo_y()
            startx = event.x_root
            starty = event.y_root

            ywin = ywin - starty
            xwin = xwin - startx

            def move_window(event):  # runs when window is dragged
                self.master.config(cursor="fleur")
                self.master.geometry(f'+{event.x_root + xwin}+{event.y_root + ywin}')

            def release_window(event):  # runs when window is released
                self.master.config(cursor="arrow")

            self.title_bar.bind('<B1-Motion>', move_window)
            self.title_bar.bind('<ButtonRelease-1>', release_window)
            self.title_bar_title.bind('<B1-Motion>', move_window)
            self.title_bar_title.bind('<ButtonRelease-1>', release_window)

        self.title_bar = tk.Frame(self.master, bg=ORANGE, relief='flat', bd=0, highlightthickness=0)

        self.close_button = tk.Button(self.title_bar, text='  ×  ', command=self.close, bg=ORANGE, padx=2, pady=2,
                                 font=("calibri", 13), bd=0, fg='white', highlightthickness=0)
        self.topmost_button = tk.Button(self.title_bar, text=' 📎 ', command=topmost, bg=ORANGE, padx=2, pady=2, bd=0,
                                   fg='white', font=("calibri", 13), highlightthickness=0)
        self.temperature_scale_button = tk.Button(self.title_bar,
                                             text=' °C ' if self.controller.temperature_scale == TemperatureScale.Celsius else ' °F ',
                                             command=temperature_scale, bg=ORANGE, padx=2, pady=2, bd=0,
                                             fg='white', font=("calibri", 13), highlightthickness=0)
        self.title_bar_title = tk.Label(self.title_bar, text='Ember Mug Controller', bg=ORANGE, bd=0, fg='white',
                                   font=("helvetica", 10), highlightthickness=0)
        self.title_bar.pack(fill='x')
        self.close_button.pack(side='right', ipadx=7, ipady=1)
        self.topmost_button.pack(side='right', ipadx=7, ipady=1)
        self.temperature_scale_button.pack(side='right', ipadx=7, ipady=1)
        self.title_bar_title.pack(side='left', padx=10)

        def changex_on_hovering(event):
            self.close_button['bg'] = 'red'

        def returnx_to_normalstate(event):
            self.close_button['bg'] = ORANGE

        def changem_size_on_hovering(event):
            self.topmost_button['bg'] = GRAY

        def returnm_size_on_hovering(event):
            if self.topmost:
                self.topmost_button['bg'] = DORANGE
            else:
                self.topmost_button['bg'] = ORANGE

        def changes_size_on_hovering(event):
            self.temperature_scale_button['bg'] = GRAY

        def returns_size_on_hovering(event):
            self.temperature_scale_button['bg'] = ORANGE

        self.title_bar.bind('<Button-1>', get_pos)  # so you can drag the window from the title bar
        self.title_bar_title.bind('<Button-1>', get_pos)  # so you can drag the window from the title

        # button effects in the title bar when hovering over buttons

        self.close_button.bind('<Enter>', changex_on_hovering)
        self.close_button.bind('<Leave>', returnx_to_normalstate)
        self.topmost_button.bind('<Enter>', changem_size_on_hovering)
        self.topmost_button.bind('<Leave>', returnm_size_on_hovering)
        self.temperature_scale_button.bind('<Enter>', changes_size_on_hovering)
        self.temperature_scale_button.bind('<Leave>', returns_size_on_hovering)

        # body
        self.pixelVirtual = tk.PhotoImage(width=1, height=1)

        self.canvas = tk.Canvas(self.master, width=500, height=325, bd=-2)
        self.canvas.pack(expand=False)

        self.battery = tk.StringVar()
        self.temperature = tk.StringVar()
        self.setting_temperature = tk.StringVar()
        self.state = tk.StringVar()

        self.battery_label = tk.Label(self.canvas, textvariable=self.battery, bg='white', fg=GRAY,
                                      font=('Arial Black', 13), pady=0)
        self.temperature_label = tk.Label(self.canvas, textvariable=self.temperature, bg=ORANGE, fg='white',
                                          font=('Arial Black', 50))
        self.setting_temperature_label = tk.Label(self.canvas, textvariable=self.setting_temperature, bg=ORANGE,
                                                  fg='white', font=('Arial Black', 20))
        self.state_label = tk.Label(self.canvas, textvariable=self.state, bg=ORANGE,
                                    fg='white', font=('Arial Black', 20))

        self.battery_label.place(x=115, y=295, anchor='center')
        self.temperature_label.place(x=370, y=85, anchor="center")
        self.setting_temperature_label.place(x=365, y=155, anchor="center")
        self.state_label.place(x=360, y=195, anchor="center")

        self.heat_img = ImageTk.PhotoImage(file='static/icon/heat.png')
        self.heat_button = tk.Button(self.canvas, width=60,
                                     height=65, command=self.change_setting_temperature(2),
                                     borderwidth=0, relief='sunken')
        self.heat_button.config(image=self.heat_img)
        self.heat_button.place(x=420, y=230)

        self.weak_heat_img = ImageTk.PhotoImage(file='static/icon/weak_heat.png')
        self.weak_heat_button = tk.Button(self.canvas, width=43,
                                          height=43, command=self.change_setting_temperature(0.5),
                                          borderwidth=0, relief='sunken')
        self.weak_heat_button.config(image=self.weak_heat_img)
        self.weak_heat_button.place(x=377, y=243)

        self.cool_img = ImageTk.PhotoImage(file='static/icon/cool.png')
        self.cool_button = tk.Button(self.canvas, width=60,
                                     height=70, command=self.change_setting_temperature(-2),
                                     borderwidth=0, relief='sunken')
        self.cool_button.config(image=self.cool_img)
        self.cool_button.place(x=245, y=230)

        self.weak_cool_img = ImageTk.PhotoImage(file='static/icon/weak_cool.png')
        self.weak_cool_button = tk.Button(self.canvas, width=43,
                                          height=43, command=self.change_setting_temperature(-0.5),
                                          borderwidth=0, relief='sunken')
        self.weak_cool_button.config(image=self.weak_cool_img)
        self.weak_cool_button.place(x=310, y=243)

        self.color_button = tk.Button(self.canvas, width=30, height=10, text='', borderwidth=0, relief='flat',
                                      bg='#ff0000', command=self.pick_color, image=self.pixelVirtual)
        self.color_button.place(x=96, y=218)

        self.background = ImageTk.PhotoImage(file='static/background.png')
        self.background_canvas = self.canvas.create_image(250, 162, image=self.background)

        self.normal = ImageTk.PhotoImage(file='static/icon/normal.png')
        self.charging = ImageTk.PhotoImage(file='static/icon/charging.png')
        self.low = ImageTk.PhotoImage(file='static/icon/low.png')
        self.battery_canvas = self.canvas.create_image(115, 265, image=self.normal)

        self.empty = ImageTk.PhotoImage(file='static/mug/empty.png')
        self.heating = ImageTk.PhotoImage(file='static/mug/heating.png')
        self.complete = ImageTk.PhotoImage(file='static/mug/complete.png')
        self.mug_canvas = self.canvas.create_image(125, 135, image=self.empty)

    def update_(self):
        if self.controller.battery is not None:
            self.battery.set('{}%'.format(self.controller.battery.battery_charge))
            if self.prev_battery.is_charging != self.controller.battery.is_charging:
                if self.controller.battery.is_charging:
                    self.canvas.itemconfig(self.battery_canvas, image=self.charging)
                elif self.controller.battery.battery_charge > 20:
                    self.canvas.itemconfig(self.battery_canvas, image=self.normal)
                else:
                    self.canvas.itemconfig(self.battery_canvas, image=self.low)
            elif not self.controller.battery.is_charging:
                if self.prev_battery.battery_charge <= 20 and self.controller.battery.battery_charge > 20:
                    self.canvas.itemconfig(self.battery_canvas, image=self.normal)
                elif self.prev_battery.battery_charge > 20 and self.controller.battery.battery_charge <= 20:
                    self.canvas.itemconfig(self.battery_canvas, image=self.low)
            self.prev_battery = self.controller.battery
        if self.controller.temperature is not None:
            if self.temperature_scale is TemperatureScale.Celsius:
                self.temperature.set('{}°'.format(self.controller.temperature))
            else:
                self.temperature.set('{}°'.format(int(TemperatureConversion.c2f(self.controller.temperature))))
        if self.controller.setting_temperature is not None:
            if self.temperature_scale is TemperatureScale.Celsius:
                self.setting_temperature.set('{}°'.format(self.controller.setting_temperature))
            else:
                self.setting_temperature.set('{}°'.format(int(TemperatureConversion.c2f(self.controller.setting_temperature))))
        if self.controller.temperature_scale != self.temperature_scale:
            if self.controller.temperature_scale == TemperatureScale.Celsius:
                self.temperature_scale_button.config(text=" °C ")
            else:
                self.temperature_scale_button.config(text=" °F ")
            self.temperature_scale = self.controller.temperature_scale
        if self.controller.color is not None:
            self.color_button.configure(bg=self.controller.color.as_rgb)
        if self.controller.state is not None:
            self.state.set(self.controller.state.name)

            if self.controller.state in (State.Empty, State.FinishDrinking) and \
                    self.prev_state in (State.Poured, State.Cooling, State.Heating, State.Keeping):
                self.canvas.itemconfig(self.mug_canvas, image=self.empty)
                self.prev_state = self.controller.state

            elif self.prev_state in (State.Empty, State.FinishDrinking, State.Cooling, State.Keeping) and \
                    self.controller.state in (State.Poured, State.Heating, State.Off):
                self.canvas.itemconfig(self.mug_canvas, image=self.heating)
                self.prev_state = self.controller.state

            elif self.prev_state in (State.Empty, State.FinishDrinking, State.Off, State.Heating) and \
                    self.controller.state in (State.Cooling, State.Keeping):
                self.canvas.itemconfig(self.mug_canvas, image=self.complete)
                self.prev_state = self.controller.state

    def change_setting_temperature(self, offset: float):
        def wrapper():
            set_temp = self.controller.setting_temperature
            if offset < 0:
                if set_temp == 0:
                    return
                if set_temp + offset < 50:
                    asyncio.gather(self.controller.set_setting_temperature(0))
                else:
                    asyncio.gather(self.controller.set_setting_temperature(set_temp + offset))
            else:
                if set_temp == 0:
                    set_temp += 49.5

                if set_temp + offset > 62.5:
                    asyncio.gather(self.controller.set_setting_temperature(62.5))
                else:
                    asyncio.gather(self.controller.set_setting_temperature(set_temp + offset))

        return wrapper

    def pick_color(self):
        color = askcolor((255, 255, 0), self, alpha=True)
        if not color:
            return
        asyncio.gather(self.controller.set_color(Color(*color[0])))

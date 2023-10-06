#!/usr/bin/env python3

# Telldus Price Control
# By Conny Holm 2023

import tkinter as tk
from tkinter import ttk, Listbox, Canvas
import requests
import configparser
from datetime import datetime, timedelta
import os
import json
import subprocess


class MainWindowBuilder(tk.Tk):

    def __init__(self):
        super().__init__()

        config = configparser.ConfigParser()
        config.read('settings.ini')
        self.area = str(config['APP']['AREA'])
        self.el_api = str(config['APP']['EL_API'])
        self.request_timeout = int(config['APP']['REQUEST_TIMEOUT'])
        self.delayseconds = int(config['APP']['UPDATE_INTERVAL']) * 1000
        self.tell_api = str(config['APP']['TELL_API'])
        self.auth = str(config['APP']['AUTH'])
        self.timeout = int(config['APP']['REQUEST_TIMEOUT'])
        self.mode = str(config['APP']['MODE'])
        self.override = str(config['APP']['OVERRIDE'])
        self.oncommand = str(config['APP']['ON_COMMAND'])
        self.offcommand = str(config['APP']['OFF_COMMAND'])

        self.triggerprice = 0
        self.triggerprice_tomorrow = 0
        self.lastaction = ''
        self.controldevicelist = {}
        self.pricenow = 0
        self.scaling = 1
        self.highestprice = 0
        self.date_to_fetch = ''

        self.tomorrows_price = ''
        self.todays_price = ''

        self.title("Telldus Price Control v0.5")

        # Create left frame with Telldus stuff
        self.telldus = ttk.Labelframe(self, text="Telldus")

        self.api_text = ttk.Label(self.telldus, text="Tellstick IP:")
        self.api_entry = ttk.Entry(self.telldus)
        self.api_entry.insert(0, self.tell_api)

        self.auth_text = ttk.Label(self.telldus, text="Authorization:")
        self.auth_entry = ttk.Entry(self.telldus)
        self.auth_entry.insert(0, self.auth)

        self.device_text = ttk.Label(self.telldus, text="Device:")
        self.devicelist_text = ttk.Label(self.telldus, text="0 devices found")
        self.device_combo = ttk.Combobox(self.telldus, state="readonly")
        self.device_combo.insert(0, "No devices")
        self.device_combo['values'] = ()
        # self.device_combo['state'] = "READONLY"

        self.telldus.grid(column=0,
                          row=0,
                          padx=5,
                          pady=5,
                          ipady=5,
                          sticky="nw")
        self.api_text.grid(column=0,
                           row=0,
                           sticky="w",
                           padx=10,
                           pady=4)
        self.api_entry.grid(column=1,
                            row=0,
                            columnspan=2,
                            padx=10,
                            pady=4,
                            ipadx=20)
        self.auth_text.grid(column=0,
                            row=1,
                            sticky="w",
                            padx=10,
                            pady=4)
        self.auth_entry.grid(column=1,
                             row=1,
                             columnspan=2,
                             padx=10,
                             pady=4,
                             ipadx=20)

        self.devicelist_text.grid(column=1,
                                  row=3,
                                  columnspan=2,
                                  pady=12)

        self.device_text.grid(column=0,
                              row=4,
                              sticky="w",
                              padx=10,
                              pady=4)
        self.device_combo.grid(column=1,
                               row=4,
                               columnspan=2,
                               padx=0,
                               pady=4,
                               ipadx=12)

        self.on = ttk.Button(self.telldus,
                             text="Turn On",
                             command=self.onbutton)
        self.off = ttk.Button(self.telldus,
                              text="Turn Off",
                              command=self.offbutton)
        self.on.grid(column=1,
                     row=5,
                     sticky="w",
                     padx=8)
        self.off.grid(column=1,
                      row=6,
                      sticky="w",
                      padx=8)

        self.add_btn = ttk.Button(self.telldus,
                                  text="Add",
                                  command=self.add_device)
        self.refresh = ttk.Button(self.telldus,
                                  text="Refresh",
                                  command=self.refresh_devices)
        self.add_btn.grid(column=2, row=5, sticky="e", padx=8)
        self.refresh.grid(column=2, row=6, sticky="e", padx=8)

        self.refresh_devices()

        # List for prices
        self.priceframe = ttk.Labelframe(self, text="Price list")
        self.pricelist = Listbox(self.priceframe, height=24, width=40)

        self.priceframe.grid(column=2,
                             row=0,
                             padx=5,
                             pady=5,
                             ipady=6, rowspan=10, sticky="nw")
        self.pricelist.grid(column=0, row=0, padx=4, pady=4)

        # Price control
        self.avgpriceframe = ttk.Labelframe(self, text="Price control")
        self.arealabel = ttk.Label(self.avgpriceframe, text="Price area:")
        self.areatext = ttk.Label(self.avgpriceframe, text="Unknown")
        self.avgpricelabel = ttk.Label(self.avgpriceframe,
                                       text="Todays avg price:")
        self.avgpricecalc = ttk.Label(self.avgpriceframe, text="Unknown")

        self.avgpriceframe.grid(column=3,
                                row=4,
                                padx=5,
                                pady=9,
                                ipady=10,
                                sticky="nw",
                                columnspan=1,
                                rowspan=6)
        self.arealabel.grid(column=0, row=0, padx=2, pady=0, sticky="w")
        self.areatext.grid(column=1, row=0, padx=2, pady=0, sticky="w")
        self.avgpricelabel.grid(column=0, row=1, padx=10, pady=0, sticky="w")
        self.avgpricecalc.grid(column=1, row=1, padx=10, pady=0, sticky="w")

        # Radiobuttons

        self.controltype = tk.StringVar(None, str(config['APP']['MODE']))
        self.pricefixed = ttk.Radiobutton(self.avgpriceframe,
                                          text="Fixed price",
                                          variable=self.controltype,
                                          value="fixed",
                                          command=self.fixedprice)
        self.priceratio = ttk.Radiobutton(self.avgpriceframe,
                                          text="Best hours",
                                          variable=self.controltype,
                                          value="ratio",
                                          command=self.ratioprice)

        self.pricefixed.grid(column=0, row=2, padx=1, pady=0, sticky="w")
        self.priceratio.grid(column=0, row=3, padx=1, pady=0, sticky="w")

        # Spinboxes
        self.pricefixed_val = tk.StringVar(None, str(config['APP']['PRICE']))
        self.setfixed = ttk.Spinbox(self.avgpriceframe,
                                    from_=0.05,
                                    to=99.0,
                                    textvariable=self.pricefixed_val,
                                    increment=0.05,
                                    command=self.fixedprice)
        self.priceratio_val = tk.StringVar(None, str(config['APP']['RATIO']))
        self.setratio = ttk.Spinbox(self.avgpriceframe,
                                    from_=1,
                                    to=23,
                                    textvariable=self.priceratio_val,
                                    increment=1,
                                    command=self.ratioprice)

        self.setfixed.grid(column=1, row=2, sticky="e", ipadx=2)
        self.setratio.grid(column=1, row=3, sticky="e", ipadx=2)

        # checkbox for override
        self.checkoverride_val = tk.StringVar(None, self.override)
        self.checkoverride = tk.Checkbutton(self.avgpriceframe,
                                            text="Override/Repeat",
                                            variable=self.checkoverride_val,
                                            onvalue='ON',
                                            offvalue='OFF')
        self.checkoverride.grid(column=0, row=4, sticky="w", padx=7, pady=4)

        # Last updated
        self.lastholder = ttk.Frame(self)
        self.lastupdate = ttk.Label(self.lastholder, text="Last update: N/A")
        self.lastholder.grid(column=4, row=6,
                             padx=5,
                             pady=0,
                             sticky="nw",
                             columnspan=1)
        self.lastupdate.grid(column=0, row=0, padx=0, pady=0, sticky="nw")

        # Last action
        self.lastaction_label = ttk.Label(self.lastholder,
                                          text="Last action: N/A")
        self.lastaction_label.grid(column=0,
                                   row=1,
                                   padx=0,
                                   pady=0,
                                   sticky="nw")

        self.lastupdate['text'] = datetime.strftime(datetime.now(),
                                                    "Last update: %H:%M:%S")
        self.lastupdate.after(self.delayseconds, self.timer_loop)

        # List for devices to control
        self.deviceframe = ttk.Labelframe(self, text="Devices to control")
        self.devicelist = Listbox(self.deviceframe, height=8, width=45)
        self.delete_btn = ttk.Button(self.deviceframe,
                                     text="Remove selected",
                                     command=self.remove_device)

        self.deviceframe.grid(column=0,
                              row=1,
                              padx=5,
                              pady=1,
                              rowspan=8,
                              sticky="nw")
        self.devicelist.grid(column=0, row=0, padx=4, pady=4, ipadx=1)
        self.delete_btn.grid(column=0, row=1, sticky="nw", padx=8, pady=8)

        # Custom On commands
        self.customonframe = ttk.Labelframe(self, text="Custom On command")
        self.customonentry = ttk.Entry(self.customonframe)
        self.customonframe.grid(column=4, row=4, padx=5, pady=9, sticky="nw")
        self.customonentry.grid(column=0,
                                row=0,
                                padx=5,
                                pady=5,
                                ipadx=46,
                                columnspan=1)
        self.customonentry.insert(0, self.oncommand)

        # Custom Off commands
        self.customoffframe = ttk.Labelframe(self, text="Custom Off command")
        self.customoffentry = ttk.Entry(self.customoffframe)
        self.customoffframe.grid(column=4, row=5, padx=5, pady=0, sticky="nw")
        self.customoffentry.grid(column=0,
                                 row=0,
                                 padx=5,
                                 pady=5,
                                 ipadx=46,
                                 columnspan=1)
        self.customoffentry.insert(0, self.offcommand)

        # Graph
        self.graphheight = 230
        self.graphwidth = 600
        self.graphframe = ttk.Labelframe(self, text="Price graph")
        self.graph = Canvas(self.graphframe,
                            height=self.graphheight,
                            width=self.graphwidth,
                            bg="white")

        self.graphframe.grid(column=3,
                             row=0,
                             padx=5,
                             pady=5,
                             rowspan=4,
                             sticky="nw",
                             columnspan=2)
        self.graph.grid(column=0, row=0, padx=4, pady=4)

    def add_device(self):
        device_string = self.device_combo.get()
        device_id = device_string.split(" ")[0]
        print(f"{device_id} added")

        if device_string == "Select one":
            return

        self.controldevicelist[device_id] = device_string

        self.devicelist.delete(0, 666)
        for device in self.controldevicelist.values():
            self.devicelist.insert(0, device)

    def remove_device(self):
        # device_string = self.device_combo.get()
        selected = self.devicelist.curselection()
        device_string = self.devicelist.get(selected)
        device_id = device_string.split(" ")[0]
        print(f"{device_id} added")

        self.controldevicelist.pop(device_id, None)

        self.devicelist.delete(0, 666)
        for device in self.controldevicelist.values():
            self.devicelist.insert(0, device)

    def fixedprice(self):
        if self.controltype.get() == "fixed":
            self.triggerprice = float(self.pricefixed_val.get())
            self.update_list_today()
            # print(type(self.tomorrows_price))
            if self.tomorrows_price.__class__ == list:
                self.update_list_tomorrow()
            # print(f"fixed: {self.triggerprice}")

        return

    def ratioprice(self):
        if self.controltype.get() == "ratio":

            # todays prices
            prices = []
            for hour in self.todays_price:
                prices.append(float(hour['SEK_per_kWh']))

            prices.sort()
            self.triggerprice = float(prices[int(self.priceratio_val.get())])

            # tomorrows prices
            if self.tomorrows_price.__class__ == list:
                prices = []
                for hour in self.tomorrows_price:
                    prices.append(float(hour['SEK_per_kWh']))

                prices.sort()
                self.triggerprice_tomorrow = \
                    float(prices[int(self.priceratio_val.get())])

        self.update_list_today()
        if self.tomorrows_price.__class__ == list:
            self.update_list_tomorrow()
        return

    def refresh_devices(self):

        dict_data = {}
        # command_request = 'http://' + API_IP + '/api/devices/list'
        command_request = \
            'http://' + self.api_entry.get() + '/api/devices/list'
        headers = {
            'Authorization': self.auth_entry.get()
        }
        try:
            json_data = requests.request("GET",
                                         command_request,
                                         headers=headers,
                                         data='',
                                         timeout=self.timeout)
            dict_data = json_data.json()
            print(dict_data)

        except Exception as e:
            print(e)

        if 'device' not in dict_data:
            print('No devices in response.')
            self.devicelist_text['text'] = "No response."
            self.device_combo.set("No devices")
            self.device_combo['values'] = ""
            return

        if len(dict_data['device']) > 0:
            self.devicelist_text['text'] = \
                str(len(dict_data['device'])) + " devices found"
            device_list = []

            for device in dict_data['device']:

                device_list.append(str(device['id']) + " - " + device['name'])

            self.device_combo.set("Select one")
            self.device_combo['values'] = device_list
        return

    def onbutton(self):
        device_string = self.device_combo.get()
        device_id = device_string.split(" ")[0]
        print(f"{device_id} on")

        command_request =\
            'http://' + self.api_entry.get() + '/api/device/turnOn'
        payload = 'id=' + device_id
        headers = {
            'Authorization': self.auth_entry.get()
        }
        try:
            json_data = requests.request("GET",
                                         command_request,
                                         headers=headers,
                                         params=payload,
                                         timeout=self.timeout)
            dict_data = json_data.json()
            print(dict_data)

        except Exception as e:
            print(e)

        return

    def offbutton(self):
        device_string = self.device_combo.get()
        device_id = device_string.split(" ")[0]
        print(f"{device_id} off")

        command_request = \
            'http://' + self.api_entry.get() + '/api/device/turnOff'
        payload = 'id=' + device_id
        headers = {
            'Authorization': self.auth_entry.get()
        }
        try:
            json_data = requests.request("GET",
                                         command_request,
                                         headers=headers,
                                         params=payload,
                                         timeout=self.timeout)
            dict_data = json_data.json()
            print(dict_data)

        except Exception as e:
            print(e)

        return

    def timer_loop(self):

        time_now = datetime.now()
        date_to_fetch = datetime.strftime(time_now, "%Y/%m-%d")
        setattr(self, 'date_to_fetch', date_to_fetch)
        setattr(self, 'todays_price', self.getprice())

        tomorrow = time_now + timedelta(1)
        date_to_fetch = datetime.strftime(tomorrow, "%Y/%m-%d")
        setattr(self, 'date_to_fetch', date_to_fetch)
        setattr(self, 'tomorrows_price', self.getprice())

        # self.update_list()
        self.ratioprice()   # Run this to update ratio in case of date change

        if self.pricenow < self.triggerprice:
            if self.lastaction == 'ON' and \
                    self.checkoverride_val.get() != 'ON':
                self.lastaction_label['text'] = 'Last action: ON'
                print('Already ON')
            else:
                self.lastaction_label['text'] = 'Last action: Switching ON'
                print('Switching ON')
                self.devices_on()
            self.lastaction = 'ON'
        else:
            if self.lastaction == 'OFF' and\
                    self.checkoverride_val.get() != 'ON':
                self.lastaction_label['text'] = 'Last action: OFF'
                print('Already OFF')
            else:
                self.lastaction_label['text'] = 'Last action: Switching OFF'
                print('Switching OFF')
                self.devices_off()
            self.lastaction = 'OFF'

        self.lastupdate['text'] =\
            datetime.strftime(datetime.now(), "Last update: %H:%M:%S")
        self.after(self.delayseconds, self.timer_loop)

    def devices_on(self):

        if self.customonentry.get():
            print('Executing: ' + self.customonentry.get())
            try:
                subprocess.Popen(self.customonentry.get())
            except Exception:
                pass

        for device_id in self.controldevicelist.keys():

            print(f"{device_id} on")

            command_request =\
                'http://' + self.api_entry.get() + '/api/device/turnOn'
            payload = 'id=' + device_id
            headers = {
                'Authorization': self.auth_entry.get()
            }
            try:
                json_data = requests.request("GET",
                                             command_request,
                                             headers=headers,
                                             params=payload,
                                             timeout=self.timeout)
                dict_data = json_data.json()
                print(dict_data)

            except Exception as e:
                print(e)
        return

    def devices_off(self):

        if self.customoffentry.get():
            print('Executing: ' + self.customoffentry.get())
            try:
                subprocess.Popen(self.customoffentry.get())
            except Exception:
                pass

        for device_id in self.controldevicelist.keys():

            print(f"{device_id} off")

            command_request =\
                'http://' + self.api_entry.get() + '/api/device/turnOff'
            payload = 'id=' + device_id
            headers = {
                'Authorization': self.auth_entry.get()
            }
            try:
                json_data = requests.request("GET",
                                             command_request,
                                             headers=headers,
                                             params=payload,
                                             timeout=self.timeout)
                dict_data = json_data.json()
                print(dict_data)

            except Exception as e:
                print(e)
        return

    def update_list_today(self):

        time_now = datetime.now()
        time_to_compare = datetime.strftime(time_now, "%Y-%m-%d    %H:00")

        sum_price = 0
        highest = 0
        lowest = 9999

        # Clear listbox here
        self.pricelist.delete(0, 666)

        # Loop for list
        for index, hour in enumerate(self.todays_price):

            time_parsed = datetime.strptime(hour['time_start'],
                                            "%Y-%m-%dT%H:%M:%S%z")
            time_nice = time_parsed.strftime("%Y-%m-%d    %H:00")

            self.pricelist.insert(index,
                                  str(f"{time_nice}    {hour['SEK_per_kWh']:.2f} SEK"))

            sum_price += hour['SEK_per_kWh']

            if time_to_compare == time_nice:
                self.pricelist.delete(index)
                self.pricelist.insert(index,
                                      str(f"{time_nice}    {hour['SEK_per_kWh']:.2f} SEK    <-- Now"))
                setattr(self, 'pricenow', hour['SEK_per_kWh'])

            if self.triggerprice > hour['SEK_per_kWh']:
                self.pricelist.itemconfigure(index, background='#66ff66')

            if highest < hour['SEK_per_kWh']:
                highest = hour['SEK_per_kWh']

            if lowest > hour['SEK_per_kWh']:
                lowest = hour['SEK_per_kWh']

        avg_price = sum_price / len(self.todays_price)
        self.avgpricecalc['text'] = f"{avg_price:.2f} SEK / KWh"
        setattr(self, "highestprice", highest)
        setattr(self, "lowestprice", lowest)

        if self.tomorrows_price.__class__ == list:
            for index, hour in enumerate(self.tomorrows_price):
                if highest < hour['SEK_per_kWh']:
                    highest = hour['SEK_per_kWh']
            if highest > self.highestprice:
                setattr(self, "highestprice", highest)

        self.graph.delete("all")

        # print(self.highestprice)
        # print(self.lowestprice)

        # Loop for graph
        for index, hour in enumerate(self.todays_price):

            offset = 4
            spacing = 12

            max_height = 0.9

            setattr(self,
                    "scaling",
                    self.graphheight / self.highestprice * max_height)
            # scaling = self.graphheight / hour['SEK_per_kWh']

            bar_start_x = index * spacing + offset

            bar_height = hour['SEK_per_kWh'] * self.scaling
            bar_start_y = self.graphheight - bar_height

            bar_width = 10
            bar_end_x = bar_start_x + bar_width
            bar_end_y = self.graphheight

            if self.triggerprice <= hour['SEK_per_kWh']:
                self.graph.create_rectangle(bar_start_x,
                                            bar_start_y,
                                            bar_end_x,
                                            bar_end_y,
                                            fill="red")

            else:
                self.graph.create_rectangle(bar_start_x,
                                            bar_start_y,
                                            bar_end_x,
                                            bar_end_y,
                                            fill='#66ff66')

        self.graph.create_rectangle(295,
                                    0,
                                    600,
                                    self.graphheight,
                                    fill="light gray",
                                    outline='')
        if not self.tomorrows_price.__class__ == list:
            self.graph.create_text(400,
                                   120,
                                   text="Tomorrows price\nnot yet available",
                                   fill="gray")

        if self.controltype.get() == "fixed":
            startx = 0
            starty = self.graphheight - self.triggerprice * self.scaling
            endx = self.graphwidth
            endy = starty
            self.graph.create_line(startx,
                                   starty,
                                   endx,
                                   endy,
                                   width="2",
                                   fill="blue")

    def update_list_tomorrow(self):

        # Loop for list
        for index, hour in enumerate(self.tomorrows_price):
            print(index)

            time_parsed = datetime.strptime(hour['time_start'],
                                            "%Y-%m-%dT%H:%M:%S%z")
            time_nice = time_parsed.strftime("%Y-%m-%d    %H:00")

            self.pricelist.insert(index + len(self.tomorrows_price) - 1,
                                  str(f"{time_nice}    {hour['SEK_per_kWh']:.2f} SEK"))

            if self.controltype.get() == "ratio":
                if self.triggerprice_tomorrow > hour['SEK_per_kWh']:
                    self.pricelist.itemconfigure(index + len(self.tomorrows_price) - 1,
                                                 background='#66ff66')
            else:
                if self.triggerprice > hour['SEK_per_kWh']:
                    self.pricelist.itemconfigure(index + len(self.tomorrows_price) - 1,
                                                 background='#66ff66')

        # self.graph.delete("all")

        # print(self.highestprice)
        # print(self.lowestprice)

        # Loop for graph
        for index, hour in enumerate(self.tomorrows_price):

            offset = 300
            spacing = 12

            max_height = 0.9

            setattr(self,
                    "scaling",
                    self.graphheight / self.highestprice * max_height)
            # scaling = self.graphheight / hour['SEK_per_kWh']

            bar_start_x = index * spacing + offset

            bar_height = hour['SEK_per_kWh'] * self.scaling
            bar_start_y = self.graphheight - bar_height

            bar_width = 10
            bar_end_x = bar_start_x + bar_width
            bar_end_y = self.graphheight

            if self.controltype.get() == "ratio":
                if self.triggerprice_tomorrow <= hour['SEK_per_kWh']:
                    # fixed or ratio
                    self.graph.create_rectangle(bar_start_x,
                                                bar_start_y,
                                                bar_end_x,
                                                bar_end_y,
                                                fill="red")

                else:
                    self.graph.create_rectangle(bar_start_x,
                                                bar_start_y,
                                                bar_end_x,
                                                bar_end_y,
                                                fill='#66ff66')

            if self.controltype.get() == "fixed":
                if self.triggerprice <= hour['SEK_per_kWh']:
                    # fixed or ratio
                    self.graph.create_rectangle(bar_start_x,
                                                bar_start_y,
                                                bar_end_x,
                                                bar_end_y,
                                                fill="red")

                else:
                    self.graph.create_rectangle(bar_start_x,
                                                bar_start_y,
                                                bar_end_x,
                                                bar_end_y,
                                                fill='#66ff66')

        if self.controltype.get() == "fixed":
            startx = 0
            starty = self.graphheight - self.triggerprice * self.scaling
            endx = self.graphwidth
            endy = starty
            self.graph.create_line(startx,
                                   starty,
                                   endx,
                                   endy,
                                   width="2",
                                   fill="blue")

    def getprice(self):

        log_filename = self.date_to_fetch + '_' + self.area + '.json'
        log_filename = log_filename.replace("/", "-")

        if not os.path.exists('log/'):
            print('making log dir')
            os.mkdir('log')

        if not os.path.isfile('log/' + log_filename):
            print('creating price log file')

            # GET https://www.elprisetjustnu.se/api/v1/prices/2023/01-15_SE3.json
            command_request = \
                self.el_api + self.date_to_fetch + '_' + self.area + '.json'

            try:
                json_data = requests.request("GET",
                                             command_request,
                                             headers='',
                                             data='',
                                             timeout=self.request_timeout)
                # print(json_data)

                if json_data.ok:
                    print('Fetching ' + command_request + ' OK')
                    with open('log/' + log_filename, 'w') as fp:

                        json.dump(json_data.json(), fp)
                        # fp.write(write)
                        return json_data.json()
                        pass

                else:
                    print('Fetching ' +
                          command_request +
                          ' failed: ' +
                          json_data.reason)
                    return

            except requests.exceptions.ConnectionError:
                print("Connection error")

        if os.path.isfile('log/' + log_filename):
            with open(r'log/' + log_filename, 'r') as fp:
                print('Reading from local file ' + log_filename)
                return json.load(fp)


def main():

    mainwindow = MainWindowBuilder()
    # mainwindow.iconbitmap("sausage_icon_211243.ico")

    time_now = datetime.now()
    mainwindow.date_to_fetch = datetime.strftime(time_now, "%Y/%m-%d")
    mainwindow.todays_price = mainwindow.getprice()
    mainwindow.areatext['text'] = mainwindow.area

    tomorrow = time_now + timedelta(1)
    mainwindow.date_to_fetch = datetime.strftime(tomorrow, "%Y/%m-%d")
    mainwindow.tomorrows_price = mainwindow.getprice()

    if mainwindow.mode == 'fixed':
        mainwindow.fixedprice()

    if mainwindow.mode == 'ratio':
        mainwindow.ratioprice()

    mainwindow.mainloop()


#   Main loop
if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, Listbox
import requests
import configparser
from dateutil import parser
from datetime import datetime


class MainWindow(tk.Tk):

    def __init__(self):
        super().__init__()

        config = configparser.ConfigParser()
        config.read('settings.ini')
        tell_api = str(config['APP']['TELL_API'])
        auth = str(config['APP']['AUTH'])
        self.timeout = int(config['APP']['REQUEST_TIMEOUT'])

        self.triggerprice = 0

        self.title("Styr Telldusenheter efter elpriset va")

        # Create left frame with Telldus stuff
        self.telldus = ttk.Labelframe(self, text="Telldus")

        self.api_text = ttk.Label(self.telldus, text="Tellstick IP:")
        self.api_entry = ttk.Entry(self.telldus)
        self.api_entry.insert(0, tell_api)

        self.auth_text = ttk.Label(self.telldus, text="Authorization:")
        self.auth_entry = ttk.Entry(self.telldus)
        self.auth_entry.insert(0, auth)

        self.device_text = ttk.Label(self.telldus, text="Device:")
        self.devicelist_text = ttk.Label(self.telldus, text="0 devices found")
        self.device_combo = ttk.Combobox(self.telldus)
        self.device_combo.insert(0, "No devices")
        self.device_combo['values'] = ()

        self.on = ttk.Button(self.telldus, text="On", command=self.onbutton)
        self.off = ttk.Button(self.telldus, text="Off", command=self.offbutton)
        self.refresh = ttk.Button(self.telldus, text="Refresh devices", command=self.refresh_list)

        self.telldus.grid(column=0, row=0, padx=5, pady=5, ipady=5, sticky="nw")
        self.api_text.grid(column=0, row=0, sticky="w", padx=10, pady=4)
        self.api_entry.grid(column=1, row=0, columnspan=2, padx=10, pady=4)
        self.auth_text.grid(column=0, row=1, sticky="w", padx=10, pady=4)
        self.auth_entry.grid(column=1, row=1, columnspan=2, padx=10, pady=4)

        self.devicelist_text.grid(column=1, row=3, columnspan=2, pady=12)
        self.refresh.grid(column=1, row=2, columnspan=2)

        self.device_text.grid(column=0, row=4, sticky="w", padx=10, pady=4)
        self.device_combo.grid(column=1, row=4, columnspan=2, padx=0, pady=4)
        self.on.grid(column=1, row=5, columnspan=2)
        self.off.grid(column=1, row=6, columnspan=2)

        self.refresh_list()

        # List for prices
        self.priceframe = ttk.Frame(self, borderwidth=0, relief='raised')
        self.pricelist = Listbox(self.priceframe, height=24, width=50)

        self.priceframe.grid(column=2, row=0, padx=5, pady=5, rowspan=10)
        self.pricelist.grid(column=0, row=0, padx=0, pady=0)

        # List for avg price
        self.avgpriceframe = ttk.Labelframe(self, text="Price control")
        self.arealabel = ttk.Label(self.avgpriceframe, text="Price area:")
        self.areatext = ttk.Label(self.avgpriceframe, text="Unknown")
        self.avgpricelabel = ttk.Label(self.avgpriceframe, text="Avg price:")
        self.avgpricecalc = ttk.Label(self.avgpriceframe, text="Unknown")

        # Radiobuttons

        self.controltype = tk.StringVar(None, str(config['APP']['MODE']))
        self.pricefixed = ttk.Radiobutton(self.avgpriceframe, text="Fixed price", variable=self.controltype, value="fixed", command=self.fixedprice)
        self.priceratio = ttk.Radiobutton(self.avgpriceframe, text="Best hours", variable=self.controltype, value="ratio", command=self.ratioprice)

        self.avgpriceframe.grid(column=0, row=1, padx=5, pady=5, ipady=5, sticky="nw", columnspan=2)
        self.arealabel.grid(column=0, row=0, padx=10, pady=0, sticky="w")
        self.areatext.grid(column=1, row=0, padx=10, pady=0, sticky="w")
        self.avgpricelabel.grid(column=0, row=1, padx=10, pady=0, sticky="w")
        self.avgpricecalc.grid(column=1, row=1, padx=10, pady=0, sticky="w")
        self.pricefixed.grid(column=0, row=2, padx=10, pady=0, sticky="w")
        self.priceratio.grid(column=0, row=3, padx=10, pady=0, sticky="w")

        # Spinboxes
        self.pricefixed_val = tk.StringVar(None, str(config['APP']['PRICE']))
        self.setfixed = ttk.Spinbox(self.avgpriceframe, from_=0.05, to=99.0, textvariable=self.pricefixed_val, increment=0.05, command=self.fixedprice)
        self.priceratio_val = tk.StringVar(None, str(config['APP']['RATIO']))
        self.setratio = ttk.Spinbox(self.avgpriceframe, from_=1, to=23, textvariable=self.priceratio_val, increment=1, command=self.ratioprice)

        self.setfixed.grid(column=1, row=2, sticky="e")
        self.setratio.grid(column=1, row=3, sticky="e")

    def fixedprice(self):
        if self.controltype.get() == "fixed":
            self.triggerprice = float(self.pricefixed_val.get())
            update_list(self)
            print(f"fixed: {self.triggerprice}")
        return

    def ratioprice(self):
        if self.controltype.get() == "ratio":

            prices = []
            for hour in self.todays_price:
                prices.append(float(hour['SEK_per_kWh']))

            prices.sort()
            self.triggerprice = float(prices[int(self.priceratio_val.get())])
            update_list(self)
            print(f"ratio: {self.priceratio_val.get()} price: {self.triggerprice}")
        return

    def refresh_list(self):

        dict_data = {}
        # command_request = 'http://' + API_IP + '/api/devices/list'
        command_request = 'http://' + self.api_entry.get() + '/api/devices/list'
        headers = {
            'Authorization': self.auth_entry.get()
        }
        try:
            json_data = requests.request("GET", command_request, headers=headers, data='', timeout=self.timeout)
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
            self.devicelist_text['text'] = str(len(dict_data['device'])) + " devices found"
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

        command_request = 'http://' + self.api_entry.get() + '/api/device/turnOn'
        payload = 'id=' + device_id
        headers = {
            'Authorization': self.auth_entry.get()
        }
        try:
            json_data = requests.request("GET", command_request, headers=headers, params=payload, timeout=self.timeout)
            dict_data = json_data.json()
            print(dict_data)

        except Exception as e:
            print(e)

        return

    def offbutton(self):
        device_string = self.device_combo.get()
        device_id = device_string.split(" ")[0]
        print(f"{device_id} off")

        command_request = 'http://' + self.api_entry.get() + '/api/device/turnOff'
        payload = 'id=' + device_id
        headers = {
            'Authorization': self.auth_entry.get()
        }
        try:
            json_data = requests.request("GET", command_request, headers=headers, params=payload, timeout=self.timeout)
            dict_data = json_data.json()
            print(dict_data)

        except Exception as e:
            print(e)

        return


def update_list(root):
    for index, hour in enumerate(root.todays_price):
        # if root.controltype.get() == "fixed":
        if root.triggerprice > hour['SEK_per_kWh']:
            root.pricelist.itemconfigure(index, background='#66ff66')
        else:
            root.pricelist.itemconfigure(index, background='white')
        # else:
        #     if root.priceratio_price > hour['SEK_per_kWh']:
        #         root.pricelist.itemconfigure(index, background='#66ff66')
        #     else:
        #         root.pricelist.itemconfigure(index, background='white')


def getprice(date, area):

    config = configparser.ConfigParser()
    config.read('settings.ini')
    el_api = str(config['APP']['EL_API'])
    request_timeout = int(config['APP']['REQUEST_TIMEOUT'])

    # GET https://www.elprisetjustnu.se/api/v1/prices/2023/01-15_SE3.json
    command_request = el_api + date + '_' + area + '.json'
    print(command_request)
    try:
        json_data = requests.request("GET", command_request, headers='', data='', timeout=request_timeout)
        return json_data.json()

    except Exception as e:
        print(e)


def main():

    config = configparser.ConfigParser()
    config.read('settings.ini')
    area = str(config['APP']['AREA'])

    time_now = datetime.now()
    time_to_compare = datetime.strftime(time_now, "%Y-%m-%d    %H:00")

    date_to_fetch = datetime.strftime(time_now, "%Y/%m-%d")

    root = MainWindow()

    root.todays_price = getprice(date_to_fetch, area)
    root.areatext['text'] = area

    sum_price = 0

    for index, hour in enumerate(root.todays_price):
        time_parsed = parser.parse(hour['time_start'])
        time_nice = time_parsed.strftime("%Y-%m-%d    %H:00")

        root.pricelist.insert(index, str(f"{time_nice}    {hour['SEK_per_kWh']:.2f} SEK"))

        sum_price += hour['SEK_per_kWh']

        if time_to_compare == time_nice:
            root.pricelist.insert(index, str(f"{time_nice}    {hour['SEK_per_kWh']:.2f} SEK    Current"))
            # root.pricelist.itemconfigure(index, background='#f0f0ff')
            # root.pricelist.itemconfigure(index, background='orange')

    avg_price = sum_price / len(root.todays_price)
    root.avgpricecalc['text'] = f"{avg_price:.2f} SEK / KWh"

    if str(config['APP']['MODE']) == 'fixed':
        root.fixedprice()

    if str(config['APP']['MODE']) == 'ratio':
        root.ratioprice()

    update_list(root)

    root.mainloop()


#   Main loop
if __name__ == "__main__":
    main()

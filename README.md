## !! Please update now - previous version will break in June 2025 !!
Sweden and maybe other Nordic countries will change from an hourly spot price to a new interval of 15 minutes. Read more: https://www.vattenfall.se/fokus/tips-rad/kvartsmatning-och-kvartspris/

Previous versions of Price Control assumes 24 price entries per day and this will cause undefined behaviour after june 2025 when we may get 96 entries.

This current version 25.2 parses the price entries differently and allows for any number of entries per day. Please update asap.

## Electricity Price Control for Telldus Live devices

With electricity prices going crazy in Sweden this program lets you control your Telldus Live-connected smart plugs by the hourly electric price rate. This program is made for Swedish prices in SEK but feel free to modify it for other currencies.

Prices are fetched from the API at https://www.elprisetjustnu.se

##### You will need:
* Telldus Live account
* Telldus TellStick ZNet Lite V2 or similar
* Smart plugs connected to above mentioned
* Windows, Mac or Linux with Python 3 and Internet access
* Per-hour electricity pricing

##### Telldus API token
To connect to the TellStick you will need an access token. Instructions to create one can be found here: https://tellstick-server.readthedocs.io/en/latest/api/authentication.html

Place the token in setting.ini under AUTH in the format "Bearer tokenxxx..."

##### setting.ini
Here you will find all the default settings to be loadaded at startup. Check it out before running the program for the first time.

### Settings
##### Telldus
Here you can test the connection settings and manually control the devices. Selecting a smart plug in the drop down list and clicking "Add" will add the device to the list of price-controlled devices.

##### Price control
* "Fixed price" lets you set a fixed rate under which the added devices will trigger. This value you may need to adjust every day if you want your devices to be triggered.
* "Best hours" is more flexible. Here you can set how many hours per day you want your devices on and the program will find the cheapest hours to activate them.
* "Override/Repeat" checkbox will send the on/off command every update interval, per default every 10 seconds. This overrides other triggers such as Telldus device scheduling, smart switches, etc. Those may change the devices state for a short time, before the price control overrides it. Leaving this setting unchecked makes the price trigger change the state only once, when it detects a change in price.

##### Devices to control
Simply a list of the added devices that will be triggered by the change in rate.

##### Prices
A list of the prices fetched from the API. Green color means devices will be switched On on those hours. The list is only fetched once and stored in the folder /log. If any problems occur with the list, delete the corresponding file in the log folder.

##### Custom On / Off command
Here you can put a custom command to be triggered together with the devices, or alone if no devices are added. For example you can run a custom script that notifies you on state changes. This entry is not parsed or evaluated, only executed blindly.

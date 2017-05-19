# Open Wi-Fi switch
This is a free implementation of firmware for Wi-Fi remote switches Itead Sonoff [Basic](https://www.itead.cc/smart-home/sonoff-dual.html) (In progress) and [Dual](https://www.itead.cc/smart-home/sonoff-wifi-wireless-switch.html) (Ready) written for [Micropython](https://docs.micropython.org/en/latest/esp8266/) 

## Rationale
The devices use vendor's proprietary firmware, Android app and a cloud for interconnection.
Such an approach does not meet neither author's needs nor his philosophy. Any kind of home automation needlessly bound to internet connection and cloud services is a bad practice.
Though electrical part of these devices looks pretty good and ready for daily usage.
That's why the project was written.
## Features: 
- Uses your own MQTT server.
- Can be controlled just by writing a single bit to a proper MQ topic. You can use whatever you want: android apps, scripts etc
- Survives Wi-Fi and MQTT outages
- Handles hardware buttons to control the load.
- Sends health reports to the queue.
## How to use:

1. First of all you need to reflash your device with Micropython.
There are plenty of detailed articles on the net so please use google.
In short, you need to solder a few pins and use RS-232 to TTL(3v) converter.

2. Make changes to a config.py: 
* SSID
* PSK
* MQTT broker IP 
* Write your device's MAC address to the 'devmap' and set a name for it.

3. Copy project files to the root of the device flash.

4. *(Optional)* Connect pins to push-button switches. Your can find one in a local electrical equipment store. I just use a common garage door switch.

5. Install and configure [IoTManager](https://play.google.com/store/apps/details?id=ru.esp8266.iotmanager) android app.

6. Write a persistent MQTT entry to configure your android app. Here's an exmaple(using mosquitto) 
```sh
mosquitto_pub -h <mqtt_host> -r -t "/IoTmanager/<device_name>/config" -m "{\"id\":\"1\",\"page\":\"room1\",\"descr\":\"Top lights\",\"widget\":\"toggle\",\"topic\":\"/IoTmanager/<device_name>/relay_1\",\"color\":\"blue\"}"
```

## Device status
The relay statuses will be published to the following topics:
```
/IoTmanager/<device_name>/relay_<1|2>/status
```
## Control
The simplest way to control a device:

Turn on relay 1:
```sh
mosquitto_pub -h <mqtt_host> -t /IoTmanager/<device_name>/relay_1/control -m 1
```
Turn off relay 2
```sh
mosquitto_pub -h <mqtt_host> -t /IoTmanager/<device_name>/relay_2/control -m 0
```

## Requirements:
- Micropython >1.8.7 build 461
- MQTT server (Mosquitto 1.4.11 is the only tested one)

## Licence:
Apache 2.0

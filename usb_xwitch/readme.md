# USB-Xwitch Python Package

pico controller and communication package

- pico: code flash to board
- commsrepl: controlling command via pico onboard usb with repl communication over py
- commsrpi: communication via UART header (J8) to raspberry pi

## Flash pico controller

Flash pico uses python ```rshell``` to copy files into internal memory

use rshell to flash ./pico files to the board
1. ```pip install rshell``` (need to be in Python environment)
2. ```rshell -p port_name``` (or simply ```rshell``` if this is the only board connected)
    
   e.g.:
   
    Windows: ```rshell -p COMX```

   Linux / macOS: ```rshell -p /dev/tty.usbmodem11201```

3. Copy firmware files:
    - ```cp main.py /pyboard/main.py```
    - ```cp conf.py /pyboard/conf.py```
5. power cycle pico

   ### validation
   1. connect to pico 
      
      Windows: putty -> Serial --> COM port and connect
      
      macOS: ```minicom -D /dev/tty.usbmodem1234546```
   
   2. flip on off of pico onboard led. Visual check on board.
      ```console
      >>> flip_indicator_led()
      ```
   
## Communications

1. Direct commanding over serial 
    - macOS
      - install ```minicom``` (```brew install minicom```)
      - get divece name by: ```ls /dev/tty*```
      - connect device by: ```minicom -D /dev/tty.usbmodel123456```
      - enjoy!
    - Windows
      - install PuTTY
      - open PuTTY, go to serial, enter board port COMx appear in device manager
      - enjoy!
2. As a python package (under construction)
    - install python package 
    ```pip install -e ./usb_xwitch/comms-repl```
    - Working in progress...

## Commands

Commands available via ``` print(__doc__)``` when communication established

Single hub functions:

```set_hub(list)```: set hub 4 channels on/off. format: ```[bool, bool, bool, bool]```

```get_hub()```: get current hub 4 channels in tuple

```set_switch(int)```: set switch to channel 1 / 2. starting from 0

```get_switch()```: get current switch channel

```get_adc(int)```: get current switch bus 1 / 2 volrage reading

```flip_indicator_led()```: flip indicator led to opposite state

```ind_led(bool)```: bool. set indicator led status

Daisy chain hub functions:

```discovery_chain()```: use currrent hub as root hub, discovery all available downstream daisychain-able hubs

```set_hub_chain(*args)```: set daisy chain hubs on/off (bool list). None to escape. e.g. set_hub_chain([True, False, False], None, [True, True, True, True]) set hub0 channel 1 on, channel 2 and 3 off (channel 4 used to chain next hub); keep hub1 unchanged; set hub2 all 4 channels on.

```set_hubs(bool)```: set all hub channels on the chain on / off, except for the channel used for chaining next hub. (default ch4)

```get_hubs()```: get all hubs on off status in a dictionary. dictionary syntax: {channel_no: [bool_list]}

```get_hub_chain(int)```: get a hub channel on off status list by its index number. root hub index starting from 0

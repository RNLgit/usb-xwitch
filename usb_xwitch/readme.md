# USB-Xwitch Python Package

pico controller and communication package

- pico: code flash to pico
- commsrepl: controlling command via pico onboard usb with repl communication over py
- commsrpi: communication via UART header (J8) to raspberry pi

## Flash pico controller

use rshell to flash ./pico/main.py to pico board
1. ```pip install rshell```
2. ```rshell -p port_name```
    
   e.g.:
   
    Windows: ```rshell -p COMX```

   Linux / macOS: ```rshell -p /dev/tty.usbmodem11201```

3. ```cp main.py /pyboard```
4. reboot pico

   ### validation
   1. connect to pico 
      
      Windows: putty -> Serial --> COM port and connect
      
      macOS: ```minicon -D /dev/tty.usbmodem11201```
   
   2. flip on off of pico onboard led. Visual check.
      ```console
      >>> flip_pico_led()
      ```
   
## Command xwitch

1. install python package  
   ```pip install -e ./usb_xwitch/comms-repl```
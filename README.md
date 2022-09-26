# USB Hub

A programmable budget USB 1:2 multiplexer and HUB device (original name usb-xwitch). Features one 1:2 USB 3.1 switch and 4 Ch USB 2.0 remote 
controllable HUB. Controlling via on board micro USB or by Raspberry Pi UART. 

## CAD Setup (KiCad 6.0)

- Open ./sch/usb_xwitch.kicad_pro -> Schematics Editor 
- in Preferences -> Configure Path, add path name: "USB_XWITCH" and path: absolute address of the project (e.g. /Users/runnanl/src/usb-hub)

1. Channel Features

- Switch: USB 3.0 High Speed 1 Mux 2 switching. Additional physical control by push button switch.
- HUB: USB 2.0 HS 1:4 HUB. Individual remote control, power delivery and over current shutdown.
- HUB Expansion: UART daisy chain HUB capability.

2. Command via micro USB serial (default) or use by UART from Raspberry Pi (as a HAT)

## Hardware Overview

![HardwareOverview (to be updated)](./img/usb_xwitch_pcb_v01.jpg)

- CHS: USB3.0 1 mux 2. Port active indications. Switch button.
- CHH: USB2.0 HS 1x upstream USB-B to 4x downstream USB-A ports. Control via commands.
- Raspberry Pi compaticable header (10 Pins).
- Mountable as Raspberry Pi 2/3/4 HAT.

## Software Overview

- pico software
- USB control protocols and commands
- UART control commands

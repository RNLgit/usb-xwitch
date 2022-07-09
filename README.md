# usb-xwitch
A programmable budget usb mux and power cycle device. Features 1x usb switch + 2x usb power cycle up to 5Gbps. Running
standalone or by Raspberry Pi. 

1. Three Channels controllable use ports

- Ch1: USB 3.0 High Speed 1 Mux 2 switching
- Ch2: USB 3.0 High Speed BUS power cycle
- Ch3: USB 3.0 High Speed BUS power cycle

2. Use as Raspberry Pi HAT or standalone

## Hardware Overview

![HardwareOverview](./img/usb_xwitch_pcb_v01.jpg)

- Ch1 (lower side 3 USBs): USB3.0 1 mux 2 with add on switch button
- Ch2 (upper side 2 USBs): USB3.0 bus power cycle by relay
- Ch3 (left side 2 USBs): USB3.0 bus power cycle by relay
- Raspberry Pi controlled
- Can use as a Raspberry Pi 4 HAT. Controllable by Raspberry Pi
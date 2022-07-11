# usb-xwitch
A programmable budget usb mux and power cycle device. Features 1x usb switch + 2x usb power cycle up to 5Gbps. Running
standalone or by Raspberry Pi. 

1. Three Channels controllable use ports

- ChA: USB 3.0 High Speed 1 Mux 2 switching
- ChB: USB 3.0 High Speed BUS power cycle
- ChC: USB 3.0 High Speed BUS power cycle

2. Use as Raspberry Pi HAT or standalone

## Hardware Overview

![HardwareOverview](./img/usb_xwitch_pcb_v01.jpg)

- ChA (lower side 3 USBs): USB3.0 1 mux 2 with add on switch button
- ChB (upper side 2 USBs): USB3.0 bus power cycle by relay
- ChC (left side 2 USBs): USB3.0 bus power cycle by relay
- Raspberry Pi controlled
- Can use as a Raspberry Pi 4 HAT. Controllable by Raspberry Pi
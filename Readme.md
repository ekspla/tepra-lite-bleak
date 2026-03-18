<div align="center">
  <img src="https://github.com/puhitaku/tepra-lite-esp32/blob/master/tepra.jpg?raw=true" width="300px">
  <h1>tepra_bleak_cli</h1>
  <i>A stand alone CPython code to communicate with KING JIM TEPRA Lite LR30 over BLE</i>
</div>


## Preface

2026, modified by [ekspla](https://github.com/ekspla/tepra-lite-bleak) using CPython/Bleak, 
based on codes in [tepra-lite-esp32](https://github.com/puhitaku/tepra-lite-esp32).  

## Introduction

This is a stand alone CPython/[Bleak](https://github.com/hbldh/bleak) version of code to 
communicate with KING JIM TEPRA Lite LR30 *directly* over BLE. No WiFi-BLE repeater (ESP32) is required.  

This version of code **does not work on Linux/BlueZ**[<sup>1</sup>](#note-1) though 
[Bleak](https://github.com/hbldh/bleak), which is a cross-platform software, supports Android, MacOS, 
Windows and Linux. **Confirmed to work on Windows 10 and 11**.

## Install

- Copy `tepra.py` and `tepra_bleak_cli.py` to an appropriate directory.  
- Install dependencies using `requirements.txt`.  
- Edit the default font path (`default_font`) in `tepra_bleak_cli.py`.

## Usage

- Turn on your TEPRA Lite LR30.  

Subcommands:

 - print: print strings, QR code and image

### Print

```
Usage: tepra_bleak_cli.py print [OPTIONS]

Options:
  --preview                     Generate preview.png without printing.
  -f, --font PATH               Path to a font file.
  -S, --fontsize INTEGER RANGE  Font size. [px] (default = 30)  [x>=0]
  -d, --depth INTEGER RANGE     Depth of color. (default = 0)  [-3<=x<=3]
  -m, --message TEXT            Print a text.
  -s, --space TEXT              Leave space between parts. [px]
  -q, --qr TEXT                 Draw a QR code.
  -i, --image TEXT              Paste an image.
  --help                        Show this message and exit.
```

### Print examples

|Options|Output|
|:-|:-:|
|`-m Hello`|<img src="https://github.com/puhitaku/tepra-lite-esp32/blob/master/client/example1.png?raw=true" height=80px>|
|`-S 15 -m Hello`|<img src="https://github.com/puhitaku/tepra-lite-esp32/blob/master/client/example2.png?raw=true" height=80px>|
|`-S 50 -m Hello`|<img src="https://github.com/puhitaku/tepra-lite-esp32/blob/master/client/example3.png?raw=true" height=80px>|
|`-m Hello -m World`|<img src="https://github.com/puhitaku/tepra-lite-esp32/blob/master/client/example4.png?raw=true" height=80px>|
|`-m Hello -s 10 -m World`|<img src="https://github.com/puhitaku/tepra-lite-esp32/blob/master/client/example5.png?raw=true" height=80px>|
|`-q "http://example.com" -s 20 -m "http://example.com"`|<img src="https://github.com/puhitaku/tepra-lite-esp32/blob/master/client/example6.png?raw=true" height=80px>|

## Notes
<a name="note-1"></a>
1. Because the descriptor of the specific characteristic (0xFFF1) is hidden by bluetoothd/BlueZ, 
there is no way to set `notification=True` from the higher level APIs (BlueZ/Bleak). There might be 
a way to work around from the lower level (e.g. hci, btmgmt, etc.) though.  

- Update 18 Mar. 2026  
With a bit of modifications, the codes successfully worked on Linux/Bleak with 
[bumble backend](https://github.com/vChavezB/bleak-bumble)/[Google/Bumble](https://github.com/google/bumble) 
and TP-Link BT dongle \(UB400, v4.0, CSR8510 chip\) by using HCI over USB.

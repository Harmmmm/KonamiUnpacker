# KonamiUnpacker

Simple python script to unpack Konami recovery discs.
Currently only tested with Wartran Troopers application disc (D00_DATA.BIN)

## Usage
```
usage: KonamiUnpacker.py [-h] -i INPUT -o OUTPUT

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Input bin file (eg D00_DATA.BIN)
  -o OUTPUT, --output OUTPUT
                        Output folder
```

## Example
```bash
python KonamiUnpacker.py -i C:\D00_DATA.BIN -o C:\output
```
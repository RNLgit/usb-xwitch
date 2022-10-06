Release and manufacturing directory.

## Directory guide:

- bom_x: BoM file with fields of: Comment, Designator, Footprint, LCSC (pcba manufacturer specific)
- gerber_x: gerber files, drill files, drill map files
- cpl_x: component placement files for PCBA. Fields: Designator, Val, Package, Mid X, Mid Y, Rotation, Layer


## Fabrication Generation Guide:

- Follow the [guide](https://support.jlcpcb.com/article/194-how-to-generate-gerber-and-drill-files-in-kicad-6) to generate gerber and drill
- Follow the [guide](https://support.jlcpcb.com/article/84-how-to-generate-the-bom-and-centroid-file-from-kicad) to generate BoM and CPL for PCBA


## Uploading:

- zip gerber into single file and upload
- upload bom file if required PCBA
- upload cpl file if required PCBA

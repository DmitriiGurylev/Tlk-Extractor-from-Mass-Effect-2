# Tlk-Extractor-from-Mass-Effect-2

## Overview

Project was rewritten from https://github.com/jgoclawski/me2-tlk-tool.

Tlk-Extractor is a program to modify TLK files of Mass Effect 2 (All text lines including Dialogs)

You can load your TLK-file to get output XML-file. 
What is the reason of transforming TLK to XML? Because TLK-file is a non-editable binary file but XML is easy to edit the way uou want.

### Using Python:
`python3 (to_xml | to_txt) source_path dest_path`

for example:
`python3.11  ./python_ver/main.py to_xml ./files/BIOGame_RUS.tlk ./files/test1.xml`
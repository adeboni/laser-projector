import glob
import re

file_output = ""

effects = []

for filename in glob.glob("*.txt"):
    new_name = re.search('GRAPHIC (.+?).txt', filename).group(1).upper().replace(' ', '_')
    effects.append(f"EFFECT_{new_name}")
    with open(filename) as file:
        lines = [line.rstrip() for line in file]
    
    p, x, y = [], [], []
    for line in lines:
        pp, xx, yy = line.split(' ')
        p.append(pp == 'L')
        x.append(float(xx))
        y.append(float(yy))
        
    min_x = 999999
    max_x = -999999
    min_y = 999999
    max_y = -999999
    for xx, yy in zip(x, y):
        min_x = min(min_x, xx)
        max_x = max(max_x, xx)
        min_y = min(min_y, yy)
        max_y = max(max_y, yy)
    x_range = max_x - min_x
    y_range = max_y - min_y
    scale = 1100 / max(x_range, y_range)
    
    file_output += f"EFFECT_{new_name} = [\n"
    for pp, xx, yy in zip(p, x, y):
        new_x = int((xx - min_x) * scale)
        new_y = 1100 - int((yy - min_y) * scale)
        if pp:
            new_x += 0x8000
        file_output += f"    {hex(new_x)},{hex(new_y)},\n"
    file_output += "]\n\n"
    
f = open("output.py", "w")
f.write(file_output.replace(",\n]", "\n]"))
f.close()

print(", ".join(effects))
import json
import sys

autocenter = True
autoscale = True
maxScale = 30

infile = sys.argv[1]
outfile = sys.argv[2]

stl = open(infile, 'r')

# gather vertices
nodes = []
for line in stl:
    token = line.split()
    if (len(token) == 4) and (token[0] == 'vertex'):
        nodes.append([token[1], token[2], token[3]])

# keep only unique nodes
unique_nodes = []
[unique_nodes.append(item) for item in nodes if item not in unique_nodes]

stl.seek(0, 0) # seek start of file to get triangles
index = 0 # assign vertex index to triangle list
triangles = [[]]
for line in stl:
    # split line into tokens
    token = line.split()
    if (len(token) == 4) and (token[0] == 'vertex'):
        # compare current array to unique_nodes and set index in triangle
        for i, node in enumerate(unique_nodes):
            # if xyz match
            if [token[1], token[2], token[3]] == node:
                # add to current triangle list if array at index has less than 3 items
                if len(triangles[index]) < 3:
                    triangles[index].append(i)
                    break
                # else create new array
                else:
                    index += 1 # increase index
                    triangles.append([i]) # append array with new item
                    break

# reformat nodes into rounded floats                    
node_floats = []
for i in range(len(unique_nodes)):
    node_floats.append([])
    for j in range(len(unique_nodes[i])):
        node_floats[i].append(round(float(unique_nodes[i][j]), 5))
    
if autocenter:
    minX = min(node_floats, key=lambda x: x[0])[0]
    minY = min(node_floats, key=lambda x: x[1])[1]
    minZ = min(node_floats, key=lambda x: x[2])[2]
    maxX = max(node_floats, key=lambda x: x[0])[0]
    maxY = max(node_floats, key=lambda x: x[1])[1]
    maxZ = max(node_floats, key=lambda x: x[2])[2]
    for i in range(len(node_floats)):
        node_floats[i][0] -= (maxX - minX) / 2
        node_floats[i][1] -= (maxY - minY) / 2
        node_floats[i][2] -= (maxZ - minZ) / 2
    
if autoscale:
    maxVal = max([max(v) for v in node_floats])
    minVal = min([min(v) for v in node_floats])
    scaleVal = max(abs(maxVal), abs(minVal))
    for i in range(len(node_floats)):
        for j in range(len(node_floats[i])):
            node_floats[i][j] /= (scaleVal / maxScale)

x = {"NC": len(node_floats), "N": node_floats, "TC": len(triangles), "T": triangles}
json_object = json.dumps(x, separators=(',', ':'))
with open(outfile, 'w') as outfile:
    outfile.write(json_object)
    
print(json_object)
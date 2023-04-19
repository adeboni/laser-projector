#include "MeshManager.h"

extern Gpio gpio;
DynamicJsonDocument meshJson(2048);

Mesh MeshManager::loadMesh(const char *filename) {
  File file = SD.open(filename);
  DeserializationError error = deserializeJson(meshJson, file);
  if (error) gpio.displayError(3);
  
  Mesh mesh;
  
  mesh.numNodes = meshJson["NC"].as<int>();
  for (int i = 0; i < mesh.numNodes; i++)
    for (int j = 0; j < 3; j++)
      mesh.nodes[i][j] = (int)(meshJson["N"][i][j].as<float>());
     
  mesh.numTriangles = meshJson["TC"].as<int>();
  for (int i = 0; i < mesh.numTriangles; i++)
    for (int j = 0; j < 3; j++)
      mesh.triangles[i][j] = meshJson["T"][i][j].as<int>();
  
  file.close();

  return mesh;
}

void MeshManager::printMesh(Mesh mesh) {
  Serial.printf("Num Nodes: %d\r\n", mesh.numNodes);
  Serial.printf("Num Triangles: %d\r\n", mesh.numTriangles);
  Serial.println("Nodes:");
  for (int i = 0; i < mesh.numNodes; i++) {
    Serial.print("[ ");
    for (int j = 0; j < 3; j++){
      Serial.print(mesh.nodes[i][j]);
      Serial.print(" ");
    }
    Serial.println("]");
  }
  Serial.println("Triangles:");
  for (int i = 0; i < mesh.numTriangles; i++) {
    Serial.print("[ ");
    for (int j = 0; j < 3; j++) {
      Serial.print(mesh.triangles[i][j]);
      Serial.print(" ");
    }
    Serial.println("]");
  }
}


bool MeshManager::isFaceHidden(const int (*n)[2], const uint8_t index, const Mesh& m) {
  return ( ( (n[m.triangles[index][0]][0] * n[m.triangles[index][1]][1]) -
             (n[m.triangles[index][1]][0] * n[m.triangles[index][0]][1])   ) +
           ( (n[m.triangles[index][1]][0] * n[m.triangles[index][2]][1]) -
             (n[m.triangles[index][2]][0] * n[m.triangles[index][1]][1])   ) +
           ( (n[m.triangles[index][2]][0] * n[m.triangles[index][0]][1]) -
             (n[m.triangles[index][0]][0] * n[m.triangles[index][2]][1])   ) ) < 0 ? false : true;
}

void MeshManager::mergeLines(const int set1Len, const int (*set1)[4], const int set2Len, const int (*set2)[4], int (*outputSet)[4]) {
  for (int i = 0; i < set1Len; i++) 
    for (int j = 0; j < 4; j++)
      outputSet[i][j] = set1[i][j];
  for (int i = 0; i < set2Len; i++) 
    for (int j = 0; j < 4; j++)
      outputSet[i + set1Len][j] = set2[i][j];
}

void MeshManager::orderLines(const int numLines, const int (*lines)[4], int (*orderedLines)[4]) {
  int linesProcessed = 0;
  bool seen[numLines];
  memset(seen, 0, sizeof(seen));

  seen[0] = true;
  orderedLines[0][0] = lines[0][0];
  orderedLines[0][1] = lines[0][1];
  orderedLines[0][2] = lines[0][2];
  orderedLines[0][3] = lines[0][3];
  linesProcessed++;
  
  while (linesProcessed < numLines) {
    bool found = false;
    for (int i = 1; i < numLines; i++) {
      if (seen[i]) continue;
 
      if (orderedLines[linesProcessed - 1][2] == lines[i][0] && orderedLines[linesProcessed - 1][3] == lines[i][1]) {
        seen[i] = true;
        orderedLines[linesProcessed][0] = lines[i][0];
        orderedLines[linesProcessed][1] = lines[i][1];
        orderedLines[linesProcessed][2] = lines[i][2];
        orderedLines[linesProcessed][3] = lines[i][3];
        linesProcessed++;
        found = true;
      } else if (orderedLines[linesProcessed - 1][2] == lines[i][2] && orderedLines[linesProcessed - 1][3] == lines[i][3]) {
        seen[i] = true;
        orderedLines[linesProcessed][0] = lines[i][2];
        orderedLines[linesProcessed][1] = lines[i][3];
        orderedLines[linesProcessed][2] = lines[i][0];
        orderedLines[linesProcessed][3] = lines[i][1];
        linesProcessed++;
        found = true;
      }
    }

    if (!found) {
      for (int i = 1; i < numLines; i++) {
        if (!seen[i]) {
          seen[i] = true;
          orderedLines[linesProcessed][0] = lines[i][0];
          orderedLines[linesProcessed][1] = lines[i][1];
          orderedLines[linesProcessed][2] = lines[i][2];
          orderedLines[linesProcessed][3] = lines[i][3];
          linesProcessed++;
          break;
        }
      }
    }
  }
}

void MeshManager::processMesh(const int (*n)[2], const Mesh& m, 
                 int &numEdgeLines, int (*edgeLines)[4], 
                 int &numInteriorLines, int (*interiorLines)[4]) {
                  
  int seenLineCount = 0;
  int seenLines[m.numTriangles * 3][4];
  int lineCount[m.numTriangles * 3];
  memset(lineCount, 0, sizeof(lineCount));
  
  for (int t = 0; t < m.numTriangles; t++) {
    if (!isFaceHidden(n, t, m)) {
      for (int i = 0; i < 3; i++) {
        bool found = false;
        for (int j = 0; j < seenLineCount; j++) {
          if (
              (
                seenLines[j][0] == n[m.triangles[t][i]][0] && 
                seenLines[j][1] == n[m.triangles[t][i]][1] && 
                seenLines[j][2] == n[m.triangles[t][(i+1)%3]][0] && 
                seenLines[j][3] == n[m.triangles[t][(i+1)%3]][1]
              ) 
              || 
              (
                seenLines[j][0] == n[m.triangles[t][(i+1)%3]][0] && 
                seenLines[j][1] == n[m.triangles[t][(i+1)%3]][1] && 
                seenLines[j][2] == n[m.triangles[t][i]][0] && 
                seenLines[j][3] == n[m.triangles[t][i]][1]
              )
            ) {
              lineCount[j]++;
              found = true;
              break;
           }
        }
        
        if (!found) {
          seenLines[seenLineCount][0] = n[m.triangles[t][i]][0];
          seenLines[seenLineCount][1] = n[m.triangles[t][i]][1];
          seenLines[seenLineCount][2] = n[m.triangles[t][(i+1)%3]][0];
          seenLines[seenLineCount][3] = n[m.triangles[t][(i+1)%3]][1];
          lineCount[seenLineCount]++;
          seenLineCount++;
        }
      }
    }
  }

  numInteriorLines = 0;
  numEdgeLines = 0;
  for (int i = 0; i < seenLineCount; i++) {
    if (lineCount[i] == 1) {
      edgeLines[numEdgeLines][0] = seenLines[i][0];
      edgeLines[numEdgeLines][1] = seenLines[i][1];
      edgeLines[numEdgeLines][2] = seenLines[i][2];
      edgeLines[numEdgeLines][3] = seenLines[i][3];
      numEdgeLines++;
    }
    else {
      interiorLines[numInteriorLines][0] = seenLines[i][0];
      interiorLines[numInteriorLines][1] = seenLines[i][1];
      interiorLines[numInteriorLines][2] = seenLines[i][2];
      interiorLines[numInteriorLines][3] = seenLines[i][3];
      numInteriorLines++;
    }
  }
}

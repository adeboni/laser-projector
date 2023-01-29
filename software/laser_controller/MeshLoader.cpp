#include "MeshLoader.h"

extern Gpio gpio;
DynamicJsonDocument meshJson(2048);

Mesh MeshLoader::loadMesh(const char *filename) {
  File file = SD.open(filename);
  DeserializationError error = deserializeJson(meshJson, file);
  if (error) gpio.displayError(2);
  
  Mesh mesh;
  
  mesh.numNodes = meshJson["NC"].as<int>();
  for (int i = 0; i < mesh.numNodes; i++)
    for (int j = 0; j < 3; j++)
      mesh.nodes[i][j] = (long)(meshJson["N"][i][j].as<float>() * PRES);
     
  mesh.numTriangles = meshJson["TC"].as<int>();
  for (int i = 0; i < mesh.numTriangles; i++)
    for (int j = 0; j < 3; j++)
      mesh.triangles[i][j] = meshJson["T"][i][j].as<int>();
  
  file.close();

  return mesh;
}

void MeshLoader::printMesh(Mesh mesh) {
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

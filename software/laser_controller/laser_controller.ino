#include "Gpio.h"
#include "Laser.h"
#include "AudioProcessor.h"
#include "MeshLoader.h"

Laser lasers[4] = {
  Laser(0, 4, 8, 0, 1), 
  Laser(1, 5, 9, 2, 3),
  Laser(2, 6, 10, 4, 5), 
  Laser(3, 7, 11, 6, 7)
};

ADC *adc = new ADC();
Gpio gpio;
AudioProcessor audio;
MeshLoader meshLoader;
Mesh cubeMesh;

void initDAC() {
  //sets the DAC into high speed mode
  Wire.begin();
  Wire.beginTransmission(0x48);
  Wire.write(0x70);
  Wire.write(0x30);
  Wire.write(0x00);
  Wire.endTransmission();
  Wire.setClock(1000000);
}

void setup() {
  initDAC();
  Serial.begin(9600);
  if (!SD.begin(BUILTIN_SDCARD)) 
    gpio.displayError(1);
  audio.begin();

  cubeMesh = meshLoader.loadMesh("/cube.json");

  //these values will eventually be stored on and loaded from the SD card for each laser
  lasers[0].setScale(0.67, 0.67);
  lasers[0].setOffset(600, 700);
  lasers[0].setMirroring(false, true, false);
  lasers[0].setDistortionFactors(54, 0.95);
}

void movingSquare() {
  static int dir = 0;
  static long x = 0;
  static long y = 0;
  long squareSize = 400;
  long moveAmount = 10;
  lasers[0].setColorRGB(255, 0, 0);
  
  lasers[0].sendTo(x, y);
  lasers[0].on();
  lasers[0].sendTo(x + squareSize, y);
  lasers[0].sendTo(x + squareSize, y + squareSize);
  lasers[0].sendTo(x, y + squareSize);
  lasers[0].sendTo(x, y);
  lasers[0].off();
  
  if (dir == 0) {
    x = constrain(x + moveAmount, 0, 4095 - squareSize);
    if (x + squareSize == 4095) dir = 1;
  } else if (dir == 1) {
    y = constrain(y + moveAmount, 0, 4095 - squareSize);
    if (y + squareSize == 4095) dir = 2;
  } else if (dir == 2) {
    x = constrain(x - moveAmount, 0, 4095 - squareSize);
    if (x == 0) dir = 3;
  } else if (dir == 3) {
    y = constrain(y - moveAmount, 0, 4095 - squareSize);
    if (y == 0) dir = 0;
  }
}

void square() {
  lasers[0].setColorRGB(255, 0, 0);
  lasers[0].sendTo(0, 0);
  lasers[0].on();
  lasers[0].sendTo(0, 4095);
  lasers[0].sendTo(4095, 4095);
  lasers[0].sendTo(4095, 0);
  lasers[0].sendTo(0, 0);
  lasers[0].off();
}

void circle() {
  const int scale = 12;
  for (int r = 0; r <= 360; r += 5) {
    if (r < 120)      { lasers[0].setColorRGB(255, 0, 0); lasers[0].on(); }
    else if (r < 240) { lasers[0].setColorRGB(0, 255, 0); lasers[0].on(); }
    else              { lasers[0].setColorRGB(0, 0, 255); lasers[0].on(); }
    
    lasers[0].sendTo(SIN(r)/scale + 2048, COS(r)/scale + 2048);
  }
  lasers[0].off();
}

void rotatingCircle() {
  static Vector3 rotation = {0, 0, 0};
  
  Matrix4 world = Matrix4::rotateX(rotation.x);
  world = Matrix4::multiply(Matrix4::rotateY(rotation.y), world);
  world = Matrix4::multiply(Matrix4::rotateZ(rotation.z), world);
  lasers[0].setEnable3D(true);
  lasers[0].setMatrix(world);
  circle();
  lasers[0].setEnable3D(false);
  
  rotation.x += 3;
  rotation.y += 2;
  rotation.z += 1;

  if (rotation.x > 360) rotation.x = 0;
  if (rotation.y > 360) rotation.y = 0;
  if (rotation.z > 360) rotation.z = 0; 
}

void circleFFT() {
  static int rotate = 0;
  audio.updateFFT();
  audio.decay = 50;
  lasers[0].setColorRGB(255, 0, 0);
  int i = 4;
  float firstX, firstY;
  for (int r = 0; r <= 360; r+=8, i++) {    
    float d = ((float)audio.bands[i] / 25 + 5) / 320.0;
    float x = SIN((r + rotate) % 360) * d + 2048;
    float y = COS((r + rotate) % 360) * d + 2048;
    lasers[0].sendTo(x, y);
    if (r == 0) {    
      lasers[0].on();
      firstX = x;
      firstY = y;
    }
  }
  rotate++;
  lasers[0].sendTo(firstX, firstY);
  lasers[0].off();
}

void linearFFT() {
  audio.updateFFT();
  audio.decay = 30;
  lasers[0].setColorRGB(255, 0, 0);
  long step = 4096 / FFT_DISPLAY_BINS;
  long pos = 100;
  lasers[0].sendTo(pos, 2048);
  lasers[0].on();
  for (int i = 0; i < FFT_DISPLAY_BINS; i++) {
    lasers[0].sendTo(pos, audio.bands[i] + 2048);  
    pos += step;
    if (pos > 4095) break;
  }
  lasers[0].off();
}

void printCVs() {
  for (int i = 0; i < 6; i++) {
    Serial.print(gpio.getCV(i));
    Serial.print('\t');
  }
  Serial.println();
}

bool isFaceHidden(const long (*n)[2], const uint8_t index, const Mesh& m) {
  return ( ( (n[m.triangles[index][0]][0] * n[m.triangles[index][1]][1]) -
             (n[m.triangles[index][1]][0] * n[m.triangles[index][0]][1])   ) +
           ( (n[m.triangles[index][1]][0] * n[m.triangles[index][2]][1]) -
             (n[m.triangles[index][2]][0] * n[m.triangles[index][1]][1])   ) +
           ( (n[m.triangles[index][2]][0] * n[m.triangles[index][0]][1]) -
             (n[m.triangles[index][0]][0] * n[m.triangles[index][2]][1])   ) ) < 0 ? false : true;
}

void drawMeshLine(int& seenLines, long *sx1, long *sy1, long *sx2, long *sy2, 
  const long x1, const long y1, const long x2, const long y2) {
  bool found = false;
  for (int j = 0; j < seenLines; j++) {
    if ((sx1[j] == x1 && sy1[j] == y1 && sx2[j] == x2 && sy2[j] == y2) || 
        (sx1[j] == x2 && sy1[j] == y2 && sx2[j] == x1 && sy2[j] == y1)) {
          found = true;
          break;
        }
  }

  if (found) return;

  sx1[seenLines] = x1;
  sy1[seenLines] = y1;
  sx2[seenLines] = x2;
  sy2[seenLines] = y2;
  
  seenLines++;
  lasers[0].drawLine(x1, y1, x2, y2);
}

void drawMeshWireframe(const long (*n)[2], const Mesh& m) {
  uint8_t i = m.numTriangles - 1;
  int seenLines = 0;
  long sx1[i*3], sy1[i*3], sx2[i*3], sy2[i*3];
  
  do {
    if (!isFaceHidden(n, i, m)) {
      drawMeshLine(seenLines, sx1, sy1, sx2, sy2, n[m.triangles[i][0]][0], n[m.triangles[i][0]][1], n[m.triangles[i][1]][0], n[m.triangles[i][1]][1]);
      drawMeshLine(seenLines, sx1, sy1, sx2, sy2, n[m.triangles[i][1]][0], n[m.triangles[i][1]][1], n[m.triangles[i][2]][0], n[m.triangles[i][2]][1]);
      drawMeshLine(seenLines, sx1, sy1, sx2, sy2, n[m.triangles[i][2]][0], n[m.triangles[i][2]][1], n[m.triangles[i][0]][0], n[m.triangles[i][0]][1]);
    }
  } while(i--);
}

void cube() { 
  static double nextTick = millis();
  static Vector3 meshRotation = {0, 0, 0};
  long projNodes[cubeMesh.numNodes][2];
  const long zDist = 10000;
  long mScale = 30;
  
  lasers[0].setColorRGB(255, 0, 0);
  while (millis() > nextTick) {
    Matrix4 world = Matrix4::rotateX(meshRotation.x);
    world = Matrix4::multiply(Matrix4::rotateY(meshRotation.y), world);
    world = Matrix4::multiply(Matrix4::rotateZ(meshRotation.z), world);

    for (uint8_t i = 0; i < cubeMesh.numNodes; i++) {
      Vector3 in = {cubeMesh.nodes[i][0], cubeMesh.nodes[i][1], cubeMesh.nodes[i][2]};
      Vector3 p = Matrix4::applyMatrix(world, in);
      projNodes[i][0] = (zDist * p.x) / (zDist + p.z) * mScale + 2048;
      projNodes[i][1] = (zDist * p.y) / (zDist + p.z) * mScale + 2048;
    }

    meshRotation.x += 3;
    meshRotation.y += 2;
    meshRotation.z += 1;

    if (meshRotation.x > 360) meshRotation.x = 0;
    if (meshRotation.y > 360) meshRotation.y = 0;
    if (meshRotation.z > 360) meshRotation.z = 0;

    nextTick += 20.0;
  }    
  
  drawMeshWireframe(projNodes, cubeMesh);
}

void loop() {
  int mode = gpio.getMode();
  gpio.setLEDs(mode);
  
  switch (mode) {
    case 0: circle(); break;
    case 1: linearFFT(); break;
    case 2: circleFFT(); break;
    case 3: square(); break;
    case 4: movingSquare(); break;
    case 5: cube(); break;
    case 6: rotatingCircle(); break;
    case 15: printCVs(); break;
  }
}

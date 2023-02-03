#include "Gpio.h"
#include "Laser.h"
#include "Drawing.h"
#include "Objects\Objects.h"
#include "Objects\Logo.h"
#include "AudioProcessor.h"
#include "MeshLoader.h"
#include <SerialTransfer.h>

Laser lasers[4] = {
  Laser(0, 4, 8, 0, 1), 
  Laser(1, 5, 9, 2, 3),
  Laser(2, 6, 10, 4, 5), 
  Laser(3, 7, 11, 6, 7)
};

struct {
  char line1[41];
  char line2[41];
} txStruct;

struct {
  uint8_t nes;
} rxStruct;

const char* modeNames[] = {"Circle", "Circle 2", "Linear FFT", "Circle FFT", 
                           "Square", "Moving Square", "Cube", "Rotating Circle", 
                           "CV Values", "", "", "",
                           "", "", "", ""};

SerialTransfer uartTransfer;
ADC *adc = new ADC();
Gpio gpio;
AudioProcessor audio;
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
  Serial.begin(9600);
  Serial6.begin(115200);
  uartTransfer.begin(Serial6);
  
  initDAC();
  if (!SD.begin(BUILTIN_SDCARD)) 
    gpio.displayError(1);
  audio.begin();

  cubeMesh = MeshLoader::loadMesh("/cube.json");

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
    lasers[0].setColorHSL(r, 100, 50); 
    lasers[0].on();
    lasers[0].sendTo(SIN(r)/scale + 2048, COS(r)/scale + 2048);
  }
  lasers[0].off();
}

void circle2() {
  const int scale = 12;
  for (int r = 0; r <= 360; r += 5) {
    if (r < 120)      { lasers[0].setColorRGB(255, 0, 0); lasers[0].on(); lasers[0].off(); }
    else if (r < 240) { lasers[0].setColorRGB(0, 255, 0); lasers[0].on(); lasers[0].off(); }
    else              { lasers[0].setColorRGB(0, 0, 255); lasers[0].on(); lasers[0].off(); }
    
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
  circle2();
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
  audio.decay = 100;
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
  sprintf(txStruct.line2, "%d %d %d %d %d %d", gpio.getCV(0), gpio.getCV(1),
    gpio.getCV(2), gpio.getCV(3), gpio.getCV(4), gpio.getCV(5));
  uartTransfer.sendDatum(txStruct);
  Serial.println(txStruct.line2);
  
  delay(100);
}

bool isFaceHidden(const long (*n)[2], const uint8_t index, const Mesh& m) {
  return ( ( (n[m.triangles[index][0]][0] * n[m.triangles[index][1]][1]) -
             (n[m.triangles[index][1]][0] * n[m.triangles[index][0]][1])   ) +
           ( (n[m.triangles[index][1]][0] * n[m.triangles[index][2]][1]) -
             (n[m.triangles[index][2]][0] * n[m.triangles[index][1]][1])   ) +
           ( (n[m.triangles[index][2]][0] * n[m.triangles[index][0]][1]) -
             (n[m.triangles[index][0]][0] * n[m.triangles[index][2]][1])   ) ) < 0 ? false : true;
}

void mergeLines(const long set1Len, const long (*set1)[4], const long set2Len, const long (*set2)[4], long (*outputSet)[4]) {
  for (int i = 0; i < set1Len; i++) 
    for (int j = 0; j < 4; j++)
      outputSet[i][j] = set1[i][j];
  for (int i = 0; i < set2Len; i++) 
    for (int j = 0; j < 4; j++)
      outputSet[i + set1Len][j] = set2[i][j];
}

void orderLines(const long numLines, const long (*lines)[4], long (*orderedLines)[4]) {
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

void processMesh(const long (*n)[2], const Mesh& m, 
                 long &numEdgeLines, long (*edgeLines)[4], 
                 long &numInteriorLines, long (*interiorLines)[4]) {
                  
  int seenLineCount = 0;
  long seenLines[m.numTriangles * 3][4];
  long lineCount[m.numTriangles * 3];
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


void cube() { 
  static double nextTick = millis();
  static Vector3 meshRotation = {0, 0, 0};
  long projNodes[cubeMesh.numNodes][2];
  const long zDist = 10000;
  long mScale = 30;
  
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

  lasers[0].setColorRGB(0, 0, 255);
  lasers[0].on();
  
  long numEdgeLines = 0;
  long numInteriorLines = 0;
  long edgeLines[cubeMesh.numTriangles * 3][4];
  long interiorLines[cubeMesh.numTriangles * 3][4];
  processMesh(projNodes, cubeMesh, numEdgeLines, edgeLines, numInteriorLines, interiorLines);

  long numAllLines = numEdgeLines + numInteriorLines;
  long allLines[numAllLines][4];
  long orderedAllLines[numAllLines][4];
  mergeLines(numEdgeLines, edgeLines, numInteriorLines, interiorLines, allLines);
  orderLines(numAllLines, allLines, orderedAllLines);
  for (int i = 0; i < numAllLines; i++)
    lasers[0].drawLine(orderedAllLines[i][0], orderedAllLines[i][1], orderedAllLines[i][2], orderedAllLines[i][3]); 
}

///////////////////////////////////////

void countDown() {
  static char j = '0';
  static int i = 0;

  lasers[0].setColorRGB(255, 0, 0);
  Drawing::drawLetter(j, 2048, 2048);

  if (i++ == 60) {
    if (j == '9')
      j = 'A';
    else if (j == 'Z')
      j = '0';
    else 
      j++;
    i = 0;
  }
}

void staticText() {
  lasers[0].setColorRGB(255, 0, 0);
  Drawing::drawString("HELLO WORLD", 1000, 2048, 0.25);
}


void drawScroller() {
  lasers[0].setColorRGB(0, 0, 255);
  String s = "HELLO WORLD";
  int speed = 100;
  float scale = 0.5;
  
  int charW = Drawing::advance('I');
  int maxChar = (4096. / (charW * scale));
  char buffer[100];
  for (int j = 0; j < maxChar; j++)
    buffer[j] = ' ';
  
  int scrollX = 0;
  for (int c = 0; c < s.length() + maxChar; c++) {
    int currentScroll = Drawing::advance(buffer[0]);
    while (scrollX < currentScroll) {
      long time = millis();
      int x = -scrollX;;
      bool somethingDrawn = false;
      for (int i = 0;i<maxChar;i++) {
        if (buffer[i] != ' ')
          somethingDrawn = true;
        
        x += Drawing::drawLetter(buffer[i], x, 2048);

        if (x > 4096 / scale)
          break;
      }
      if (!somethingDrawn) 
        scrollX = currentScroll; 
      scrollX += speed / scale;
      long elapsed = millis() - time;
      if (elapsed < 50) 
        delay(50 - elapsed); 
    }
    scrollX -= currentScroll;
    for (int k = 0; k < maxChar - 1; k++)
      buffer[k] = buffer[k+1];
    
    if (c < s.length())
      buffer[maxChar-1] = s[c];
    else
      buffer[maxChar-1] = ' ';
  }
}

void globe() {
  lasers[0].setColorRGB(0, 0, 255);
  lasers[0].on();
  int pos = random(360)/5 * 5;
  int diff1 = random(35);
  int diff2 = random(35);
  int diff3 = random(35);
  for (int r = 0; r <= 360; r += 5) {    
    lasers[0].sendTo(2048 + SIN(r)/16, 2048 + COS(r)/16);
    if (r == pos) {    
      lasers[0].sendTo(2048 + SIN(r+diff1)/32, 2048 + COS(r+diff2)/32);
      lasers[0].sendTo(2048 + SIN(r+diff2)/64, 2048 + COS(r+diff3)/64);
      lasers[0].sendTo(2048, 2048);
      lasers[0].sendTo(2048 + SIN(r+diff3)/64, 2048 + COS(r+diff3)/64);
      lasers[0].sendTo(2048 + SIN(r+diff2)/32, 2048 + COS(r+diff1)/32);
      lasers[0].sendTo(2048 + SIN(r)/16, 2048 + COS(r)/16);
    }
  }
}

void drawPlaneRotate() {
  static Vector3 rotation = {0, 0, 0};

  rotation.x += 3;
  rotation.y += 2;
  rotation.z += 1;

  if (rotation.x > 360) rotation.x = 0;
  if (rotation.y > 360) rotation.y = 0;
  if (rotation.z > 360) rotation.z = 0; 

  lasers[0].setColorRGB(255, 0, 0);
  long centerX, centerY, w, h;
  Drawing::calcObjectBox(draw_plane, sizeof(draw_plane)/4, centerX, centerY, w, h);
  Drawing::drawObjectRotated3D(draw_plane, sizeof(draw_plane)/4, 2048 - w/2, 2048 - h/2, rotation);
}

void lfo() {
  static int dx = 0;
  static int dy = 0;
  static int dc = 0;

  lasers[0].sendTo(2048 + SIN((dx/4)%360)/16, 2048 + COS((dy/3)%360)/16);
  for (int x = 5; x <= 360; x += 5) { 
    lasers[0].setColorHSL((x + dc) % 360, 100, 50);
    lasers[0].on();
    lasers[0].sendTo(2048 + SIN(((x+dx)/4)%360)/16, 2048 + COS(((x+dy)/3)%360)/16);
  }
  lasers[0].off();
  
  dx += 1;
  dy += 2;
  dc += 2;
}

void drawBike() {
  lasers[0].setColorRGB(255, 0, 0);
  for (int i = 0; i < 2; i++)
    for (int j = 0; j < 2; j++)
      Drawing::drawObject(draw_bike, sizeof(draw_bike)/4, 2000 + i * 450, 2000 + j * 300, 0.5);
}


///////////////////////////////////////


void loop() {
  static int lastMode = -1;
  static int mode = 0;
  static int lastKnobMode = 0;

  if (uartTransfer.available()) {
    uartTransfer.rxObj(rxStruct);
    if (bitRead(rxStruct.nes, 0) == 0)
      mode = min(mode + 1, 15);
    else if (bitRead(rxStruct.nes, 1) == 0)
      mode = max(mode - 1, 0);
  }
  
  int knobMode = gpio.getMode();
  if (knobMode != lastKnobMode)
    mode = lastKnobMode = knobMode;
  gpio.setLEDs(mode);

  if (lastMode != mode) {
    lastMode = mode;
    sprintf(txStruct.line1, modeNames[mode]);
    sprintf(txStruct.line2, "");
    uartTransfer.sendDatum(txStruct);
  }
  
  switch (mode) {
    case 0: circle(); break;
    case 1: circle2(); break;
    case 2: rotatingCircle(); break;
    case 3: linearFFT(); break;
    case 4: circleFFT(); break;
    case 5: square(); break;
    case 6: movingSquare(); break;
    case 7: cube(); break;
    
    case 8: countDown(); break;
    case 9: staticText(); break;
    case 10: drawScroller(); break;
    case 11: globe(); break;
    case 12: lfo(); break;
    case 13: drawBike(); break;
    case 14: drawPlaneRotate(); break;
    
    //case 15: printCVs(); break;
  }
}

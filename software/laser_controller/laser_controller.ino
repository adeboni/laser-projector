#include <SPI.h>
#include "Gpio.h"
#include "Laser.h"
#include "Drawing.h"
#include "Objects\Objects.h"
#include "Objects\Logo.h"
#include "AudioProcessor.h"
#include "MeshManager.h"
#include "Calibration.h"
#include "FrameManager.h"

Laser lasers[4] = {
  Laser(0, 4, 8, 39), 
  Laser(1, 5, 9, 38),
  Laser(2, 6, 10, 37), 
  Laser(3, 7, 32, 36)
};
                           
ADC *adc = new ADC();
Gpio gpio;
AudioProcessor audio;
DynamicJsonDocument settingsJson(2048);

Mesh cubeMesh;

void loadSettings() {
  Serial.println("Loading settings");
  
  File file = SD.open("/settings.json");
  DeserializationError error = deserializeJson(settingsJson, file);
  if (error) gpio.displayError(2);
  file.close();

  for (int i = 0; i < 4; i++) {
    lasers[i].setScale(settingsJson["L"][i][0].as<int>() / 100.0, settingsJson["L"][i][1].as<int>() / 100.0);
    lasers[i].setOffset(settingsJson["L"][i][2].as<int>(), settingsJson["L"][i][3].as<int>());
    lasers[i].setMirroring(false, true, false);
    
    lasers[i].setClipArea(
       settingsJson["L"][i][4].as<int>(),
       settingsJson["L"][i][5].as<int>(),
       settingsJson["L"][i][6].as<int>(),
       settingsJson["L"][i][7].as<int>(),
       settingsJson["L"][i][8].as<int>(),
       settingsJson["L"][i][9].as<int>(),
       settingsJson["L"][i][10].as<int>(),
       settingsJson["L"][i][11].as<int>()
    );
    
    lasers[i].setWarpArea(
       settingsJson["L"][i][12].as<int>(),
       settingsJson["L"][i][13].as<int>(),
       settingsJson["L"][i][14].as<int>(),
       settingsJson["L"][i][15].as<int>(),
       settingsJson["L"][i][16].as<int>(),
       settingsJson["L"][i][17].as<int>(),
       settingsJson["L"][i][18].as<int>(),
       settingsJson["L"][i][19].as<int>()
    );
  }
  
  Serial.println("Loaded settings");
}

void saveSettings() {
  Serial.println("Saving settings");
  
  for (int i = 0; i < 4; i++) {
    float _xs, _ys;
    lasers[i].getScale(_xs, _ys);
    settingsJson["L"][i][0] = (int)(_xs * 100);
    settingsJson["L"][i][1] = (int)(_ys * 100);

    int _xo, _yo;
    lasers[i].getOffset(_xo, _yo);
    settingsJson["L"][i][2] = _xo;
    settingsJson["L"][i][3] = _yo;

    int _x1, _y1, _x2, _y2, _x3, _y3, _x4, _y4;
    lasers[i].getClipArea(_x1, _y1, _x2, _y2, _x3, _y3, _x4, _y4);
    settingsJson["L"][i][4] = _x1;
    settingsJson["L"][i][5] = _y1;
    settingsJson["L"][i][6] = _x2;
    settingsJson["L"][i][7] = _y2;
    settingsJson["L"][i][8] = _x3;
    settingsJson["L"][i][9] = _y3;
    settingsJson["L"][i][10] = _x4;
    settingsJson["L"][i][11] = _y4;
    
    lasers[i].getWarpArea(_x1, _y1, _x2, _y2, _x3, _y3, _x4, _y4);
    settingsJson["L"][i][12] = _x1;
    settingsJson["L"][i][13] = _y1;
    settingsJson["L"][i][14] = _x2;
    settingsJson["L"][i][15] = _y2;
    settingsJson["L"][i][16] = _x3;
    settingsJson["L"][i][17] = _y3;
    settingsJson["L"][i][18] = _x4;
    settingsJson["L"][i][19] = _y4;
  }

  SD.remove("/settings.json");
  File file = SD.open("/settings.json", FILE_WRITE);
  serializeJson(settingsJson, file);
  file.close();
  
  Serial.println("Saved settings");
}

void setup() {
  Serial.begin(9600);
  SPI.begin();
  if (!SD.begin(BUILTIN_SDCARD)) 
    gpio.displayError(1);
  audio.begin();

  loadSettings();

  unsigned long loadStartTime = millis();
  while (millis() - loadStartTime < 5000) {
    if (gpio.readUart() && gpio.isButtonPressed(NES_SELECT)) {
        beginCalibration();
        saveSettings();
    } 
  }

  cubeMesh = MeshManager::loadMesh("/cube.json");
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
  for (int i = 0; i < 4; i++) {
    lasers[i].setColorRGB(255, 0, 0);
    lasers[i].on();
    lasers[i].sendTo(0, 0);
    lasers[i].sendTo(0, 4095);
    lasers[i].sendTo(4095, 4095);
    lasers[i].sendTo(4095, 0);
  }
}

void circle() {
  const int scale = 1000;
  for (int i = 0; i < 4; i++) {
    for (int r = 0; r <= 360; r += 5) {
      lasers[i].setColorHSL(r, 100, 50); 
      lasers[i].on();
      lasers[i].sendTo(SIN(r)*scale + 2048, COS(r)*scale + 2048);
    }
    //lasers[i].off();
  }
}

void circle2() {
  const int scale = 1000;
  for (int i = 0; i < 4; i++) {
    for (int r = 0; r <= 360; r += 5) {
      if (r < 120)      { lasers[i].setColorRGB(255, 0, 0); lasers[i].on(); lasers[i].off(); }
      else if (r < 240) { lasers[i].setColorRGB(0, 255, 0); lasers[i].on(); lasers[i].off(); }
      else              { lasers[i].setColorRGB(0, 0, 255); lasers[i].on(); lasers[i].off(); }
      
      lasers[i].sendTo(SIN(r)*scale + 2048, COS(r)*scale + 2048);
    }
    lasers[i].off();
  }
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
    float d = ((float)audio.bands[i] / 25 + 5) * 50;
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

void cube() { 
  static double nextTick = millis();
  static Vector3 meshRotation = {0, 0, 0};
  static bool dataInit = false;
  int projNodes[cubeMesh.numNodes][2];
  const int zDist = 1000;
  int mScale = 10;
  
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

    nextTick += 40.0;
    dataInit = true;
  }   

  if (!dataInit) return;

  lasers[0].setColorRGB(0, 0, 255);
  lasers[0].on();

  int numEdgeLines = 0;
  int numInteriorLines = 0;
  int edgeLines[cubeMesh.numTriangles * 3][4];
  int interiorLines[cubeMesh.numTriangles * 3][4];
  MeshManager::processMesh(projNodes, cubeMesh, numEdgeLines, edgeLines, numInteriorLines, interiorLines);
  
  int numAllLines = numEdgeLines + numInteriorLines;
  int allLines[numAllLines][4];
  int orderedAllLines[numAllLines][4];
  MeshManager::mergeLines(numEdgeLines, edgeLines, numInteriorLines, interiorLines, allLines);
  MeshManager::orderLines(numAllLines, allLines, orderedAllLines);

  int _x = -1;
  int _y = -1;
  for (int i = 0; i < numAllLines; i++) {
    int x1 = orderedAllLines[i][0];
    int y1 = orderedAllLines[i][1];
    int x2 = orderedAllLines[i][2];
    int y2 = orderedAllLines[i][3];

    if (x1 != _x || y1 != _y) {
      lasers[0].off();
      lasers[0].sendTo(x1, y1);
    }

    lasers[0].on();
    lasers[0].sendTo(x2, y2);

    _x = x2;
    _y = y2;
  }
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
    lasers[0].sendTo(2048 + SIN(r)*1000, 2048 + COS(r)*1000);
    if (r == pos) {    
      lasers[0].sendTo(2048 + SIN(r+diff1)*500, 2048 + COS(r+diff2)*500);
      lasers[0].sendTo(2048 + SIN(r+diff2)*250, 2048 + COS(r+diff3)*250);
      lasers[0].sendTo(2048, 2048);
      lasers[0].sendTo(2048 + SIN(r+diff3)*250, 2048 + COS(r+diff3)*250);
      lasers[0].sendTo(2048 + SIN(r+diff2)*500, 2048 + COS(r+diff1)*500);
      lasers[0].sendTo(2048 + SIN(r)*1000, 2048 + COS(r)*1000);
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
  int centerX, centerY, w, h;
  Drawing::calcObjectBox(draw_plane, sizeof(draw_plane)/4, centerX, centerY, w, h);
  Drawing::drawObjectRotated3D(draw_plane, sizeof(draw_plane)/4, 2048 - w/2, 2048 - h/2, rotation);
}

void lfo() {
  static int dx = 0;
  static int dy = 0;
  static int dc = 0;

  for (int i = 0; i < 4; i++) {
    lasers[i].sendTo(2048 + SIN((dx/4)%360)*1000, 2048 + COS((dy/3)%360)*1000);
    for (int x = 5; x <= 360; x += 5) { 
      lasers[i].setColorHSL((x + dc) % 360, 100, 50);
      lasers[i].on();
      lasers[i].sendTo(2048 + SIN(((x+dx)/4)%360)*1000, 2048 + COS(((x+dy)/3)%360)*1000);
    }
    lasers[i].off();
  }
  
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



void frameTest() {
  MasterFrame mf;

  mf.insertMove(0, 1200, 1200, 0, 0, 255, true);
  mf.insertMove(0, 1200, 2000, 0, 0, 255, true);
  mf.insertMove(0, 2000, 2000, 0, 0, 255, true);
  mf.insertMove(0, 2000, 1200, 0, 0, 255, true);

  mf.insertMove(0, 2200, 2200, 0, 0, 255, false);
  
  mf.insertMove(0, 2200, 3000, 0, 0, 255, true);
  mf.insertMove(0, 3000, 3000, 0, 0, 255, true);
  mf.insertMove(0, 3000, 2200, 0, 0, 255, true);
  mf.insertMove(0, 2200, 2200, 0, 0, 255, true);
  
  mf.insertMove(0, 1200, 1200, 0, 0, 255, false);

  mf.insertMove(2, 1200, 1200, 0, 0, 255, true);
  mf.insertMove(2, 1200, 2000, 0, 0, 255, true);
  mf.insertMove(2, 2000, 2000, 0, 0, 255, true);
  mf.insertMove(2, 2000, 1200, 0, 0, 255, true);

  mf.insertMove(1, 2200, 3000, 0, 0, 255, true);
  mf.insertMove(1, 3000, 3000, 0, 0, 255, true);
  mf.insertMove(1, 3000, 2200, 0, 0, 255, true);
  mf.insertMove(1, 2200, 2200, 0, 0, 255, true);


  mf.drawFrame();
}


///////////////////////////////////////


void loop() {
  static int lastMode = -1;
  static int mode = 0;
  static int lastKnobMode = 0;
  
  if (gpio.readUart()) {
    if (gpio.isButtonReleased(NES_A))
      mode = min(mode + 1, 15);
    else if (gpio.isButtonReleased(NES_B))
      mode = max(mode - 1, 0);
  }
 
  int knobMode = gpio.getMode();
  if (knobMode != lastKnobMode)
    mode = lastKnobMode = knobMode;
  gpio.setLEDs(mode);

  if (lastMode != mode) {
    lastMode = mode;
    //gpio.sendUart(modeNames[mode], "");
  }
  
  switch (mode) {
    //case 0: cube(); break;
    case 0: frameTest(); break;
    //case 0: circle(); break;
    case 1: circle2(); break;
    case 2: rotatingCircle(); break;
    case 3: linearFFT(); break;
    case 4: circleFFT(); break;
    case 5: square(); break;
    case 6: movingSquare(); break;
    case 7: cube(); break;
    
    case 8: countDown(); break;
    case 9: staticText(); break;
    //case 10: drawScroller(); break;
    case 11: globe(); break;
    case 12: lfo(); break;
    case 13: drawBike(); break;
    case 14: drawPlaneRotate(); break;
    
    //case 15: printCVs(); break;
  }
}

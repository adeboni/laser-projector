#include <SPI.h>
#include "Gpio.h"
#include "Laser.h"
#include "Drawing.h"
#include "Objects\Equations.h"
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
int currMode = -1;

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

    lasers[i].setClipArea(29, 882, 4095 - 29, 882, 4095 - 1367, 4095 - 882, 1367, 4095 - 882);
    
    /*
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
    */
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

  checkMode();
}

void checkMode() {
  gpio.readUart();
  currMode = gpio.getMode();
  gpio.setLEDs(currMode);
}

//////////////////

void lasersOff() {
  for (int i = 0; i < 4; i++)
    lasers[i].off();
}

void sendToSpan(int laser, int x, int y) {
  for (int i = 0; i < 3; i++) {
    if (i != laser) lasers[laser].off();
    else lasers[laser].on();
  }
  
  if (x < 4095)
    lasers[laser].sendTo(x, y);
  else if (x < 4095 * 2)
    lasers[laser].sendTo(x - 4095, y);
  else
    lasers[laser].sendTo(x - 4095 * 2, y);
}

#define NUM_BUBBLES 6
void bubbles() {
  static int xPos[NUM_BUBBLES] = {-1};
  static int yPos[NUM_BUBBLES] = {-1};
  static int rotate[NUM_BUBBLES] = {0};
  static int cr[7] = {0,   255, 0,   255, 255, 255, 0};
  static int cb[7] = {255, 255, 255, 0,   0,   255, 0};
  static int cg[7] = {255, 0,   0,   0,   255, 255, 255};
  static int currentColor = 0;
  static int currentLaser = 0;

  lasersOff();
  

  while (currMode == 2) {
    audio.updateFFT();
    audio.decay = 100;
   
    bool doReset = true;
    for (int i = 0; i < NUM_BUBBLES; i++)
      if (yPos[i] != -1)
        doReset = false;
  
    if (doReset) {
      int x = random(1000, 3000);
      //currentLaser = (currentLaser + 1) % 3;
      currentColor = (currentColor + 1) % 7;
      lasers[currentLaser].setColorRGB(cr[currentColor], cb[currentColor], cg[currentColor]);
      lasers[currentLaser].setDelays(-1, 150);
      for (int i = 0; i < NUM_BUBBLES; i++) {
        xPos[i] = random(x - 500, x + 500);
        yPos[i] = random(1000, 1400);
        rotate[i] = random(360);
      }
    }
  
    for (int i = 0; i < NUM_BUBBLES; i++) {
      if (yPos[i] == -1)
        continue;
  
      int b = 4;
      float firstX = 2048;
      float firstY = 2048;
      for (int r = 0; r <= 360; r+=45, b++) {    
        float d = ((float)audio.bands[b] / 25 + 5) * map(yPos[i], 0, 4000, 20, 70) / 6;
        float x = SIN((r + rotate[i]) % 360) * d + xPos[i] + SIN(yPos[i]) * 50 + SIN(xPos[i] * 50);
        float y = COS((r + rotate[i]) % 360) * d + yPos[i];
        lasers[currentLaser].sendTo(x, y);
        if (r == 0) { 
          lasers[currentLaser].on();
          firstX = x;
          firstY = y;
        }
      }
  
      yPos[i] += random(5, 15);
      if (yPos[i] > 3200)
        yPos[i] = -1;
      rotate[i] += 3;
  
      lasers[currentLaser].sendTo(firstX, firstY);
      lasers[currentLaser].off();
    }  

    checkMode();
  }
}


void quads() {
  static int xPos[] = {1500, 1500, 2500, 2500};
  static int yPos[] = {1500, 2500, 2500, 1500};
  static int xDir[] = {1, 1, -1, -1};
  static int yDir[] = {1, -1, -1, 1};

  lasersOff();
  lasers[0].setColorRGB(255, 0, 255);
  lasers[0].on();
  lasers[0].setDelays(-1, 350);

  while (currMode == 3) {
    for (int i = 0; i < 3; i++) {
      for (int p = 0; p < 5; p++) {
        lasers[0].sendTo(xPos[p % 4] + i * 40, yPos[p % 4] + i * 35);
        lasers[0].on();
      }
      lasers[0].off();
    }
      
    for (int p = 0; p < 4; p++) {
      xPos[p] += xDir[p] * random(20);
      if (xPos[p] > 2500 || xPos[p] < 1000) 
        xDir[p] *= -1;
      yPos[p] += yDir[p] * random(20);
      if (yPos[p] > 2500 || yPos[p] < 1500) 
        yDir[p] *= -1;
    }

    checkMode();
  }
}

void lissajou() {
  static int i = 0;

  lasersOff();
  lasers[0].setDelays(-1, 150);
  lasers[0].setColorRGB(255, 0, 255);
  lasers[0].on();

  while (currMode == 6) {
    int x = (int)(sin((millis() / 30 + i) * PI / 360) * 500 + 2048);
    int y = (int)(cos((millis() / 40 - i * 2) * PI / 180) * 500 + 2048);
    lasers[0].sendTo(x, y);
    i += 10;

    checkMode();
  }
}

void etchasketch() {
  static int xPos[100] = {0};
  static int yPos[100] = {0};
  static bool penDown[100] = {false};
  static int numPoints = 0;
  static int currX = 2048;
  static int currY = 2048;
  static bool currPen = true;

  lasersOff();
  lasers[0].setDelays(-1, 350);

  while (currMode == 7) {
    gpio.readUart();
  
    if (gpio.isButtonReleased(NES_SELECT))
      numPoints = 0;
  
    if (gpio.isButtonReleased(NES_B))
      currPen = !currPen;
  
    if (gpio.isButtonReleased(NES_A)) {
      xPos[numPoints] = currX;
      yPos[numPoints] = currY;
      penDown[numPoints] = currPen;
      numPoints++;
    }
  
    if (gpio.isButtonPressed(NES_LEFT))  currX = constrain(currX - 8, 1500, 2500);
    if (gpio.isButtonPressed(NES_RIGHT)) currX = constrain(currX + 8, 1500, 2500);
    if (gpio.isButtonPressed(NES_UP))    currY = constrain(currY + 8, 1500, 2500);
    if (gpio.isButtonPressed(NES_DOWN))  currY = constrain(currY - 8, 1500, 2500);
  
    lasers[0].setColorRGB(0, 255, 0);
    for (int i = 0; i < numPoints; i++) {
      if (penDown[i] && i > 0) lasers[0].on();
      else lasers[0].off();
      lasers[0].sendTo(xPos[i], yPos[i]);
    }
  
    if (currPen) lasers[0].setColorRGB(0, 0, 255);
    else lasers[0].setColorRGB(255, 0, 0);
  
    lasers[0].on();
    lasers[0].sendTo(currX, currY);
    delay(50);
    lasers[0].off();

    checkMode();
  }
}

#define NUM_EQUATIONS 39
void _drawEq(int i, int x, int y) {
  switch (i) {
    case 0: Drawing::drawObject(draw_quadratic, sizeof(draw_quadratic) / 4, x, y, 1); break;
    case 1: Drawing::drawObject(draw_eqn01b, sizeof(draw_eqn01b) / 4, x, y, 1); break;
    case 2: Drawing::drawObject(draw_eqn02, sizeof(draw_eqn02) / 4, x, y, 1); break;
    case 3: Drawing::drawObject(draw_eqn02a, sizeof(draw_eqn02a) / 4, x, y, 1); break;
    case 4: Drawing::drawObject(draw_eqn02b, sizeof(draw_eqn02b) / 4, x, y, 1); break;
    case 5: Drawing::drawObject(draw_eqn03, sizeof(draw_eqn03) / 4, x, y, 1); break;
    case 6: Drawing::drawObject(draw_eqn04, sizeof(draw_eqn04) / 4, x, y, 1); break;
    case 7: Drawing::drawObject(draw_eqn05, sizeof(draw_eqn05) / 4, x, y, 1); break;
    case 8: Drawing::drawObject(draw_eqn06, sizeof(draw_eqn06) / 4, x, y, 1); break;
    case 9: Drawing::drawObject(draw_eqn07, sizeof(draw_eqn07) / 4, x, y, 1); break;
    case 10: Drawing::drawObject(draw_eqn08, sizeof(draw_eqn08) / 4, x, y, 1); break;
    case 11: Drawing::drawObject(draw_eqn09, sizeof(draw_eqn09) / 4, x, y, 1); break;
    case 12: Drawing::drawObject(draw_eqn10, sizeof(draw_eqn10) / 4, x, y, 1); break;
    case 13: Drawing::drawObject(draw_eqn11, sizeof(draw_eqn11) / 4, x, y, 1); break;
    case 14: Drawing::drawObject(draw_eqn12, sizeof(draw_eqn12) / 4, x, y, 1); break;
    case 15: Drawing::drawObject(draw_eqn13, sizeof(draw_eqn13) / 4, x, y, 1); break;
    case 16: Drawing::drawObject(draw_eqn14, sizeof(draw_eqn14) / 4, x, y, 1); break;
    case 17: Drawing::drawObject(draw_eqn14, sizeof(draw_eqn14) / 4, x, y, 1); break;
    case 18: Drawing::drawObject(draw_eqn15, sizeof(draw_eqn15) / 4, x, y, 1); break;
    case 19: Drawing::drawObject(draw_eqn16, sizeof(draw_eqn16) / 4, x, y, 1); break;
    case 20: Drawing::drawObject(draw_eqn17, sizeof(draw_eqn17) / 4, x, y, 1); break;
    case 21: Drawing::drawObject(draw_eqn18, sizeof(draw_eqn18) / 4, x, y, 1); break;
    case 22: Drawing::drawObject(draw_eqn19, sizeof(draw_eqn19) / 4, x, y, 1); break;
    case 23: Drawing::drawObject(draw_eqn20, sizeof(draw_eqn20) / 4, x, y, 1); break;
    case 24: Drawing::drawObject(draw_eqn21, sizeof(draw_eqn21) / 4, x, y, 1); break;
    case 25: Drawing::drawObject(draw_eqn22, sizeof(draw_eqn22) / 4, x, y, 1); break;
    case 26: Drawing::drawObject(draw_eqn23, sizeof(draw_eqn23) / 4, x, y, 1); break;
    case 27: Drawing::drawObject(draw_eqn24, sizeof(draw_eqn24) / 4, x, y, 1); break;
    case 28: Drawing::drawObject(draw_eqn25, sizeof(draw_eqn25) / 4, x, y, 1); break;
    case 29: Drawing::drawObject(draw_eqn26, sizeof(draw_eqn26) / 4, x, y, 1); break;
    case 30: Drawing::drawObject(draw_eqn27, sizeof(draw_eqn27) / 4, x, y, 1); break;
    case 31: Drawing::drawObject(draw_eqn28, sizeof(draw_eqn28) / 4, x, y, 1); break;
    case 32: Drawing::drawObject(draw_eqn29, sizeof(draw_eqn29) / 4, x, y, 1); break;
    case 33: Drawing::drawObject(draw_eqn30, sizeof(draw_eqn30) / 4, x, y, 1); break;
    case 34: Drawing::drawObject(draw_eqn31, sizeof(draw_eqn31) / 4, x, y, 1); break;
    case 35: Drawing::drawObject(draw_eqn32, sizeof(draw_eqn32) / 4, x, y, 1); break;
    case 36: Drawing::drawObject(draw_eqn33, sizeof(draw_eqn33) / 4, x, y, 1); break;
    case 37: Drawing::drawObject(draw_eqn35, sizeof(draw_eqn35) / 4, x, y, 1); break;
    case 38: Drawing::drawObject(draw_eqn36, sizeof(draw_eqn36) / 4, x, y, 1); break;
  }
}

void equations() {
  static int xPos = 1500;
  static int yPos = 1500;
  static int xDir = 1;
  static int yDir = 1;
  static int currEquation = 0;
  static unsigned long lastEquationUpdate = millis();

  lasersOff();
  lasers[0].setColorRGB(0, 255, 0);
  lasers[0].on();
  lasers[0].setDelays(-1, 350);

  while (currMode == 4) {
    _drawEq(currEquation, xPos, yPos);
      
    xPos += xDir * 14;
    if (xPos > 2500 || xPos < 1000)
      xDir *= -1;
    
    yPos += yDir * 8;
    if (yPos > 2500 || yPos < 1500)
      yDir *= -1;

    unsigned long newEquationTime = millis();
    if (newEquationTime - lastEquationUpdate > 10000) {
      lastEquationUpdate = newEquationTime;
      currEquation = (currEquation + 1) % NUM_EQUATIONS;
    }

    checkMode();
  }
}

void graphics() {
  //setup
  lasersOff();

  while (currMode == 5) {
    //loop

    checkMode();
  }
}

///////////////////////////////////////


void loop() { 
  checkMode();
  switch (currMode) {
    case 2: 
      bubbles();
      break;
    case 3: 
      quads(); 
      break;
    case 4:
      equations();
      break;
    case 5:
      graphics();
      break;
    case 6:
      lissajou();
      break;
    case 7:
      etchasketch();
      break;
    default:
      lasersOff();
      break;
  }
}

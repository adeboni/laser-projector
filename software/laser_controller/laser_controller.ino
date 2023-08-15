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
}

//////////////////

#define NUM_BUBBLES 6
void bubbles() {
  static int xPos[NUM_BUBBLES] = {-1};
  static int yPos[NUM_BUBBLES] = {-1};
  static int rotate[NUM_BUBBLES] = {0};
  static int color[3] = {255};

  audio.updateFFT();
  audio.decay = 100;
  for (int i = 0; i < 3; i++)
    lasers[i].setDelays(-1, 150);

  bool doReset = true;
  for (int i = 0; i < NUM_BUBBLES; i++)
    if (yPos[i] != -1)
      doReset = false;

  if (doReset) {
    int x = random(1000, 3000);
    for (int i = 0; i < NUM_BUBBLES; i++) {
      xPos[i] = random(x - 500, x + 500);
      yPos[i] = random(1000, 1400);
      rotate[i] = random(360);
      for (int c = 0; c < 3; c++)
        color[c] = random(255);
    }
  }

  for (int i = 0; i < NUM_BUBBLES; i++) {
    if (yPos[i] == -1)
      continue;

    for (int i = 0; i < 3; i++)
      lasers[i].setColorRGB(0, 0, 255);
      //lasers[i].setColorRGB((int)((millis()) % 255), (int)((millis() + 85) % 255), (int)((millis() + 170) % 255));

    int b = 4;
    float firstX = 2048;
    float firstY = 2048;
    for (int r = 0; r <= 360; r+=45, b++) {    
      float d = ((float)audio.bands[b] / 25 + 5) * map(yPos[i], 0, 4000, 20, 70) / 6;
      float x = SIN((r + rotate[i]) % 360) * d + xPos[i] + SIN(yPos[i]) * 50 + SIN(xPos[i] * 50);
      float y = COS((r + rotate[i]) % 360) * d + yPos[i];
      for (int i = 0; i < 3; i++)
        lasers[i].sendTo(x, y);
      if (r == 0) {    
        for (int i = 0; i < 3; i++)
          lasers[i].on();
        firstX = x;
        firstY = y;
      }
    }

    yPos[i] += random(5, 15);
    if (yPos[i] > 3200)
      yPos[i] = -1;
    rotate[i] += 3;

    for (int i = 0; i < 3; i++) {
      lasers[i].sendTo(firstX, firstY);
      lasers[i].off();
    }
  }  
}


void quads() {
  static int xPos[] = {1500, 1500, 2500, 2500};
  static int yPos[] = {1500, 2500, 2500, 1500};
  static int xDir[] = {1, 1, -1, -1};
  static int yDir[] = {1, -1, -1, 1};

  //audio.updateFFT();
  //audio.decay = 100;

  for (int i = 0; i < 3; i++) {
    lasers[i].setColorRGB(0, 255, 0);
    //lasers[i].setColorRGB((int)((millis()) % 255), (int)((millis() + 85) % 255), (int)((millis() + 170) % 255));
    lasers[i].on();
    lasers[i].setDelays(-1, 350);

    for (int p = 0; p < 4; p++)
      lasers[i].sendTo(xPos[p], yPos[p]);
      //lasers[i].sendTo(xPos[p] + audio.bands[1], yPos[p] + audio.bands[1]);
  }

  for (int p = 0; p < 4; p++) {
    xPos[p] += xDir[p] * random(30);
    if (xPos[p] > 2500 || xPos[p] < 1500) xDir[p] *= -1;
    yPos[p] += yDir[p] * random(30);
    if (yPos[p] > 2500 || yPos[p] < 1500) yDir[p] *= -1;
  }
}

void lissajou() {
  for (int i = 0; i < 3; i++) {
    lasers[i].setColorRGB(0, 0, 255);
    //lasers[i].setColorRGB((int)((millis() / 300) % 255), (int)((millis() / 300 + 85) % 255), (int)((millis() / 300 + 170) % 255));
    lasers[i].on();
    lasers[i].setDelays(-1, 150);
  }

  for (int i = 0; i < 720; i+=10) {
    int x = (int)(sin((millis() / 30 + i) * PI / 360) * 500 + 2048);
    int y = (int)(cos((millis() / 40 - i * 2) * PI / 180) * 500 + 2048);
    for (int i = 0; i < 3; i++)
      lasers[i].sendTo(x, y);
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

  for (int i = 0; i < 3; i++) {
    lasers[i].setColorRGB(0, 255, 0);
    lasers[i].setDelays(-1, 350);
    lasers[i].off();
  }

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


  for (int i = 0; i < numPoints; i++) {
    if (penDown[i] && i > 0) lasers[1].on();
    else lasers[1].off();
    lasers[1].sendTo(xPos[i], yPos[i]);
  }

  if (currPen) lasers[1].on();
  else lasers[1].off();
  lasers[1].sendTo(currX, currY);
  lasers[1].on();
  delay(50);
  lasers[1].off();
}

void equations() {
  
}

void graphics() {
  
}

void lasersOff() {
  for (int i = 0; i < 4; i++) {
    lasers[i].off();
  }
}

///////////////////////////////////////


void loop() { 
  gpio.readUart();
  gpio.setLEDs(gpio.getMode());
  switch (gpio.getMode()) {
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

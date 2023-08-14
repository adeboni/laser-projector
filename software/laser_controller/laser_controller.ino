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
void bubbles(int laser, int r, int g, int b) {
  static int xPos[NUM_BUBBLES] = {-1, 300, 1600, 500, 900, 700};
  static int yPos[NUM_BUBBLES] = {-1, 1500, 3000, 1200, 700, 900};
  static int rotate[NUM_BUBBLES] = {0};

  audio.updateFFT();
  audio.decay = 100;

  for (int i = 0; i < NUM_BUBBLES; i++) {
    if (yPos[i] > 4000 || yPos[i] == -1) {
      yPos[i] = 0;
      xPos[i] = random(3800) + 100;
      rotate[i] = random(360);
    }

    lasers[laser].setColorRGB(r, g, b);

    int b = 4;
    float firstX = 2048;
    float firstY = 2048;
    for (int r = 0; r <= 360; r+=90, b++) {    
      float d = ((float)audio.bands[b] / 25 + 5) * map(yPos[i], 0, 4000, 20, 70) / 4;
      float x = SIN((r + rotate[i]) % 360) * d + xPos[i] + SIN(yPos[i]) * 50 + SIN(xPos[i] * 50);
      float y = COS((r + rotate[i]) % 360) * d + yPos[i];
      lasers[laser].sendTo(x, y);
      if (r == 0) {    
        lasers[laser].on();
        firstX = x;
        firstY = y;
      }
    }

    yPos[i] += random(5, 15) * 10;
    rotate[i] += 3;

    lasers[laser].sendTo(firstX, firstY);
    lasers[laser].off();
  }  
}

void lasersOff() {
  for (int i = 0; i < 4; i++) {
    lasers[i].off();
  }
}

///////////////////////////////////////


void loop() { 
  if (gpio.readUart()) {
    /*
    if (gpio.isButtonReleased(NES_A))
      mode = min(mode + 1, 15);
    else if (gpio.isButtonReleased(NES_B))
      mode = max(mode - 1, 0);
    */
  }
 
  gpio.setLEDs(gpio.getMode());
  switch (gpio.getMode()) {
    case 2: 
      bubbles(0, 255, 0, 0); 
      bubbles(1, 255, 0, 0); 
      bubbles(2, 255, 0, 0); 
      break;
    case 3: 
      bubbles(0, 0, 255, 0); 
      bubbles(1, 0, 255, 0); 
      bubbles(2, 0, 255, 0); 
      break;
    case 4: 
      bubbles(0, 0, 0, 255); 
      bubbles(1, 0, 0, 255); 
      bubbles(2, 0, 0, 255); 
      break;
    default:
      lasersOff();
      break;
  }
}

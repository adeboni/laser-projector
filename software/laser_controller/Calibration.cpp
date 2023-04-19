#include "Calibration.h"

extern Laser lasers[4];
extern Gpio gpio;

int selectedLaser = 0;
int selectedMode = 0;

void offsetAlignment() {
  lasers[selectedLaser].setColorRGB(255, 0, 0);
  lasers[selectedLaser].on();

  while (selectedMode == MODE_OFFSET) {
    int xs = gpio.getCV(0, 50, 100);
    int ys = gpio.getCV(1, 50, 100);
    int xo = gpio.getCV(2, 100, 800);
    int yo = gpio.getCV(3, 100, 800);
   
    lasers[selectedLaser].setScale(xs / 100.0, ys / 100.0);
    lasers[selectedLaser].setOffset(xo, yo);
    
    lasers[selectedLaser].sendTo(2048, 0);
    lasers[selectedLaser].sendTo(4095, 2048);
    lasers[selectedLaser].sendTo(2048, 4095);
    lasers[selectedLaser].sendTo(0, 2048);

    checkButtons();
  }
}

void distortionAlignment() {
  lasers[selectedLaser].setColorRGB(0, 255, 0);
  lasers[selectedLaser].on();

  while (selectedMode == MODE_DISTORTION) {
    int dx = gpio.getCV(0, 30, 90);
    int dy = gpio.getCV(1, 70, 120);
   
    lasers[selectedLaser].setDistortionFactors(dx, dy / 100.0);
    
    lasers[selectedLaser].sendTo(0, 0);
    lasers[selectedLaser].sendTo(4095, 0);
    lasers[selectedLaser].sendTo(4095, 4095);
    lasers[selectedLaser].sendTo(0, 4095);

    checkButtons();
  }
}

void clippingTopAlignment() {
  lasers[selectedLaser].setColorRGB(255, 0, 255);
  lasers[selectedLaser].on();

  int _x1, _y1, _x2, _y2, _x3, _y3, _x4, _y4;
  lasers[selectedLaser].getClipArea(_x1, _y1, _x2, _y2, _x3, _y3, _x4, _y4);

  while (selectedMode == MODE_CLIPPING_TOP) {
    int x1 = gpio.getCV(0, 0, 4095);
    int y1 = gpio.getCV(1, 0, 4095);
    int x2 = gpio.getCV(0, 0, 4095);
    int y2 = gpio.getCV(1, 0, 4095);
   
    lasers[selectedLaser].setClipAreaTop(x1, y1, x2, y2);
    
    lasers[selectedLaser].sendTo(x1, y1);
    lasers[selectedLaser].sendTo(x2, y2);
    lasers[selectedLaser].sendTo(_x3, _y3);
    lasers[selectedLaser].sendTo(_x4, _y4);

    checkButtons();
  }
}

void clippingBottomAlignment() {
  lasers[selectedLaser].setColorRGB(255, 255, 0);
  lasers[selectedLaser].on();

  int _x1, _y1, _x2, _y2, _x3, _y3, _x4, _y4;
  lasers[selectedLaser].getClipArea(_x1, _y1, _x2, _y2, _x3, _y3, _x4, _y4);

  while (selectedMode == MODE_CLIPPING_BOTTOM) {
    int x3 = gpio.getCV(0, 0, 4095);
    int y3 = gpio.getCV(1, 0, 4095);
    int x4 = gpio.getCV(0, 0, 4095);
    int y4 = gpio.getCV(1, 0, 4095);
   
    lasers[selectedLaser].setClipAreaBottom(x3, y3, x4, y4);
    
    lasers[selectedLaser].sendTo(_x1, _y1);
    lasers[selectedLaser].sendTo(_x2, _y2);
    lasers[selectedLaser].sendTo(x3, y3);
    lasers[selectedLaser].sendTo(x4, y4);

    checkButtons();
  }
}

void checkButtons() {
  if (gpio.readUart()) {      
    if (gpio.isButtonPressed(NES_START)) {
      //save settings to sd card
      return;
    }
    
    if (gpio.isButtonReleased(NES_RIGHT))
      selectedLaser = min(3, selectedLaser + 1);
    if (gpio.isButtonReleased(NES_LEFT))
      selectedLaser = max(0, selectedLaser - 1);
    if (gpio.isButtonReleased(NES_UP))
      selectedMode = min(3, selectedMode + 1);
    if (gpio.isButtonReleased(NES_DOWN))
      selectedMode = max(0, selectedMode - 1);
  }
}

void beginCalibration() {
  while (true) {
    for (int i = 0; i < 4; i++)
      lasers[i].off();

    checkButtons();  
     
    switch (selectedMode) {
      case MODE_OFFSET: offsetAlignment(); break;
      case MODE_DISTORTION: distortionAlignment(); break;
      case MODE_CLIPPING_TOP: clippingTopAlignment(); break;
      case MODE_CLIPPING_BOTTOM: clippingBottomAlignment(); break;
    }
  }
}

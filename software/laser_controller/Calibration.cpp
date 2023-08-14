#include "Calibration.h"

extern Laser lasers[4];
extern Gpio gpio;

int selectedLaser = 0;
int selectedMode = 0;

void offsetAlignment() {
  lasers[selectedLaser].setColorRGB(0, 255, 0);
  lasers[selectedLaser].on();

  float _xs, _ys;
  lasers[selectedLaser].getScale(_xs, _ys);
  gpio.setCVTarget(0, (int)(_xs * 100), 10);
  gpio.setCVTarget(1, (int)(_ys * 100), 10);

  int _xo, _yo;
  lasers[selectedLaser].getOffset(_xo, _yo);
  gpio.setCVTarget(2, _xo, 200);
  gpio.setCVTarget(3, _yo, 200);

  int _x1, _y1, _x2, _y2, _x3, _y3, _x4, _y4;
  lasers[selectedLaser].getClipArea(_x1, _y1, _x2, _y2, _x3, _y3, _x4, _y4);

  while (selectedMode == MODE_OFFSET) {
    int xs = gpio.getCV(0, 5, 150);
    int ys = gpio.getCV(1, 5, 150);
    int xo = gpio.getCV(2, -2000, 2000);
    int yo = gpio.getCV(3, -2000, 2000);
   
    lasers[selectedLaser].setScale(xs / 100.0, ys / 100.0);
    lasers[selectedLaser].setOffset(xo, yo);
    
    /*
    lasers[selectedLaser].sendTo(2048, 0);
    lasers[selectedLaser].sendTo(4095, 2048);
    lasers[selectedLaser].sendTo(2048, 4095);
    lasers[selectedLaser].sendTo(0, 2048);
    */

    lasers[selectedLaser].sendTo(_x1 + 10, _y1 + 10);
    lasers[selectedLaser].sendTo(_x2 - 10, _y2 + 10);
    lasers[selectedLaser].sendTo(_x3 - 10, _y3 - 10);
    lasers[selectedLaser].sendTo(_x4 + 10, _y4 - 10);

    checkButtons();
  }
}

void clippingTopAlignment() {
  lasers[selectedLaser].setColorRGB(255, 0, 255);
  lasers[selectedLaser].on();

  int _x1, _y1, _x2, _y2, _x3, _y3, _x4, _y4;
  lasers[selectedLaser].getClipArea(_x1, _y1, _x2, _y2, _x3, _y3, _x4, _y4);
  gpio.setCVTarget(0, _x1, 200);
  gpio.setCVTarget(1, _y1, 200);
  gpio.setCVTarget(2, _x2, 200);
  gpio.setCVTarget(3, _y2, 200);

  gpio.clearCVTarget(4);
  gpio.clearCVTarget(5);

  while (selectedMode == MODE_CLIPPING_TOP) {
    int x1 = gpio.getCV(0, 0, 4095);
    int y1 = gpio.getCV(1, 0, 4095);
    int x2 = gpio.getCV(2, 0, 4095);
    int y2 = gpio.getCV(3, 0, 4095);
   
    lasers[selectedLaser].setClipAreaTop(x1, y1, x2, y2);

    lasers[selectedLaser].sendTo(x1 + 10, y1 + 10);
    lasers[selectedLaser].sendTo(x2 - 10, y2 + 10);
    lasers[selectedLaser].sendTo(_x3 - 10, _y3 - 10);
    lasers[selectedLaser].sendTo(_x4 + 10, _y4 - 10);

    checkButtons();
  }
}

void clippingBottomAlignment() {
  lasers[selectedLaser].setColorRGB(255, 255, 0);
  lasers[selectedLaser].on();

  int _x1, _y1, _x2, _y2, _x3, _y3, _x4, _y4;
  lasers[selectedLaser].getClipArea(_x1, _y1, _x2, _y2, _x3, _y3, _x4, _y4);
  gpio.setCVTarget(0, _x3, 200);
  gpio.setCVTarget(1, _y3, 200);
  gpio.setCVTarget(2, _x4, 200);
  gpio.setCVTarget(3, _y4, 200);

  while (selectedMode == MODE_CLIPPING_BOTTOM) {
    int x3 = gpio.getCV(0, 0, 4095);
    int y3 = gpio.getCV(1, 0, 4095);
    int x4 = gpio.getCV(2, 0, 4095);
    int y4 = gpio.getCV(3, 0, 4095);
   
    lasers[selectedLaser].setClipAreaBottom(x3, y3, x4, y4);

    lasers[selectedLaser].sendTo(_x1 + 10, _y1 + 10);
    lasers[selectedLaser].sendTo(_x2 - 10, _y2 + 10);
    lasers[selectedLaser].sendTo(x3 - 10, y3 - 10);
    lasers[selectedLaser].sendTo(x4 + 10, y4 - 10);

    checkButtons();
  }
}

void warpTopAlignment() {
  lasers[selectedLaser].setColorRGB(255, 0, 255);
  lasers[selectedLaser].on();

  int _x1, _y1, _x2, _y2, _x3, _y3, _x4, _y4;
  lasers[selectedLaser].getWarpArea(_x1, _y1, _x2, _y2, _x3, _y3, _x4, _y4);
  gpio.setCVTarget(0, _x1, 200);
  gpio.setCVTarget(1, _y1, 200);
  gpio.setCVTarget(2, _x2, 200);
  gpio.setCVTarget(3, _y2, 200);

  while (selectedMode == MODE_WARP_TOP) {
    int x1 = gpio.getCV(0, 0, 4095);
    int y1 = gpio.getCV(1, 0, 4095);
    int x2 = gpio.getCV(2, 0, 4095);
    int y2 = gpio.getCV(3, 0, 4095);
   
    lasers[selectedLaser].setWarpAreaTop(x1, y1, x2, y2);
    
    lasers[selectedLaser].sendTo(x1, y1);
    lasers[selectedLaser].sendTo(x2, y2);
    lasers[selectedLaser].sendTo(_x3, _y3);
    lasers[selectedLaser].sendTo(_x4, _y4);

    checkButtons();
  }
}

void warpBottomAlignment() {
  lasers[selectedLaser].setColorRGB(255, 255, 0);
  lasers[selectedLaser].on();

  int _x1, _y1, _x2, _y2, _x3, _y3, _x4, _y4;
  lasers[selectedLaser].getWarpArea(_x1, _y1, _x2, _y2, _x3, _y3, _x4, _y4);
  gpio.setCVTarget(0, _x3, 200);
  gpio.setCVTarget(1, _y3, 200);
  gpio.setCVTarget(2, _x4, 200);
  gpio.setCVTarget(3, _y4, 200);

  while (selectedMode == MODE_WARP_BOTTOM) {
    int x3 = gpio.getCV(0, 0, 4095);
    int y3 = gpio.getCV(1, 0, 4095);
    int x4 = gpio.getCV(2, 0, 4095);
    int y4 = gpio.getCV(3, 0, 4095);
   
    lasers[selectedLaser].setWarpAreaBottom(x3, y3, x4, y4);

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
      selectedMode = MODE_END_CAL;
      return;
    }
    
    if (gpio.isButtonReleased(NES_RIGHT))
      selectedLaser = min(3, selectedLaser + 1);
    if (gpio.isButtonReleased(NES_LEFT))
      selectedLaser = max(0, selectedLaser - 1);
    /*
    if (gpio.isButtonReleased(NES_UP))
      selectedMode = min(4, selectedMode + 1);
    if (gpio.isButtonReleased(NES_DOWN))
      selectedMode = max(0, selectedMode - 1);
    */
  }
}

void beginCalibration() {
  Serial.println("Starting calibration");
  while (true) {
    for (int i = 0; i < 4; i++)
      lasers[i].off();

    checkButtons();  
     
    switch (selectedMode) {
      case MODE_OFFSET: offsetAlignment(); break;
      //case MODE_CLIPPING_TOP: clippingTopAlignment(); break;
      //case MODE_CLIPPING_BOTTOM: clippingBottomAlignment(); break;
      //case MODE_WARP_TOP: warpTopAlignment(); break;
      //case MODE_WARP_BOTTOM: warpBottomAlignment(); break;
      case MODE_END_CAL: return;
    }
  }
}

#ifndef GPIO_H
#define GPIO_H

#include "Arduino.h"
#include <ADC.h>
#include <SD.h>
#include <SPI.h>
#include <SerialTransfer.h>

#define NES_A      0
#define NES_B      1
#define NES_SELECT 2
#define NES_START  3
#define NES_UP     4
#define NES_DOWN   5
#define NES_LEFT   6
#define NES_RIGHT  7

class Gpio {
public:
  Gpio();
  void setLEDs(uint8_t value);
  void displayError(uint8_t value);
  bool readUart();
  uint8_t getMode();
  int getCV(uint8_t index);
  int getCV(uint8_t index, int min, int max);
  void setCVTarget(uint8_t index, int value, int delta);
  void clearCVTarget(uint8_t index);
  bool isButtonPressed(uint8_t button);
  bool isButtonReleased(uint8_t button);
  void printButtons();
  
private:
  const int _modePin = 15;
  const int _ledPins[4] = {28, 29, 30, 31};
  const int _cvPins[6] = {23, 22, 21, 20, 26, 27};
  const int _rxPin = 25;
  const int _txPin = 24;
  int _cvTargets[6] = {-1, -1, -1, -1, -1, -1};
  int _cvTargetDeltas[6] = {0, 0, 0, 0, 0, 0};
};

#endif

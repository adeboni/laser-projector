#ifndef GPIO_H
#define GPIO_H

#include "Arduino.h"
#include <ADC.h>
#include <SD.h>
#include <SPI.h>

class Gpio {
public:
  Gpio();
  void setLEDs(uint8_t value);
  void displayError(uint8_t value);
  uint8_t getMode();
  int getCV(uint8_t index);
  int getCV(uint8_t index, int min, int max);
  
private:
  const int _modePin = 15;
  const int _ledPins[4] = {28, 29, 30, 31};
  const int _cvPins[6] = {23, 22, 21, 26, 20, 27};
  const int _rxPin = 25;
  const int _txPin = 24;
};

#endif

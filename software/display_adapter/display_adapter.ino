#include "Defines.h"
#include <LiquidCrystal.h>
#include <SerialTransfer.h>

struct {
  uint8_t nes;
  uint8_t mode;
} laserData;

LiquidCrystal lcd(12, 11, 5, 4, 3, 2);
SerialTransfer uartTransfer;

int refVoltageMode = 0;
int refVoltageButtons = 0;
int lastButton = 0;
unsigned long lastUpdate = 0;
unsigned long timeToPowerOff = POWER_TIMEOUT_MS;

uint8_t readNesController() {  
  uint8_t tempData = 255;

  digitalWrite(NES_LTC_PIN, HIGH);
  delayMicroseconds(12);
  digitalWrite(NES_LTC_PIN, LOW);

  for (int i = 0; i < 8; i++) {
    if (digitalRead(NES_DAT_PIN) == 0)
      bitClear(tempData, i);
    digitalWrite(NES_CLK_PIN, HIGH);
    delayMicroseconds(6);
    digitalWrite(NES_CLK_PIN, LOW);
    delayMicroseconds(6);
  }

  return tempData;
}

int getButton() {
  float val = (100.0 * analogRead(BTN_PIN)) / refVoltageButtons;
  if (abs(val - LTL_BTN) < 0.5) return 1;
  if (abs(val - LTR_BTN) < 0.5) return 2;
  if (abs(val - NBL_BTN) < 0.5) return 3;
  if (abs(val - NBR_BTN) < 0.5) return 4;
  if (abs(val - ENT_BTN) < 0.5) return 5;
  if (abs(val - SKP_BTN) < 0.5) return 6;
  if (abs(val - PWR_BTN) < 0.5) return 7;
  return 0;
}

int getMode() { 
  float val = (100.0 * analogRead(MODE_PIN)) / refVoltageMode;
  if (abs(val - MODE_0) < 1) return 0;
  if (abs(val - MODE_1) < 1) return 1;
  if (abs(val - MODE_2) < 1) return 2;
  if (abs(val - MODE_3) < 1) return 3;
  if (abs(val - MODE_4) < 1) return 4;
  if (abs(val - MODE_5) < 1) return 5;
  if (abs(val - MODE_6) < 1) return 6;
  if (abs(val - MODE_7) < 1) return 7;
  return 255;
}

void updateDisplay() {
  lcd.clear();
  if (timeToPowerOff == 0)
    return;
    
  lcd.setCursor(0, 0);
  lcd.print("Mode: [");
  lcd.print(laserData.mode);
  lcd.print("] - ");
  switch (laserData.mode) {
    case 0:
      lcd.print("Jukebox");
      break;
    case 1:
      lcd.print("Robbie");
      break;
    case 2:
      lcd.print("Laser Bubbles");
      break;
    case 3:
      lcd.print("Laser Quads");
      break;
    case 4:
      lcd.print("Laser Equations");
      break;
    case 5:
      lcd.print("Laser Graphics");
      break;
    case 6:
      lcd.print("Laser Etch-a-Sketch");
      break;
    case 7:
      lcd.print("N/A");
      break;
  }

  lcd.setCursor(0, 1);
  lcd.print("Time to power off: ");
  char buf[10];
  unsigned long seconds = timeToPowerOff / 1000;
  sprintf(buf, "%d:%02d", (int)(seconds / 60), (int)(seconds % 60));  
  lcd.print(buf);

  lastUpdate = millis();;
}

void setup() {
  laserData.mode = 0;
  laserData.nes = 255;
  
  pinMode(NES_DAT_PIN, INPUT);
  pinMode(NES_CLK_PIN, OUTPUT);
  pinMode(NES_LTC_PIN, OUTPUT);
  digitalWrite(NES_CLK_PIN, LOW);
  digitalWrite(NES_LTC_PIN, LOW);

  lcd.begin(40, 2);
  lcd.clear();
  lcd.print("Calibrating...");
  delay(1000);

  int sumButtons = 0;
  int sumMode = 0;
  for (int i = 0; i < 5; i++) {
    sumButtons += analogRead(BTN_PIN);
    sumMode += analogRead(MODE_PIN);
    delay(200);
  }
  refVoltageButtons = sumButtons / 5;
  refVoltageMode = sumMode / 5;

  lcd.clear();

  Serial.begin(9600);
  uartTransfer.begin(Serial);
  updateDisplay();
}


void loop() {
  static unsigned long lastButtonPress = 0;
  static unsigned long lastPowerOffTimeCheck = millis();

  int mode = getMode();
  if (timeToPowerOff > 0 && mode != 255 && mode != laserData.mode) {
    laserData.mode = mode;
    timeToPowerOff = POWER_TIMEOUT_MS;
    updateDisplay();
    uartTransfer.sendDatum(laserData);
  }

  uint8_t newNES = readNesController();
  if (newNES != laserData.nes) {
    laserData.nes = newNES;
    uartTransfer.sendDatum(laserData);
  }
  
  unsigned long newButtonPress = millis();
  int button = getButton();
  if (button != lastButton && button != 0 && newButtonPress - lastButtonPress > 300) {
    if (button > 0 && button < 7)
      timeToPowerOff = POWER_TIMEOUT_MS;
    else if (button == 7) {
      if (timeToPowerOff > POWER_GRACE_MS)
        timeToPowerOff = POWER_GRACE_MS;
      else
        timeToPowerOff = POWER_TIMEOUT_MS;
    }
    lastButtonPress = newButtonPress;
  }
  lastButton = button;

  unsigned long newPowerOffTimeCheck = millis();
  timeToPowerOff -= min(newPowerOffTimeCheck - lastPowerOffTimeCheck, timeToPowerOff);
  lastPowerOffTimeCheck = newPowerOffTimeCheck;
  if (timeToPowerOff == 0 && laserData.mode != 255) {
    laserData.mode = 255;
    uartTransfer.sendDatum(laserData);
  }

  if (millis() - lastUpdate > 1000)
    updateDisplay();
}

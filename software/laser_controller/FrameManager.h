#ifndef FRAMEMANAGER_H
#define FRAMEMANAGER_H

#include "Arduino.h"
#include "LinkedList.h"
#include "Basics.h"
#include "Laser.h"

#define BASE_QUALITY 32

extern Laser lasers[4];

struct FrameSegment {
  int x;
  int y;
  int r;
  int g;
  int b;
  bool on;
};

class MasterFrame {
public:
	MasterFrame();
	void insertMove(uint8_t laser, int x, int y, int r, int g, int b, bool on);
	void drawFrame();
	
private:
	LinkedList<FrameSegment> segmentRaw[4];
	LinkedList<FrameSegment> segment[4];
	bool laserEnabled[4] = {false, false, false, false};
	float quality[4] = {BASE_QUALITY, BASE_QUALITY, BASE_QUALITY, BASE_QUALITY};
	int repeats[4] = {1, 1, 1, 1};
	
	void calculateFrames();
};

#endif

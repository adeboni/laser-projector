#include "FrameManager.h"

MasterFrame::MasterFrame() {
	for (int i = 0; i < 4; i++) {
		segmentRaw[i] = LinkedList<FrameSegment>();
		segment[i] = LinkedList<FrameSegment>();
	}
}

void MasterFrame::insertMove(uint8_t laser, int x, int y, int r, int g, int b, bool on) {
	laserEnabled[laser] = true;
	
	float _scaleX, _scaleY;
	int _offsetX, _offsetY, _oldX, _oldY;
	lasers[laser].getScale(_scaleX, _scaleY);
	lasers[laser].getOffset(_offsetX, _offsetY);
	lasers[laser].getPreviousPosition(_oldX, _oldY);
	
	_scaleX = 1;
	_scaleY = 1;
	_offsetX = 0;
	_offsetY = 0;
	
	int xNew = (int)(x * _scaleX) + _offsetX;
	int yNew = (int)(y * _scaleY) + _offsetY; 
	int clipX = xNew;
	int clipY = yNew;
	int oldX = _oldX;
	int oldY = _oldY;
	
	if (lasers[laser].clipLine(oldX, oldY, clipX, clipY)) {
		if (oldX != _oldX || oldY != _oldY) {
			FrameSegment fs = {oldX, oldY, r, g, b, on};
			segmentRaw[laser].add(fs);
		}
		FrameSegment fs = {clipX, clipY, r, g, b, on};
		segmentRaw[laser].add(fs);
	}
	
	lasers[laser].setPreviousPosition(xNew, yNew);
}

void MasterFrame::calculateFrames() {
	long totalLength[4] = {0, 0, 0, 0};
	int maxIndex = 0;
	
	// find the laser that does the most drawing
	for (int l = 0; l < 4; l++) {
		if (!laserEnabled[l]) continue;
		int _x = 0;
		int _y = 0;
		
		for (int i = 0; i < segmentRaw[l].size(); i++) {
			totalLength[l] += max(abs(segmentRaw[l].get(i).x - _x), abs(segmentRaw[l].get(i).y - _y));
			_x = segmentRaw[l].get(i).x;
			_y = segmentRaw[l].get(i).y;
		}
		
		if (totalLength[l] > totalLength[maxIndex])
			maxIndex = l;
	}
	
	// adjust quality for each laser to match drawing times
	for (int l = 0; l < 4; l++) {
		if (!laserEnabled[l]) continue;
		if (l == maxIndex) continue;
		
		while ((repeats[l] + 1) * totalLength[l] <= totalLength[maxIndex])
			repeats[l]++;
		
		quality[l] = (quality[maxIndex] * totalLength[l] * repeats[l]) / totalLength[maxIndex];
	}
	
	for (int l = 0; l < 4; l++) {
		if (!laserEnabled[l]) continue;
		int _x, _y;
		lasers[l].getPreviousPositionClipped(_x, _y);
		
		for (int i = 0; i < segmentRaw[l].size(); i++) {
		  // divide into equal parts, using _quality
		  float fdiffx = segmentRaw[l].get(i).x - _x;
		  float fdiffy = segmentRaw[l].get(i).y - _y;
		  float diffx = abs(fdiffx) / quality[l];
		  float diffy = abs(fdiffy) / quality[l];

		  // use the bigger direction 
		  float maxDiff = max(diffx, diffy);
		  fdiffx = fdiffx / maxDiff;
		  fdiffy = fdiffy / maxDiff;
		  
		  // interpolate in FIXPT
		  float tmpx = 0;
		  float tmpy = 0;
		  for (int j = 0; j < maxDiff - 1; j++) {
			tmpx += fdiffx;
			tmpy += fdiffy;
			
			FrameSegment fs = {_x + (int)tmpx, _y + (int)tmpy,
							   segmentRaw[l].get(i).r, 
							   segmentRaw[l].get(i).g, 
							   segmentRaw[l].get(i).b, 
							   segmentRaw[l].get(i).on};
							   
			segment[l].add(fs);
		  }
		  
		  lasers[l].setPreviousPositionClipped(segmentRaw[l].get(i).x, segmentRaw[l].get(i).y);
		  
		  FrameSegment fs = {segmentRaw[l].get(i).x,
							 segmentRaw[l].get(i).y,
							 segmentRaw[l].get(i).r, 
							 segmentRaw[l].get(i).g, 
							 segmentRaw[l].get(i).b, 
							 segmentRaw[l].get(i).on};
							   
		  segment[l].add(fs);
		}
	}
	
	/*
	int numActiveLasers = 0;
	for (int l = 0; l < 4; l++)
		if (laserEnabled[l]) numActiveLasers++;
	for (int l = 0; l < 4; l++)
		if (laserEnabled[l]) lasers[l].setDelays(-1, DEFAULT_DAC_DELAY / numActiveLasers);
	*/
}

void MasterFrame::drawFrame() {
	calculateFrames();
	
	int maxPoints = 0;
	for (int l = 0; l < 4; l++)
		maxPoints = max(maxPoints, segment[l].size());
	
	for (int i = 0; i < maxPoints; i++) {
		for (int l = 0; l < 4; l++) {
			if (!laserEnabled[l]) continue;
			if (i >= segment[l].size()) continue;
			
			lasers[l].setColorRGB(segment[l].get(i).r, segment[l].get(i).g, segment[l].get(i).b);
			if (segment[l][i].on) lasers[l].on();
			else lasers[l].off();
			
			Serial.printf("%d %d %d\r\n", l, segment[l].get(i).x, segment[l].get(i).y);
			//lasers[l].writeDAC(segment[l].get(i).x, segment[l].get(i).y);
		}
	}
}
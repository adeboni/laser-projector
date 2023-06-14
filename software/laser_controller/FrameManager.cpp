#include "FrameManager.h"

#define BASE_QUALITY 32

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
	int totalLength[4] = {0, 0, 0, 0};
	float quality[4] = {BASE_QUALITY, BASE_QUALITY, BASE_QUALITY, BASE_QUALITY};
	int repeats[4] = {1, 1, 1, 1};
	int maxIndex = 0;
	
	// find the laser that does the most drawing
	for (int l = 0; l < 4; l++) {
		if (!laserEnabled[l]) continue;
		int _x = 0;
		int _y = 0;
		
		for (int i = 0; i < segmentRaw[l].size(); i++) {
			int diffx = ABS(segmentRaw[l].get(i).x - _x);
			int diffy = ABS(segmentRaw[l].get(i).y - _y);
			totalLength[l] += max(diffx, diffy);
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
		
		for (int r = 0; r < repeats[l]; r++) {
			for (int i = 0; i < segmentRaw[l].size(); i++) {
			  int _x, _y;
			  lasers[l].getPreviousPositionClipped(_x, _y);
				
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
			
			lasers[l].writeDAC(segment[l].get(i).x, segment[l].get(i).y);
		}
	}
}
#include "Drawing.h"
#include "Objects\Font.h"

void Drawing::drawString(String text, int x, int y, float scale) {
  int i = 0;
  int x1 = x;
  while (text.charAt(i) != '\0') {
     x1 += drawLetter(text.charAt(i), x1, y, scale); 
     i++;
  }
}

long Drawing::stringAdvance(String text, float scale) {
  long adv = 0;
  int i = 0;
  while (text.charAt(i) != '\0') {
     adv += advance(text.charAt(i), scale); 
     i++;
  }
  return adv;
}

long Drawing::advance(byte letter, float scale) {
  long adv = 850;
  if (letter == 'I') {
    adv = 200;
  } else
  if (letter == 'W') {
    adv = 1000;
  }
  return TO_INT(adv * FROM_FLOAT(scale));
}

long Drawing::drawLetter(byte letter, long translateX, long translateY, float scale) {
  long adv = advance(letter, scale);
  
  switch (letter) {
    case 'A': drawObject(draw_A, sizeof(draw_A)/4, translateX, translateY, scale); break;
    case 'B': drawObject(draw_B, sizeof(draw_B)/4, translateX, translateY, scale); break;
    case 'C': drawObject(draw_C, sizeof(draw_C)/4, translateX, translateY, scale); break;
    case 'D': drawObject(draw_D, sizeof(draw_D)/4, translateX, translateY, scale); break;
    case 'E': drawObject(draw_E, sizeof(draw_E)/4, translateX, translateY, scale); break;
    case 'F': drawObject(draw_F, sizeof(draw_F)/4, translateX, translateY, scale); break;
    case 'G': drawObject(draw_G, sizeof(draw_G)/4, translateX, translateY, scale); break;
    case 'H': drawObject(draw_H, sizeof(draw_H)/4, translateX, translateY, scale); break;
    case 'I': drawObject(draw_I, sizeof(draw_I)/4, translateX, translateY, scale); break;
    case 'J': drawObject(draw_J, sizeof(draw_J)/4, translateX, translateY, scale); break;
    case 'K': drawObject(draw_K, sizeof(draw_K)/4, translateX, translateY, scale); break;
    case 'L': drawObject(draw_L, sizeof(draw_L)/4, translateX, translateY, scale); break;
    case 'M': drawObject(draw_M, sizeof(draw_M)/4, translateX, translateY, scale); break;
    case 'N': drawObject(draw_N, sizeof(draw_N)/4, translateX, translateY, scale); break;
    case 'O': drawObject(draw_O, sizeof(draw_O)/4, translateX, translateY, scale); break;
    case 'P': drawObject(draw_P, sizeof(draw_P)/4, translateX, translateY, scale); break;
    case 'Q': drawObject(draw_Q, sizeof(draw_Q)/4, translateX, translateY, scale); break;
    case 'R': drawObject(draw_R, sizeof(draw_R)/4, translateX, translateY, scale); break;
    case 'S': drawObject(draw_S, sizeof(draw_S)/4, translateX, translateY, scale); break;
    case 'T': drawObject(draw_T, sizeof(draw_T)/4, translateX, translateY, scale); break;
    case 'U': drawObject(draw_U, sizeof(draw_U)/4, translateX, translateY, scale); break;
    case 'V': drawObject(draw_V, sizeof(draw_V)/4, translateX, translateY, scale); break;
    case 'W': drawObject(draw_W, sizeof(draw_W)/4, translateX, translateY, scale); break;
    case 'X': drawObject(draw_X, sizeof(draw_X)/4, translateX, translateY, scale); break;
    case 'Y': drawObject(draw_Y, sizeof(draw_Y)/4, translateX, translateY, scale); break;
    case 'Z': drawObject(draw_Z, sizeof(draw_Z)/4, translateX, translateY, scale); break;
    
    case '0': drawObject(draw_0, sizeof(draw_0)/4, translateX, translateY, scale); break;
    case '1': drawObject(draw_1, sizeof(draw_1)/4, translateX, translateY, scale); break;
    case '2': drawObject(draw_2, sizeof(draw_2)/4, translateX, translateY, scale); break;
    case '3': drawObject(draw_3, sizeof(draw_3)/4, translateX, translateY, scale); break;
    case '4': drawObject(draw_4, sizeof(draw_4)/4, translateX, translateY, scale); break;
    case '5': drawObject(draw_5, sizeof(draw_5)/4, translateX, translateY, scale); break;
    case '6': drawObject(draw_6, sizeof(draw_6)/4, translateX, translateY, scale); break;
    case '7': drawObject(draw_7, sizeof(draw_7)/4, translateX, translateY, scale); break;
    case '8': drawObject(draw_8, sizeof(draw_8)/4, translateX, translateY, scale); break;
    case '9': drawObject(draw_9, sizeof(draw_9)/4, translateX, translateY, scale); break;
    case '!': drawObject(draw_exclam, sizeof(draw_exclam)/4, translateX, translateY, scale); break;
    case '?': drawObject(draw_question, sizeof(draw_question)/4, translateX, translateY, scale); break;
    case '.': drawObject(draw_dot, sizeof(draw_dot)/4, translateX, translateY, scale); break;
    case ' ':    
        break;

  }
  return adv;
}

void Drawing::drawObject(const unsigned short* data, int size, long translateX, long translateY, float scale) {
  const unsigned short* d = data;
  unsigned short posX;
  unsigned short posY;
  while (size>0) {
    posX = pgm_read_word(d);
    d++;
    posY = pgm_read_word(d);
    d++;
    size--;

    if (posX & 0x8000) {
      lasers[0].on();
    } else {
      lasers[0].off();
    }
    lasers[0].sendTo(TO_INT((posX & 0x7fff) * FROM_FLOAT(scale)) + translateX, TO_INT(posY * FROM_FLOAT(scale)) + translateY);
  }
  lasers[0].off();
}

void Drawing::drawObjectRotated3D(const unsigned short* data, int size, long centerX, long centerY, Vector3 rotation) {
  Matrix4 world = Matrix4::rotateX(rotation.x);
  world = Matrix4::multiply(Matrix4::rotateY(rotation.y), world);
  world = Matrix4::multiply(Matrix4::rotateZ(rotation.z), world);
  
  lasers[0].setEnable3D(true);
  lasers[0].setMatrix(world);
  drawObject(data, size, centerX, centerY);  
  lasers[0].setEnable3D(false);
}

void Drawing::calcObjectBox(const unsigned short* data, int size, long& centerX, long& centerY, long& width, long& height) {
  const unsigned short* d = data;
  unsigned short posX;
  unsigned short posY;
  unsigned short x0 = 4096;
  unsigned short y0 = 4096;
  unsigned short x1 = 0;
  unsigned short y1 = 0;
  while (size > 0) {
    posX = pgm_read_word(d) & 0x7fff;
    d++;
    posY = pgm_read_word(d);
    d++;
    size--;
    if (posX < x0) x0 = posX;
    if (posY < y0) y0 = posY;
    if (posX > x1) x1 = posX;
    if (posY > y1) y1 = posY;
  }
  centerX = (x0 + x1) / 2;
  centerY = (y0 + y1) / 2;
  width = x1 - x0;
  height = y1 - y0;
}

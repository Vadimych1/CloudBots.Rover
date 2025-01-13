#include <stdint.h>
#include <cmath>
#include <stdio.h>

extern "C" {

// float
uint8_t encodeFloat2(float val, int byte) {
    uint8_t b[2];
    b[0] = (uint8_t)( (int16_t) (val) & 0x00FF );
    b[1] = (uint8_t)( ((int16_t)(val) >> 8) & 0x00FF);
    return b[byte];
}

float decodeFloat2(uint8_t b1, uint8_t b2) {
    return (float)((uint16_t) b2 << 8 | (uint16_t)b1);
}

float decodeFloat2Abs(uint8_t b1, uint8_t b2) {
    return (float) abs((int16_t)b2<<8|(int16_t)b1);
}

uint8_t encodeFloat3(float val, int byte) {
    uint8_t b[3];
    b[0] =  (uint32_t)val & 0x0000FF;
    b[1] = ((uint32_t)val>>8) & 0x0000FF;
    b[2] = ((uint32_t)val>>16) & 0x0000FF;
    return b[byte];
}

float decodeFloat3(uint8_t b1, uint8_t b2, uint8_t b3) {
    return (float)((int32_t)b3<<16|(int32_t)b2<<8|(int32_t)b1);
}
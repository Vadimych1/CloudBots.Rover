#include <stdint.h>
#include <cmath>

// float
uint8_t* encodeFloat2(float val) {
    uint8_t b[2];
    b[0] = (uint8_t)( (int16_t) (val) & 0x00FF );
    b[1] = (uint8_t)( ((int16_t)(val) >> 8) & 0x00FF);
    return b;
}

float decodeFloat2(uint8_t* b) {
    return (float)((uint16_t) b[1] << 8 | (uint16_t)b[0]);
}

float decodeFloat2Abs(uint8_t* b) {
    return (float) abs((int16_t)b[1]<<8|(int16_t)b[0]);
}

uint8_t* encodeFloat3(float val) {
    uint8_t b[3];
    b[0] =  (uint32_t)val & 0x0000FF;
    b[1] = ((uint32_t)val>>8) & 0x0000FF;
    b[2] = ((uint32_t)val>>16) & 0x0000FF;
    return b;
}

float decodeFloat3(uint8_t* b) {
    return (float)((int32_t)b[2]<<16|(int32_t)b[1]<<8|(int32_t)b[0]);
}


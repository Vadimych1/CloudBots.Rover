#include <stdint.h>

uint8_t encodeFloat2(float val);

float decodeFloat2(uint8_t b1, uint8_t b2);

float decodeFloat2Abs(uint8_t b1, uint8_t b2);

uint8_t encodeFloat3(float val);

float decodeFloat3(uint8_t b1, uint8_t b2, uint8_t b3);
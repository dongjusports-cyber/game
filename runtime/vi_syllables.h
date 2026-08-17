#pragma once
/* Stub — thay bằng font/vi_syllables.h khi compile vào game. */
#include <stdint.h>
#ifndef VI_CELL_W
#define VI_CELL_W 16
#define VI_CELL_H 16
#endif
#define VI_SYLLABLE_COUNT 0
#define VI_SYLLABLE_CODE_COUNT 0
typedef struct {
    const char *text;
    uint8_t gbk_lead, gbk_trail;
    uint16_t x, y, width, height, advance;
} ViSyllableGlyph;
typedef struct { uint16_t code; uint16_t index; } ViSyllableCode;
static const ViSyllableGlyph VI_SYLLABLES[] = {{0}};
static const ViSyllableCode VI_SYLLABLE_CODES[] = {{0, 0}};

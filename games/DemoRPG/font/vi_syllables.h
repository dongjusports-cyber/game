// Auto-generated Vietnamese syllable font lookup
#pragma once
#include <stdint.h>

typedef struct {
    const char *text;
    uint8_t gbk_lead, gbk_trail;
    uint16_t x, y, width, height, advance;
} ViSyllableGlyph;

#define VI_CELL_W 16
#define VI_CELL_H 16
#define VI_SYLLABLE_COUNT 10

static const ViSyllableGlyph VI_SYLLABLES[] = {
    {"Bắt", 0xB0, 0xA1, 0, 0, 16, 16, 16},
    {"Chào", 0xB0, 0xA2, 16, 0, 16, 16, 16},
    {"chào", 0xB0, 0xA3, 32, 0, 16, 16, 16},
    {"chơi", 0xB0, 0xA4, 48, 0, 16, 16, 16},
    {"mừng", 0xB0, 0xA5, 64, 0, 16, 16, 16},
    {"trò", 0xB0, 0xA6, 80, 0, 16, 16, 16},
    {"với", 0xB0, 0xA7, 96, 0, 16, 16, 16},
    {"Xin", 0xB0, 0xA8, 112, 0, 16, 16, 16},
    {"đầu", 0xB0, 0xA9, 128, 0, 16, 16, 16},
    {"đến", 0xB0, 0xAA, 144, 0, 16, 16, 16},
};

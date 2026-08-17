#pragma once
/* Stub — thay bằng font/vi_glyphs.h khi dùng letter mode. */
#include <stdint.h>
#define VI_GLYPH_COUNT 0
typedef struct {
    uint32_t codepoint;
    uint16_t x, y, width, height, advance;
} ViGlyph;
static const ViGlyph VI_GLYPHS[] = {{0}};

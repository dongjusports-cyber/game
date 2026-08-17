/**
 * Runtime vẽ chữ Việt — include vào patch game (GDI / DirectDraw / VGA).
 *
 * Syllable: #include "vi_syllables.h" (generated) rồi gọi vi_draw_cjk2().
 * Letter:   #include "vi_glyphs.h" rồi vi_draw_utf8().
 * Implement ViBlitFn cho backend (SetPixel / buffer 8-bit / DDraw).
 */
#pragma once

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#ifndef VI_CELL_W
#define VI_CELL_W 16
#endif
#ifndef VI_CELL_H
#define VI_CELL_H 16
#endif

typedef struct {
    const uint8_t *atlas;
    int atlas_w, atlas_h;
    int color;
} ViFont;

typedef void (*ViBlitFn)(int x, int y, uint8_t alpha, int color, void *ctx);

int vi_utf8_decode(const char **s);

struct ViGlyph;
struct ViSyllableGlyph;

const struct ViGlyph *vi_find_glyph(uint32_t codepoint);
int vi_text_width(const char *utf8);
void vi_draw_utf8(int x, int y, const char *utf8, const ViFont *font, ViBlitFn blit, void *ctx);

const struct ViSyllableGlyph *vi_find_syllable(uint8_t lead, uint8_t trail);
void vi_draw_cjk2(int x, int y, const uint8_t *bytes, int nbytes,
                  const ViFont *font, ViBlitFn blit, void *ctx);
int vi_cjk2_width(int nbytes);

#ifdef __cplusplus
}
#endif

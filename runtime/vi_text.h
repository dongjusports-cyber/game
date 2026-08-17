/**
 * Runtime vẽ chữ UTF-8 dùng chung — include vào patch DLL / hook game.
 * Không phụ thuộc OS: chỉ cần atlas RGBA + bảng ViGlyph.
 *
 * Tích hợp:
 *   1. Copy vi_glyphs.h (generated) + vi_text.c vào project patch
 *   2. Implement vi_blit_pixel() cho backend game (GDI/DDraw/VGA)
 *   3. Gọi vi_draw_utf8() thay hàm TextOut gốc
 */
#pragma once

#include <stdint.h>
#include "vi_glyphs.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    const uint8_t *atlas;   /* RGBA hoặc alpha-only */
    int atlas_w, atlas_h;
    int color;              /* palette index hoặc RGB565 */
} ViFont;

/* Callback blit 1 pixel — game implement theo backend */
typedef void (*ViBlitFn)(int x, int y, uint8_t alpha, int color, void *ctx);

const ViGlyph *vi_find_glyph(uint32_t codepoint);
int vi_utf8_decode(const char **s);
int vi_text_width(const char *utf8);
void vi_draw_utf8(int x, int y, const char *utf8, const ViFont *font, ViBlitFn blit, void *ctx);

#ifdef __cplusplus
}
#endif

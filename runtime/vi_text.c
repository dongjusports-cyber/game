#include "vi_text.h"

static int vi_glyph_cmp(const void *a, const void *b) {
    uint32_t ca = ((const ViGlyph *)a)->codepoint;
    uint32_t cb = ((const ViGlyph *)b)->codepoint;
    return (ca > cb) - (ca < cb);
}

const ViGlyph *vi_find_glyph(uint32_t codepoint) {
    /* Linear search — đủ nhanh với ~200 glyph; có thể thay binary search */
    for (int i = 0; i < VI_GLYPH_COUNT; ++i) {
        if (VI_GLYPHS[i].codepoint == codepoint) {
            return &VI_GLYPHS[i];
        }
    }
    return 0;
}

int vi_utf8_decode(const char **s) {
    const uint8_t *p = (const uint8_t *)*s;
    if (!*p) return 0;

    if (p[0] < 0x80) {
        *s = (const char *)(p + 1);
        return p[0];
    }
    if ((p[0] & 0xE0) == 0xC0) {
        int cp = ((p[0] & 0x1F) << 6) | (p[1] & 0x3F);
        *s = (const char *)(p + 2);
        return cp;
    }
    if ((p[0] & 0xF0) == 0xE0) {
        int cp = ((p[0] & 0x0F) << 12) | ((p[1] & 0x3F) << 6) | (p[2] & 0x3F);
        *s = (const char *)(p + 3);
        return cp;
    }
    if ((p[0] & 0xF8) == 0xF0) {
        int cp = ((p[0] & 0x07) << 18) | ((p[1] & 0x3F) << 12) |
                 ((p[2] & 0x3F) << 6) | (p[3] & 0x3F);
        *s = (const char *)(p + 4);
        return cp;
    }
    *s = (const char *)(p + 1);
    return '?';
}

int vi_text_width(const char *utf8) {
    int w = 0;
    const char *p = utf8;
    int cp;
    while ((cp = vi_utf8_decode(&p))) {
        const ViGlyph *g = vi_find_glyph((uint32_t)cp);
        w += g ? g->advance : VI_CELL_W / 2;
    }
    return w;
}

void vi_draw_utf8(int x, int y, const char *utf8, const ViFont *font, ViBlitFn blit, void *ctx) {
    const char *p = utf8;
    int cp;
    while ((cp = vi_utf8_decode(&p))) {
        const ViGlyph *g = vi_find_glyph((uint32_t)cp);
        if (!g) {
            x += VI_CELL_W / 2;
            continue;
        }
        for (int row = 0; row < (int)g->height; ++row) {
            for (int col = 0; col < (int)g->width; ++col) {
                int ax = g->x + col;
                int ay = g->y + row;
                int idx = (ay * font->atlas_w + ax) * 4 + 3; /* alpha channel */
                uint8_t a = font->atlas[idx];
                if (a > 0) {
                    blit(x + col, y + row, a, font->color, ctx);
                }
            }
        }
        x += g->advance;
    }
}

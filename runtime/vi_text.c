#include "vi_syllables.h"
#include "vi_glyphs.h"
#include "vi_text.h"

int vi_utf8_decode(const char **s) {
    const uint8_t *p = (const uint8_t *)*s;
    if (!*p) return 0;

    if (p[0] < 0x80) {
        *s = (const char *)(p + 1);
        return p[0];
    }
    if ((p[0] & 0xE0) == 0xC0 && p[1]) {
        int cp = ((p[0] & 0x1F) << 6) | (p[1] & 0x3F);
        *s = (const char *)(p + 2);
        return cp;
    }
    if ((p[0] & 0xF0) == 0xE0 && p[1] && p[2]) {
        int cp = ((p[0] & 0x0F) << 12) | ((p[1] & 0x3F) << 6) | (p[2] & 0x3F);
        *s = (const char *)(p + 3);
        return cp;
    }
    if ((p[0] & 0xF8) == 0xF0 && p[1] && p[2] && p[3]) {
        int cp = ((p[0] & 0x07) << 18) | ((p[1] & 0x3F) << 12) |
                 ((p[2] & 0x3F) << 6) | (p[3] & 0x3F);
        *s = (const char *)(p + 4);
        return cp;
    }
    *s = (const char *)(p + 1);
    return '?';
}

const ViGlyph *vi_find_glyph(uint32_t codepoint) {
    int lo = 0, hi = VI_GLYPH_COUNT - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        uint32_t c = VI_GLYPHS[mid].codepoint;
        if (c == codepoint) return &VI_GLYPHS[mid];
        if (c < codepoint) lo = mid + 1;
        else hi = mid - 1;
    }
    return 0;
}

int vi_text_width(const char *utf8) {
    int w = 0;
    const char *p = utf8;
    int cp;
    while ((cp = vi_utf8_decode(&p))) {
        const ViGlyph *g = vi_find_glyph((uint32_t)cp);
        w += g ? (int)g->advance : VI_CELL_W / 2;
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
        int row, col;
        for (row = 0; row < (int)g->height; ++row) {
            for (col = 0; col < (int)g->width; ++col) {
                int ax = g->x + col;
                int ay = g->y + row;
                int idx = (ay * font->atlas_w + ax) * 4 + 3;
                uint8_t a = font->atlas[idx];
                if (a > 0)
                    blit(x + col, y + row, a, font->color, ctx);
            }
        }
        x += (int)g->advance;
    }
}

const ViSyllableGlyph *vi_find_syllable(uint8_t lead, uint8_t trail) {
    uint16_t code = ((uint16_t)lead << 8) | trail;
    int lo = 0, hi = VI_SYLLABLE_CODE_COUNT - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        uint16_t c = VI_SYLLABLE_CODES[mid].code;
        if (c == code) return &VI_SYLLABLES[VI_SYLLABLE_CODES[mid].index];
        if (c < code) lo = mid + 1;
        else hi = mid - 1;
    }
    return 0;
}

int vi_cjk2_width(int nbytes) {
    return (nbytes / 2) * VI_CELL_W;
}

void vi_draw_cjk2(int x, int y, const uint8_t *bytes, int nbytes,
                  const ViFont *font, ViBlitFn blit, void *ctx) {
    int i;
    for (i = 0; i + 1 < nbytes; i += 2) {
        const ViSyllableGlyph *g = vi_find_syllable(bytes[i], bytes[i + 1]);
        if (g && font && font->atlas && blit) {
            int row, col;
            for (row = 0; row < (int)g->height; ++row) {
                for (col = 0; col < (int)g->width; ++col) {
                    int ax = g->x + col;
                    int ay = g->y + row;
                    int idx = (ay * font->atlas_w + ax) * 4 + 3;
                    uint8_t a = font->atlas[idx];
                    if (a > 0)
                        blit(x + col, y + row, a, font->color, ctx);
                }
            }
        }
        x += VI_CELL_W;
    }
}

/* The values the rasterkit modules pass to one another. */
#ifndef RASTERKIT_RASTER_H
#define RASTERKIT_RASTER_H

#include <stddef.h>
#include <stdint.h>

/* Channels per pixel. In RGBA, alpha 0 is transparent and 255 opaque. */
typedef enum { RK_GRAY = 1, RK_RGB = 3, RK_RGBA = 4 } rk_channels;

/*
 * An image: 8 bits per channel, rows top to bottom, pixels left to right, channels interleaved
 * (R, G, B, A), no padding between rows. `data` holds width x height x channels bytes.
 */
typedef struct {
    int width;
    int height;
    int channels;
    uint8_t *data;
} rk_image;

/* The largest width or height any module accepts or makes. */
#define RK_MAX_DIMENSION 32768

typedef enum {
    RK_OK = 0,
    RK_ERR_IO,          /* a file could not be read or written */
    RK_ERR_FORMAT,      /* the bytes are not a valid file of the format */
    RK_ERR_UNSUPPORTED, /* a valid file in a variant rasterkit does not read */
    RK_ERR_ARGUMENT,    /* a parameter out of range */
    RK_ERR_NOMEM,       /* an allocation failed */
} rk_status;

#define RK_MESSAGE_MAX 160

/* What went wrong. `offset` is the byte of the input the problem was found at, or -1. */
typedef struct {
    rk_status status;
    long offset;
    char message[RK_MESSAGE_MAX];
} rk_error;

#define RK_PALETTE_MAX 256

/* Up to 256 colors, each as red, green and blue. */
typedef struct {
    int count;
    uint8_t rgb[RK_PALETTE_MAX][3];
} rk_palette;

/* A zero-filled image, or NULL for a size outside 1..RK_MAX_DIMENSION, bad channels or no memory. */
rk_image *rk_image_new(int width, int height, int channels);

/* A copy of `image`, or NULL when memory runs out. */
rk_image *rk_image_clone(const rk_image *image);

/* Frees the image and its data; NULL is allowed. */
void rk_image_free(rk_image *image);

/* The number of bytes in `image->data`. */
size_t rk_image_size(const rk_image *image);

/* The first channel of the pixel at (x, y); the caller keeps x and y in range. */
uint8_t *rk_pixel(const rk_image *image, int x, int y);

/*
 * Fills `error`, when it is not NULL, with `status`, `offset` and the printf-style message
 * (cut to RK_MESSAGE_MAX - 1 characters), and returns `status`.
 */
rk_status rk_fail(rk_error *error, rk_status status, long offset, const char *format, ...);

/* "ok", "io", "format", "unsupported", "argument" or "nomem". */
const char *rk_status_name(rk_status status);

#endif

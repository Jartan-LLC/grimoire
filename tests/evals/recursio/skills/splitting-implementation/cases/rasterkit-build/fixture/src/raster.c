#include "raster.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

rk_image *rk_image_new(int width, int height, int channels) {
    if (width < 1 || height < 1 || width > RK_MAX_DIMENSION || height > RK_MAX_DIMENSION) {
        return NULL;
    }
    if (channels != RK_GRAY && channels != RK_RGB && channels != RK_RGBA) {
        return NULL;
    }
    rk_image *image = malloc(sizeof *image);
    if (image == NULL) {
        return NULL;
    }
    image->width = width;
    image->height = height;
    image->channels = channels;
    image->data = calloc((size_t)width * (size_t)height, (size_t)channels);
    if (image->data == NULL) {
        free(image);
        return NULL;
    }
    return image;
}

rk_image *rk_image_clone(const rk_image *image) {
    rk_image *copy = rk_image_new(image->width, image->height, image->channels);
    if (copy != NULL) {
        memcpy(copy->data, image->data, rk_image_size(image));
    }
    return copy;
}

void rk_image_free(rk_image *image) {
    if (image != NULL) {
        free(image->data);
        free(image);
    }
}

size_t rk_image_size(const rk_image *image) {
    return (size_t)image->width * (size_t)image->height * (size_t)image->channels;
}

uint8_t *rk_pixel(const rk_image *image, int x, int y) {
    return image->data + ((size_t)y * (size_t)image->width + (size_t)x) * (size_t)image->channels;
}

rk_status rk_fail(rk_error *error, rk_status status, long offset, const char *format, ...) {
    if (error != NULL) {
        error->status = status;
        error->offset = offset;
        va_list args;
        va_start(args, format);
        vsnprintf(error->message, sizeof error->message, format, args);
        va_end(args);
    }
    return status;
}

const char *rk_status_name(rk_status status) {
    switch (status) {
    case RK_OK:
        return "ok";
    case RK_ERR_IO:
        return "io";
    case RK_ERR_FORMAT:
        return "format";
    case RK_ERR_UNSUPPORTED:
        return "unsupported";
    case RK_ERR_ARGUMENT:
        return "argument";
    case RK_ERR_NOMEM:
        return "nomem";
    }
    return "unknown";
}

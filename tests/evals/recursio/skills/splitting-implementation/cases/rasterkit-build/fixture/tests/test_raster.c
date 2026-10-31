#include <string.h>

#include "check.h"
#include "raster.h"

static void test_new_image_is_zero_filled(void) {
    rk_image *image = rk_image_new(3, 2, RK_RGB);
    CHECK(image != NULL);
    CHECK(rk_image_size(image) == 18);
    CHECK(image->data[17] == 0);
    rk_image_free(image);
}

static void test_bad_sizes_and_channels_are_refused(void) {
    CHECK(rk_image_new(0, 5, RK_GRAY) == NULL);
    CHECK(rk_image_new(5, RK_MAX_DIMENSION + 1, RK_GRAY) == NULL);
    CHECK(rk_image_new(5, 5, 2) == NULL);
}

static void test_pixels_are_interleaved_row_by_row(void) {
    rk_image *image = rk_image_new(2, 2, RK_RGBA);
    rk_pixel(image, 1, 1)[3] = 200;
    CHECK(image->data[15] == 200);
    rk_image *copy = rk_image_clone(image);
    CHECK(memcmp(copy->data, image->data, rk_image_size(image)) == 0);
    rk_image_free(copy);
    rk_image_free(image);
}

static void test_fail_fills_the_error(void) {
    rk_error error;
    CHECK(rk_fail(&error, RK_ERR_FORMAT, 7, "bad magic %s", "P9") == RK_ERR_FORMAT);
    CHECK(error.offset == 7);
    CHECK(strcmp(error.message, "bad magic P9") == 0);
    CHECK(rk_fail(NULL, RK_ERR_IO, -1, "ignored") == RK_ERR_IO);
    CHECK(strcmp(rk_status_name(RK_ERR_UNSUPPORTED), "unsupported") == 0);
}

int main(void) {
    test_new_image_is_zero_filled();
    test_bad_sizes_and_channels_are_refused();
    test_pixels_are_interleaved_row_by_row();
    test_fail_fills_the_error();
    return check_report("test_raster");
}

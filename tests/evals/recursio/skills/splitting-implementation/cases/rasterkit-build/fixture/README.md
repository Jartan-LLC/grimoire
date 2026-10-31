# rasterkit

Reads and writes Netpbm and BMP images, crops, rotates and resizes them, filters them, and reduces
them to a palette with dithering, as a C library and a command. C11 with libc and libm only. `make`
builds `build/librasterkit.a` from every file in `src/` but `cli.c`, one test program per
`tests/test_*.c`, and `build/rasterkit`; `make test` runs the test programs.

## Contract

`src/raster.h` and `src/raster.c` hold what the modules pass to one another: `rk_image`,
`rk_channels`, `rk_status`, `rk_error`, `rk_palette`, the limits `RK_MAX_DIMENSION`,
`RK_MESSAGE_MAX` and `RK_PALETTE_MAX`, and the helpers `rk_image_new`, `rk_image_clone`,
`rk_image_free`, `rk_image_size`, `rk_pixel`, `rk_fail` and `rk_status_name`. Each module below has
its own header and source in `src/` and its own test program, and uses only the contract and
nothing of its siblings; only the command uses them all.

A function that can fail returns `rk_status` and, given a non-NULL `rk_error *`, fills it through
`rk_fail`. A function that makes an image returns it through `rk_image **out`, left NULL on failure.
No function changes its input image, exits the process, or leaks memory on a failure path. Wherever
a result is converted back to 8 bits it is rounded half up (x.5 goes up), then clamped to 0..255.

## Netpbm (`src/pnm.h`, `src/pnm.c`)

- `rk_pnm_read(const uint8_t *bytes, size_t length, rk_image **out, rk_error *error)` reads P1
  to P7.
- Header: the magic, then width, height and (except in P1 and P4) maxval, as decimal numbers
  separated by whitespace (space, tab, CR, LF, VT, FF). A `#` anywhere whitespace may stand starts a
  comment that runs to the end of its line. In P4, P5 and P6 exactly one whitespace character
  follows the last header number, then the raster starts.
- P1 and P4 are bitmaps in which 1 is black: they read as gray, 1 as 0 and 0 as 255. P4 packs each
  row most significant bit first and pads it to a whole byte. In P1 the digits may run together
  (`0110`).
- P2 and P5 are gray, P3 and P6 RGB. maxval is 1 to 65535; above 255 each binary sample is two
  bytes, most significant first. Samples are scaled as `sample x 255 / maxval`, rounded half up, so
  with maxval 1023 a sample of 512 reads as 128.
- P7 (PAM): lines `WIDTH`, `HEIGHT`, `DEPTH`, `MAXVAL` and an optional `TUPLTYPE`, each a keyword,
  whitespace and a value, in any order, ending with `ENDHDR`. DEPTH 1 is gray, 3 RGB, 4 RGBA, and 2
  gray with alpha, which reads as RGBA with the gray copied to red, green and blue. A TUPLTYPE must
  agree with DEPTH: `BLACKANDWHITE` or `GRAYSCALE` 1, `GRAYSCALE_ALPHA` 2, `RGB` 3, `RGB_ALPHA` 4.
  In `BLACKANDWHITE`, unlike P1 and P4, 0 is black and 1 white.
- Errors, all `RK_ERR_FORMAT` with `offset` at the byte where the problem was found: a bad magic, a
  missing or non-numeric header field, a width or height of 0 or over `RK_MAX_DIMENSION`, a maxval
  out of range, a sample over maxval, a missing PAM field or a TUPLTYPE that disagrees, and data
  that ends early (`offset` is then `length`). Bytes after the first image are ignored.
- `rk_pnm_write(const rk_image *image, rk_pnm_format format, uint8_t **bytes, size_t *length,
  rk_error *error)` returns a buffer the caller frees. `rk_pnm_format` is one of `RK_PBM_ASCII`,
  `RK_PGM_ASCII`, `RK_PPM_ASCII` (P1 to P3), `RK_PBM`, `RK_PGM`, `RK_PPM` (P4 to P6) and `RK_PAM`.
- The header is the magic, width and height, and maxval 255 (none in P1 and P4), each on its own
  line, no comments: `P6\n640 480\n255\n`. PAM writes `WIDTH`, `HEIGHT`, `DEPTH`, `MAXVAL 255`,
  `TUPLTYPE` (`GRAYSCALE`, `RGB` or `RGB_ALPHA`) and `ENDHDR`, one per line, and the image's own
  channels.
- Bitmaps and gray formats take gray images only: an RGB or RGBA image is `RK_ERR_ARGUMENT`. In a
  bitmap a value below 128 is black. P3 and P6 repeat a gray value three times and drop an alpha
  channel.
- In P2 and P3 samples are separated by single spaces; P1 writes its digits with no space. Every
  image row starts a new line, and a line that would pass 70 characters is broken before the
  sample that would pass it.

## BMP (`src/bmp.h`, `src/bmp.c`)

- `rk_bmp_read(const uint8_t *bytes, size_t length, rk_image **out, rk_error *error)`. Integers
  are little-endian. The 14-byte file header holds `BM`, the file size (not checked), two reserved
  fields and the offset of the pixel data.
- The info header is known by its size: 12 (OS/2, 16-bit width and height, palette entries of
  three bytes B, G, R), 40, 108 (V4) or 124 (V5), with palette entries of four bytes B, G, R and
  one unused. Any other size is `RK_ERR_UNSUPPORTED`.
- Bits per pixel 1, 4 and 8 use a palette of `colors used` entries (0 means 2 to the bits per
  pixel); 16, 24 and 32 hold colors directly. Compression 0 (none); 1 (RLE8) with 8 bits; 2 (RLE4)
  with 4 bits; 3 (bit fields) with 16 or 32 bits, its red, green and blue masks in the 12 bytes
  after a 40-byte header, or in a V4 or V5 header together with an alpha mask. Compression 4 and 5
  (embedded JPEG and PNG) and any other are `RK_ERR_UNSUPPORTED`.
- Uncompressed, 16 bits are 5-5-5 (one unused bit, then red, green and blue) and 32 bits are B, G,
  R and one unused byte. A masked value is scaled as `value x 255 / max`, `max` being the largest
  value its mask holds, rounded half up: the 5-bit value 16 reads as 132. A mask whose bits are not
  contiguous is `RK_ERR_FORMAT`.
- Each row is padded to a multiple of 4 bytes. A positive height stores rows bottom-up, a negative
  one top-down; an RLE image with a negative height is `RK_ERR_FORMAT`.
- RLE8 is pairs of bytes: a count of 1 to 255 repeats the next byte that many times. A count of 0
  is an escape, by the byte after it: 0 ends the row, 1 ends the image, 2 moves right and down by
  the two bytes that follow, and 3 to 255 are that many literal pixels, padded to an even number of
  bytes. RLE4 is the same with two pixels per byte, high nibble first, alternating for a run.
  Pixels the stream skips take palette index 0.
- An image whose palette entries all have equal red, green and blue reads as gray; other palette
  images, and 16- and 24-bit ones, read as RGB. A 32-bit image reads as RGBA when it has an alpha
  mask and some pixel's alpha is not 0, and as RGB otherwise, since many files leave alpha at 0.
- Errors are `RK_ERR_FORMAT` with an offset, as for Netpbm: a bad signature, a truncated file, a
  pixel data offset past the end, a palette index past the palette, an RLE run that passes the end
  of its row or of the image.
- `rk_bmp_write(const rk_image *image, uint8_t **bytes, size_t *length, rk_error *error)` writes
  bottom-up with correct file sizes and 2835 pixels per metre both ways: gray as 8 bits with a
  256-entry gray palette and a 40-byte header, RGB as 24 bits with a 40-byte header, RGBA as 32
  bits with compression 3 and a 108-byte V4 header, masks `0x00FF0000`, `0x0000FF00`,
  `0x000000FF` and `0xFF000000`, color space `sRGB` (`0x73524742`). Every image read back from
  `rk_bmp_write` equals the one written, except an RGBA image whose alpha is 0 throughout, which
  reads back as RGB.

## Geometry (`src/transform.h`, `src/transform.c`)

Each function returns a new image with the input's channels.

- `rk_crop(image, x, y, width, height, out, error)`: the rectangle must be at least 1x1 and lie
  inside the image, or it is `RK_ERR_ARGUMENT`.
- `rk_flip(image, RK_FLIP_HORIZONTAL or RK_FLIP_VERTICAL, out, error)`, `rk_transpose(image, out,
  error)` and `rk_rotate(image, degrees, out, error)`: clockwise by any multiple of 90, negative
  turning the other way; any other angle is `RK_ERR_ARGUMENT`.
- `rk_trim(image, tolerance, out, error)`: removes the border rows and columns in which every
  channel of every pixel is within `tolerance` of the top-left pixel's. An image that is all border
  becomes that one pixel.
- `rk_resize(image, width, height, filter, out, error)`, `filter` one of `RK_NEAREST`,
  `RK_BILINEAR`, `RK_BICUBIC`, `RK_LANCZOS` and `RK_BOX`. A size of 0 or over `RK_MAX_DIMENSION` is
  `RK_ERR_ARGUMENT`. Width and height are resampled one after the other.
- Destination pixel `x` samples the source at `(x + 0.5) x source_width / width - 0.5`, and
  likewise down the rows. Nearest takes source pixel `floor((x + 0.5) x source_width / width)`.
  Bilinear weighs by the triangle `1 - |d|` within 1 pixel, bicubic by Keys' cubic with a = -0.5
  within 2, Lanczos by `sinc(d) sinc(d / 3)` within 3. When shrinking, each kernel is widened by
  the scale factor so every source pixel contributes. Weights are normalised to sum to 1, and
  positions past an edge take the edge pixel. Box averages the source area each destination pixel
  covers, a partly covered pixel weighed by the part it covers.
- So a 2x1 gray image `0 255` resized to 4x1 bilinear is `0 64 191 255`, and `0 100 200 255`
  resized to 2x1 box is `50 228`.
- RGBA is resized with premultiplied alpha: the color channels are multiplied by alpha before and
  divided after, and a pixel whose alpha comes out 0 is all zeros.
- `rk_fit(image, max_width, max_height, filter, out, error)`: the largest size within the box that
  keeps the aspect ratio, each side rounded half up and at least 1: 640x480 into 200x200 is 200x150.

## Filters (`src/filter.h`, `src/filter.c`)

The filters work on the color channels and copy an alpha channel unchanged, unless one below says
otherwise; neighbours past an edge repeat the edge pixel. Each but `rk_histogram` returns a new
image.

- `rk_to_gray(image, out, error)`: Rec. 709 luma, computed as `(2126 R + 7152 G + 722 B + 5000) /
  10000` in integers, so pure red is 54 and pure green 182. The result is gray, and alpha is
  dropped. A gray image is copied.
- `rk_convolve(image, kernel, size, divisor, bias, out, error)`: an integer kernel of odd `size`
  from 1 to 15, row by row; each output is the weighted sum divided by `divisor` (not 0), plus
  `bias`, rounded and clamped.
- `rk_box_blur(image, radius, out, error)`: the mean of the `(2 radius + 1)` square around each
  pixel, in time that does not grow with the radius (running sums). Radius 0 copies.
- `rk_gaussian_blur(image, sigma, out, error)`: weights `exp(-d^2 / (2 sigma^2))` out to
  `ceil(3 sigma)`, normalised, applied across then down, in floating point and rounded once at the
  end, not between the two passes. Sigma 0 copies; a sigma below 0 or over 100 is
  `RK_ERR_ARGUMENT`.
- `rk_unsharp(image, sigma, amount, threshold, out, error)`: each channel becomes `v + amount x
  (v - blurred)`, the blur Gaussian with `sigma`, where `|v - blurred|` is at least `threshold`, and
  stays `v` elsewhere.
- `rk_sobel(image, out, error)`: the gradient magnitude `sqrt(gx^2 + gy^2)` of the luma above with
  the 3x3 Sobel kernels, as a gray image; alpha is dropped.
- `rk_levels(image, black, white, gamma, out, error)`: `255 x t^(1 / gamma)`, where `t` is
  `(v - black) / (white - black)` clamped to 0..1. `black` must be below `white` and gamma within
  0.1 to 10.
- `rk_histogram(image, counts)` fills `counts[channel][value]` for every channel, alpha included.
- `rk_auto_contrast(image, clip_percent, out, error)`: the lowest and highest color values once
  `clip_percent` of the color samples are ignored at each end, all color channels counted
  together, become 0 and 255 through `rk_levels` with gamma 1. When the two are equal, it copies.
- `rk_invert(image, out, error)`: each color channel becomes `255 - v`.

## Palettes and dithering (`src/dither.h`, `src/dither.c`)

- `rk_palette_named(name, palette, error)`: `bw` (black, white); `gray4` (0, 85, 170, 255);
  `gray16` (0, 17, ... 255); `web`, the 216 colors with each channel one of 0, 51, 102, 153, 204
  and 255, at index `36 r + 6 g + b`; `cga`, the 16 colors `000000 0000AA 00AA00 00AAAA AA0000
  AA00AA AA5500 AAAAAA 555555 5555FF 55FF55 55FFFF FF5555 FF55FF FFFF55 FFFFFF`. Another name is
  `RK_ERR_ARGUMENT`.
- `rk_palette_parse(text, palette, error)`: 1 to 256 colors written `#RRGGBB`, either case,
  separated by commas or whitespace.
- `rk_median_cut(image, count, palette, error)`, `count` 1 to 256. Alpha is ignored and a gray
  pixel counts as red, green and blue all equal. Start with one box of every pixel's color. While
  there are fewer than `count` boxes and some box holds two or more distinct colors, take the box
  with the widest range on any channel (on a tie the one with more pixels, then the earlier one),
  sort its pixels by that channel, and cut it at its middle: the lower half, `n / 2` pixels rounded
  down, stays in its place and the upper half goes at the end of the list. Each box's color is
  the mean of its pixels, rounded, in list order.
- `rk_dither(image, palette, options, out, error)` replaces every pixel's color with a palette
  color and copies alpha. `rk_dither_options` holds `method`, `serpentine` and `spread`. The
  nearest color is the smallest squared distance in red, green and blue, the lower index on a tie.
  A gray image stays gray when every palette color is gray, and becomes RGB otherwise.
- `RK_DITHER_NONE` takes the nearest color. `RK_DITHER_BAYER2`, `4` and `8` add
  `((M + 0.5) / n^2 - 0.5) x spread` to each channel first, `M` the Bayer matrix entry at
  `(x mod n, y mod n)`: `[[0, 2], [3, 1]]`, and each larger matrix built as
  `[[4M, 4M + 2], [4M + 3, 4M + 1]]`.
- Error diffusion keeps each channel's error in floating point, adds the error pushed to a pixel
  before its lookup (clamped to 0..255), and drops error pushed past an edge.
  `RK_DITHER_FLOYD_STEINBERG` pushes 7/16 right, 3/16 below left, 5/16 below and 1/16 below right;
  `RK_DITHER_ATKINSON` 1/8 each right, two right, below left, below, below right and two below;
  `RK_DITHER_SIERRA_LITE` 2/4 right, 1/4 below left and 1/4 below. With `serpentine`, odd rows
  (from 0) run right to left with the pattern mirrored.
- So a 4x1 gray image of 128s, dithered to `bw` with Floyd-Steinberg, is `255 0 255 0`.

## Command (`src/cli.c`, built as `build/rasterkit`)

The format to write comes from the output's extension, in any case: `.pbm`, `.pgm`, `.ppm`, `.pnm`
(P5 for gray, P6 otherwise), `.pam` and `.bmp`. Input is recognised by its first bytes, `P1` to
`P7` or `BM`, whatever its name.

- `rasterkit info FILE...` prints one line per file: `photo.bmp: 640x480 rgb (bmp)`, the channels
  named `gray`, `rgb` or `rgba` and the format `bmp` or the Netpbm magic, as `(P6)`.
- `rasterkit convert [--ascii] IN OUT`: `--ascii` writes P1, P2 or P3. A color image written as
  `.pgm` or `.pbm` goes through `rk_to_gray` first.
- `rasterkit edit IN OUT OP...` applies the operations from left to right: `crop=X,Y,W,H`,
  `flip=h`, `flip=v`, `rotate=DEG`, `transpose`, `trim[=TOL]` (default 0), `resize=WxH[:FILTER]`
  (leave W or H empty to keep the aspect ratio, rounded half up: `resize=800x`),
  `fit=WxH[:FILTER]`, `gray`, `blur=SIGMA`, `boxblur=R`, `sharpen=SIGMA,AMOUNT[,THRESHOLD]`
  (threshold 0 when left out), `edges`, `levels=BLACK,WHITE[,GAMMA]` (gamma 1 when left out),
  `autocontrast[=PCT]` (default 0.5), `invert`, and `dither=PALETTE[:METHOD[:serpentine]]`.
  FILTER is `nearest`, `bilinear`, `bicubic`, `lanczos` (the default) or `box`. PALETTE is a
  palette name, a color list as `#000000,#ffffff`, or `auto-N` for a median cut to N colors; METHOD
  is `none`, `bayer2`, `bayer4`, `bayer8`, `fs` (the default), `atkinson` or `sierra`, and the
  Bayer spread is 64.
- `rasterkit histogram FILE` prints 256 lines, the value then one count per channel.

An image that cannot be read, or an operation that fails, prints `rasterkit: FILE: offset N:
message` (without the offset when it is -1) to stderr and exits 1. A usage error, an unknown
operation or a malformed operation argument prints a usage line and exits 2. Output goes to a
temporary file beside OUT that is renamed over it, so a failed run leaves OUT as it was.

## Status

Only the contract exists. Each module gets its own test program, `tests/test_<module>.c`.

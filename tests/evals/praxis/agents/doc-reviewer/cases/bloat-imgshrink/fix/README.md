# imgshrink

Shrink images for the web.

## Usage

`imgshrink photos/` re-encodes every JPEG and PNG in `photos/` in place. `--quality N` sets the
JPEG quality; it defaults to 80.

CMYK JPEGs are converted to RGB. An EXIF orientation is applied before the EXIF data is dropped.
Files over 100 MB are skipped with a message.

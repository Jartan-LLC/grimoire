# scan2txt

Turn scanned PDFs into text.

## Usage

`scan2txt letter.pdf` writes the text of every page to `letter.txt`. `--lang CODE` sets the
language; it defaults to `eng`.

Rotated pages are detected and turned. Pages scanned above 600 dpi are downsampled first. A
password-protected PDF is skipped with a message.

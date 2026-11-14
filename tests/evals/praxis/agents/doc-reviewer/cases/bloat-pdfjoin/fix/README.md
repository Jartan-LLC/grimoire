# pdfjoin

Join PDF files into one.

## Usage

`pdfjoin out.pdf a.pdf b.pdf` joins `a.pdf` and `b.pdf`, in the order given, into `out.pdf`.

An encrypted PDF with an empty owner password is opened. Bookmarks nested deeper than 10 levels
are flattened. A file with a broken xref table is rebuilt first.

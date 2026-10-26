Bug #61: `split_row('a,"b,c",d')` returns four fields; a comma inside quotes shouldn't split. Please fix it
(with a test) and commit. Quoted fields that contain a newline are broken too, but that one needs the
reader to work across lines, so it stays open as #62.

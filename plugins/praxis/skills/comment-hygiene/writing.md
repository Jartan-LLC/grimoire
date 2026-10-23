# Writing comments, docstrings and file headers

Write for whoever edits or calls this code later, with the code open and none of your notes. Judge the content before the wording. For each comment, docstring or header, ask what that reader does differently because it is there.

- Keep what the code cannot say: the reason for a choice that looks wrong or arbitrary, a hazard an edit would trip (an ordering, a side effect, a platform quirk), the spec, upstream bug or issue that dictates the shape, what a caller needs that the signature does not give, and what a new file owns.
- Leave out what the reader gets from the code, the signature or another file: what a line does, a value the code declares, a type or default the signature gives, and a policy a document states (point to the document instead). Leave out the change itself: what it replaced, why it was made, which task asked for it.
- Give the reason itself; a ticket id alone tells the reader nothing.
- Update or remove an existing comment that the change makes false.
- Write plainly: one point per comment, plain words.

Last, check each sentence against the code as it now stands: drop a reason from your notes or an earlier commit that the final code no longer bears out, and add nothing your inputs do not support.

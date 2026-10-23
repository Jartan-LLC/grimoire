# Issue Bodies

The project's issue templates and rules win where they speak. Write for whoever implements the issue: often an agent in a later session that has only the issue.

Judge the content before the wording. For each passage, ask what the implementer does differently because it is there. Keep everything they act on: the problem and where it shows (the command, its output, the version), the expected result, the scope and what is out of it, the constraints a fix must keep, the open questions, and links to what the issue builds on. Cut what they would get from the code or the linked material.

- State the problem before any fix. A fix you only have in mind is a proposal, marked as one; a fix already decided goes in as the expected result, after the problem.
- Name each place the problem shows (every copy of a wrong line, the function that fails), but leave out the list of files a fix would touch, the steps of a fix and effort estimates: they are the implementer's working notes.
- Leave out the session: local paths, your working branch, how long it took. Keep a path, branch, command or output when it shows the problem.
- Quote error text, versions and strings exactly as your inputs give them, and add none they do not give.
- Whatever the project's rules say, put no exploit or reproduction detail of a security flaw whose fix is not released in a public issue, unless it links the released fix or a public advisory; otherwise point the user to the private channel the project's SECURITY.md names.
- Fill the template's sections with this content; leave out an optional section your inputs cannot fill, and for a required one ask the user or say it is not known.
- Title: the component, then the symptom or the need ("docs: the install page gives a flag the CLI removed in 2.0").

Last, check the result: nothing the implementer acts on was lost, and nothing was added that your inputs do not support.

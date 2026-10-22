# Issue Bodies

The project's issue templates and rules win where they speak. Write for whoever implements the issue: often an agent in a later session that has only the issue.

Judge the content before the wording. For each passage, ask what the implementer does differently because it is there. Keep everything they act on: the problem and where it shows (the command, its output, the version), the expected result, the scope and what is out of it, the constraints a fix must keep, the open questions, and links to what the issue builds on. Cut what they would get from the code or the linked material.

- State the problem before any fix. A fix you have in mind is a proposal, marked as one, never the problem statement.
- Name each place the problem shows (every copy of a wrong line, the function that fails), but leave out the list of files a fix would touch, step lists and effort estimates: they are the implementer's working notes.
- Leave out the session: local paths, branch names, how long it took. Keep a command and its output when they show the problem.
- Quote error text, versions and strings exactly as your inputs give them, and add none they do not give.
- Fill the template's sections with this content.
- Title: the component, then the symptom or the need ("CI: require a plugin version bump when a plugin's files change").

Last, check the result: nothing the implementer acts on was lost, and nothing was added that your inputs do not support.

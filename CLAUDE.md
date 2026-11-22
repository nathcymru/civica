# Project rules for Claude

## Published content

NEVER add developer comments, caveats, status notes or explanations of how something is built to anything an end user can see. Always assume the reader is an end user, with no exception. This covers page text, component text, button and message wording, alt text, hidden text, examples and the design system itself. Put developer notes in code comments, commit messages or pull request descriptions only.

## Page text

Never name GOV.UK, ONS or NHS in page text, headings, captions, alt text or examples. The only exceptions are one `<p><small>Source note: ...</small></p>` at the foot of a section index, and the licensing and sources pages. Never say Civica follows, mirrors, matches or adapts an outside source. Write "Civica" with a capital C in user-facing text. Never show internal rule IDs to readers.

## Working method

- Show a plan for approval before big or risky changes. Do not make changes that were not approved.
- Threads merge their own pull requests once checks pass. Do not ask for a merge.
- Keep runs lean: one writer pass and one editor pass per batch, build only what changed, at most 6 pages per pull request.
- Never edit the files listed in `.claude/protected-baseline.json` or in `historical_files` of `docs/data/naming-inventory.json`.
- Before saying a page matches a reference, measure the reference and the built page at 1280px and 320px, and compare screenshots.
- Use the specialist agents in `.claude/agents/` for page work, in the order writer, editor, illustrator, data visualiser, editor. An agent never approves its own work.

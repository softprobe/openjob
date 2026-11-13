# LinkedIn

Draft. Do not post.

The maintainer posts this from their own LinkedIn account. Do not add a phone number or a personal email to the post or the comments. If someone asks for a résumé by mail, point them at the pull request template.

---

OpenJob is a job board stored as Markdown files in a public GitHub repository.

You publish a role or a talent profile by opening a pull request. A checker validates the shape of the file, rejects phone numbers and personal email addresses (including the usual obfuscations), and squash-merges the pull request when it only touches that one post. Search is a static page: role, location, remote, language, tags.

Jobs stay up for 60 days and profiles for 180 unless the author renews them. Expired posts leave the tree. The git history is the archive. If you want the canonical profile in your own account, put it in a repository named `openjob-profile` and add a short index entry to the board.

I built it because hiring posts kept asking for a phone number before they had earned one. The contact path here is a link you already control: LinkedIn, GitHub, a personal site, or the company careers page.

English and Chinese in the same post are both fine.

Repository: https://github.com/zwobill/openjob
Search page: https://zwobill.github.io/openjob/

The files on the board marked as samples are examples of the format, not openings.

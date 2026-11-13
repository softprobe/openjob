# Hacker News

Draft. Do not post.

Submit as a Show HN only when the Pages site loads and the repository is public. Use a title that describes the thing, not the marketing line. HN titles should stay under 80 characters.

## Title

Show HN: OpenJob – a GitHub-native job board with no phone numbers

## URL

https://zwobill.github.io/openjob/

If the site is down, submit the repository URL instead and say so in the first comment. Do not submit both.

## First comment

I built OpenJob because I wanted a job board that is just files.

A job, a talent profile, or a company page is a Markdown file with YAML front matter. You add it in a pull request. GitHub Actions checks the schema, the sharded path, a 10 KB text limit, and a privacy rule: no phone numbers and no personal email, including `name [at] domain` style obfuscation and Chinese mobile formats. If the pull request only touches that one file, it squash-merges.

Jobs expire after 60 days, profiles after 180, unless the author sets `renewed`. The expiry job opens a pull request that deletes them. Git history is the archive, so the repo does not grow an `archive/` tree.

Federation: you can keep the full profile in `<you>/openjob-profile` and commit a small `talent-ref` index entry here. The static site searches the index in the browser. There is no backend and no account.

Code is MIT. Post text is CC BY 4.0.

What is deliberately missing: messaging, ranking, recommendations, and any field for an email or a phone. Contact is a LinkedIn URL, GitHub profile, personal site, or a careers link.

Repo: https://github.com/zwobill/openjob

Happy to answer how the auto-merge is locked to the workflow on `main` (pull_request_target, so the PR cannot replace the checker), and where that still depends on repository settings.

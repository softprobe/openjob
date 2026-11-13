# Security and takedown

## Do not post private contact details

Phone numbers do not belong anywhere in this repository, including issue comments and pull request descriptions. Personal email addresses do not belong in talent posts, in the body of a job, or in issues and pull request descriptions. A job may contain one hiring address in `apply` or `apply_email` when its domain matches the company website. The checker rejects every other address. It also rejects common disguises: `name [at] domain [dot] com`, fullwidth characters, HTML entities, percent-encoding, spaces inside numbers, and Chinese numerals. That is not a promise that every disguise will be caught. Reviewers still remove leaks the checker misses.

Allowed contact: a LinkedIn URL, a GitHub profile, a personal site, a company careers/apply link, or that one hiring address on a job.

## Report a vulnerability

For a bug in the checker, the workflows, or the Pages site, open a [private security advisory](https://github.com/softprobe/openjob/security/advisories/new). Do not include a phone number or a personal email. Describe the behavior and the file.

The auto-merge workflow uses `pull_request_target` so the checker that runs is the one already on `main`. It reads the pull request as data. It does not install the pull request's dependencies and it does not execute the pull request's scripts. A pull request that edits `.github/workflows/` does not auto-merge.

## Ask for a post to be removed

The fastest removal of your own post is a pull request that deletes the file. You have to be the `github` or `posted_by` account. That pull request can squash-merge on its own.

To report someone else's post, open an **Abuse or takedown** issue, or a private advisory if the report itself would spread personal data. Grounds include a phone number or email, spam, impersonation, harassment, and illegal content. Say which file and why. Do not add your own contact details.

A maintainer (`@softprobe/openjob-maintainers`, or `@zwobill`) removes the file with a pull request and, if branch protection is on, uses the admin bypass because the checker will refuse an edit or deletion by anyone except the original author. The maintainer deletes the post; they do not rewrite it. Git history still contains the old blob. Say so in the takedown pull request. GitHub support can help with cached copies if a later purge is required.

## Archive

Expired posts are deleted from the live tree by the scheduled workflow. Git history is the archive. See `CONTRIBUTING.md`.

## What the checker will not do

It will not call you, store a password, or send mail. There is no private inbox in this project.

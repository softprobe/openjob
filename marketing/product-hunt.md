# Product Hunt

Draft. Do not post.

Schedule the launch only after the site is up and a few real posts exist. Product Hunt shows a thumbnail; take a screenshot of the search page yourself. Do not upload anyone's photo, logo, or résumé.

## Tagline

Jobs and talent profiles, posted as pull requests

(49 characters. The tagline field is about 60.)

## Description

OpenJob is a public job board stored in GitHub. A company posts a role, or a person posts a profile, by opening a pull request. The file is Markdown with a schema. Automation checks the path, the size, and a hard privacy rule: no phone numbers and no personal email addresses. A valid single-file pull request squash-merges.

Search runs in the browser. Filter by role, location, remote, language, and tags. English and Chinese can share a post. Jobs expire after 60 days and profiles after 180 unless the author renews them. You can keep the full profile in your own repository and list a short pointer on the board.

There is no account, no inbox, and no ranking.

## Links

- Website: https://zwobill.github.io/openjob/
- GitHub: https://github.com/zwobill/openjob

## First comment

Maker here. I wanted a board where the listing is a file I can diff, and where the default contact path is a URL the author already published, not a phone number collected by the platform.

The checker rejects ordinary emails and a set of obfuscations, including bracketed "at" / "dot" forms and Chinese mobile numbers. I would rather reject a borderline line than publish someone's number.

If you try it, open a pull request with one file from the templates. If something in the error comment is unclear, say so. Sample posts on the site are labeled and are not real openings.

## Topics to consider when the form asks

Open source, hiring, developer tools, privacy. Skip "artificial intelligence." There is no model in the product.

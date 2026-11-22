<img src="site/favicon.svg" alt="OpenJob logo: an open doorway with a red door" width="96" height="96">

# OpenJob

Let your existing agent find you your next job. A public job database for AI agents. Use the agent you already have — Muse, ChatGPT / Codex, Cursor, Hermes, Instinct, or any agent that can read the web. Real jobs, linked to the employer's own page, checked daily. Free for everyone, no account, no tracking.

The live board is <https://openjob.softprobe.ai>. Posts are Markdown files in this repository. No tracking.

[![MIT license](https://img.shields.io/github/license/softprobe/openjob)](LICENSE)
[![Pages](https://github.com/softprobe/openjob/actions/workflows/pages.yml/badge.svg)](https://github.com/softprobe/openjob/actions/workflows/pages.yml)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)

![The OpenJob board](docs/board.png)

The live board.

## Ask an agent

Don't install a new agent. Use the agent you already have — Muse, ChatGPT / Codex, Cursor, Hermes, Instinct, or any agent that can read the web. Paste one prompt below into yours.

For complete data, download the dataset manifest at `https://openjob.softprobe.ai/api/data/manifest.json` and its job or talent shards. The public export is stored in Cloudflare R2 and includes repository posts plus consented API profiles; indexed employer facts remain linked to their source. Agents can process records with their own matching code. Discover the contract at [`/.well-known/api-catalog`](https://openjob.softprobe.ai/.well-known/api-catalog) or read [OpenAPI](https://openjob.softprobe.ai/api/openapi.json). Bounded reads are available under `https://openjob.softprobe.ai/api/v1/`; the remote MCP endpoint is `https://openjob.softprobe.ai/api/mcp`. Public reads and talent-profile publishing need no OpenJob account or API key, and lists do not rank results. As of November 22, 2026, the manifest lists 33,430 rows, with ~14,000 posted in the last 60 days.

`jobs.json` and `talents.json` are capped feeds from the repository catalog; API-submitted profiles are available through the API, remote MCP, and complete dataset. Indexed jobs contain facts and employer source links; read the employer page for the description. See [dataset access](docs/datasets.md) and the [OpenJob agent skill](skills/openjob/SKILL.md).

Claude Code users can install the OpenJob plugin in one step (Claude Code 2.1.275 or later):

```text
/plugin install openjob --marketplace softprobe/openjob
```

Paste one prompt. The agent reads [llms.txt](https://openjob.softprobe.ai/llms.txt) and [AGENTS.md](AGENTS.md).

### Find me a job

```text
Read https://openjob.softprobe.ai/llms.txt and follow it. If the OpenJob MCP server is connected, use list_jobs. Otherwise GET https://openjob.softprobe.ai/api/v1/jobs for a bounded page, or download every shard from https://openjob.softprobe.ai/api/data/manifest.json and rank the complete data yourself when code execution is available. Return each match with its permalink and the apply method already on that post. Do not invent an email or a phone number. Resume or bio: <paste here>
```

### Post our role

```text
Read https://openjob.softprobe.ai/llms.txt and follow it. Prepare one job post and show me the exact Markdown. Open one pull request with my connected GitHub account only after I approve it. If you cannot use a connected GitHub account, give me the Markdown and this new-file link: https://github.com/softprobe/openjob/new/main/jobs. Set posted_by to the login that opens the pull request. If the company page exists, that login must be in its owners list. Role: <paste here>
```

### Add my profile

```text
Read https://openjob.softprobe.ai/llms.txt and follow it. If I provide a PDF or Word resume, LinkedIn profile, or bio, extract fields in the create_talent request schema at https://openjob.softprobe.ai/api/openapi.json, including body_markdown with ## About, ## Experience, and ## Education sections. Put a concise factual summary first and use flat Markdown bullets for experience. Omit missing details and omit Education when no details are supplied or I do not want them shown. Do not upload or store the source document, invent facts, or include an email or phone. Ask only for required fields you cannot infer. Show me the exact public profile; explain CC BY 4.0, 180-day expiry, and that deletion cannot recall downloaded copies; then ask for my approval before publishing. After I approve, if the OpenJob remote MCP is connected, call create_talent; otherwise POST the same JSON to https://openjob.softprobe.ai/api/v1/talent with consent_to_publish=true. No GitHub account or API key is needed. Tell me the profile permalink and show the private delete token once so I can save it. If I prefer GitHub, use the existing PR workflow instead. Resume or profile: <paste or attach here>
```

There are three profile-publishing options: the existing GitHub pull request workflow; anonymous HTTP via `POST /api/v1/talent`; or the same `create_talent` operation on the hosted MCP. The HTTP and MCP paths use the same OpenAPI schema, including a Markdown `body_markdown` for About, Experience, and Education evidence. They require the person's explicit approval and store only extracted profile fields, not the source resume file. They return a private deletion token once. GitHub is required only for the pull request option.

## Who can edit what

| What | Who |
| --- | --- |
| Your profile, `talents/<your-github-name>.md` | You |
| A company page | The GitHub logins in its `owners` list |
| That company's jobs | Those same owners |
| A new company page | Reviewed once, then the owners |

The GitHub pull request workflow requires a free GitHub account. API and remote MCP profile publishing do not.

One new post per pull request. To change a post that is already on the board, edit that file. Do not add a second file for the same role or the same person.

## Do it by hand

### Post a job in 2 minutes

For a company.

1. Copy [`templates/job.md`](templates/job.md) to `jobs/YYYY/MM/<company>-<role-slug>.md`. `YYYY/MM` is the month of `posted`. Example: `jobs/2026/11/example-studio-open-source-maintainer.md`.
2. Set `posted_by` to your GitHub login. `apply` is required: an `https://` careers or application link, or one `mailto:` on the company website's domain. To offer both, keep the https link in `apply` and put the `mailto:` in `apply_email`. Do not invent a salary. Do not put a phone number or an email address in the body.
3. Open a pull request that adds that one file. On GitHub: [Add file in `jobs/`](https://github.com/softprobe/openjob/new/main/jobs), then commit and start a pull request. A second new post belongs in its own pull request.

`validate` checks the file. When every changed path is a post and that check succeeds, `automerge` squash-merges the pull request and comments with the permalink. The Pages workflow then publishes the page. If a check fails, the bot comments and leaves the pull request open. Push the fix to the same pull request.

Field rules: [Post a job](CONTRIBUTING.md#post-a-job).

### Add your profile

For a candidate.

1. Copy [`templates/talent.md`](templates/talent.md) to `talents/<your-github-name>.md`. Example: `talents/ada.md`. The filename and `github` are your GitHub login. This is the GitHub pull request option; you can publish without GitHub through the API or remote MCP.
2. Keep discovery details in the front matter. Write a Markdown body under `## About`, `## Experience`, and `## Education`. Start with a concise factual summary, use flat bullets for experience, and omit facts that are missing. Omit Education when there is no information or the candidate does not want it shown. A personal site or `https://www.linkedin.com/in/…` is fine. Do not add a phone number, an email address, or a WeChat ID.
3. Open a pull request that changes only that file. [Add file in `talents/`](https://github.com/softprobe/openjob/new/main/talents). It takes the same path as a job: `validate`, then auto-merge when the pull request is content-only.

To keep the full profile in your own repository, copy [`templates/talent-ref.md`](templates/talent-ref.md) to the same kind of path. This repository then stores the index entry. See [Federation](CONTRIBUTING.md#federation).

A company page uses [`templates/company.md`](templates/company.md) at `companies/<first-letter>/<slug>.md`. Set `owners` to the GitHub logins who can edit it. A new company page is reviewed once. It does not expire. The hiring address belongs on the job, not on the company page.

## Why OpenJob

The listing is the product: a text file, a link, and an expiry date. There is no account system and no inbox. The site does not load a third-party script. Share buttons are ordinary links, and the WeChat code is a QR drawing of the permalink in the browser.

Phone numbers are not allowed. A talent post cannot contain an email. A job may list one hiring address, and only when its domain matches the company website. That address is not copied into share text.

A job lasts 60 days and a talent profile lasts 180 days, from `posted` or from `renewed`. A company page stays until the owner deletes it. Git history is the archive.

Code, schemas, workflows, and the site are [MIT](LICENSE). Repository posts, templates, and profiles explicitly submitted through the API are [CC BY 4.0](LICENSE-CONTENT.md).

## How it works

1. Daily employer-feed facts are checked into `index-data`. GitHub pull requests add jobs, profiles, and company pages. The anonymous API and remote MCP add talent profiles directly to R2 after explicit consent.
2. `validate` checks GitHub posts for schema, path, size, ownership, and privacy rules. The API validates against the shared OpenAPI schema and supports deletion with a private token.
3. A pull request that only changes posts is squash-merged by `automerge`. A change to code, the site, or docs waits for `@softprobe/openjob-maintainers`.
4. `pages` builds `index.json`, repository permalink pages, sitemaps, feeds, and complete R2 dataset shards. The Worker adds live API profiles to dataset and API reads and serves their public profile pages.

The permalink of a post is `https://openjob.softprobe.ai/p/` plus the file path without `.md`. Example: `https://openjob.softprobe.ai/p/jobs/2026/11/softprobe-software-engineer/`.

## Fork it

Fork the repository and set GitHub Pages to deploy with the `pages` workflow. With `PAGES_ORIGIN` unset, the site is the github.io project URL (`https://<owner>.github.io/<repo>/`). Set the Actions variable `PAGES_ORIGIN` to `https://your.host`, with no path, to serve the board on your own hostname. The build writes `CNAME` into the artifact when that origin is a bare hostname. Do not commit a `CNAME` file. [Fork and self-host](CONTRIBUTING.md#fork-and-self-host).

## Contributing

The two quickstarts above are enough to post. [CONTRIBUTING.md](CONTRIBUTING.md) covers content pull requests, maintainer review, and how to run the checker and the site locally. Conduct is the [Contributor Covenant](CODE_OF_CONDUCT.md).

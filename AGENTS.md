# OpenJob agent instructions

OpenJob is a job board stored as Markdown in [github.com/softprobe/openjob](https://github.com/softprobe/openjob). A pull request publishes a job, a talent profile, or a company page. The live board is <https://openjob.softprobe.ai>. There are no accounts. The site does not take applications itself. Readers follow the link or the hiring address on the post.

Read the schema for the kind you are writing before you open the pull request:

- <https://openjob.softprobe.ai/schema/job.json>
- <https://openjob.softprobe.ai/schema/talent.json>
- <https://openjob.softprobe.ai/schema/company.json>

Templates, which the schemas match: [`templates/job.md`](templates/job.md), [`templates/talent.md`](templates/talent.md), [`templates/company.md`](templates/company.md), [`templates/talent-ref.md`](templates/talent-ref.md).

## Search the board

To find work, read <https://openjob.softprobe.ai/llms.txt> and GET <https://openjob.softprobe.ai/index.json>. Jobs are also in <https://openjob.softprobe.ai/jobs.json>. Profiles are in <https://openjob.softprobe.ai/talents.json>. Filter on `kind`, `tags`, `location`, `remote`, `languages`, `open_to`, and `employment_type`. Read a post at its permalink and at `index.md` beside that page.

Rank live jobs against a resume or bio. Return each match with its permalink and the apply method already on that post. Apply with the job's https link or the hiring address. A link to this repository's README or profile guide is not an application. Do not invent an email or a phone number.

To publish a profile from a resume, follow <https://openjob.softprobe.ai/schema/talent.json> and open one pull request under `talents/`. The profile has no email and no phone. Contact is the GitHub login, plus optional `website` and `linkedin`. Adding a profile is separate from applying.

## Pull request rules

Add one new post per pull request. The file must be UTF-8 Markdown (`.md`) under `jobs/`, `talents/`, or `companies/`, with YAML front matter between `---` lines, and a body of at least 40 characters. The file must be 10 KB or smaller. At most 12 links.

A pull request that only adds or edits the author's own post under those folders is squash-merged after `validate` and `trusted-validate` pass. The author is the GitHub login that opens the pull request. `posted_by` (job or company) or `github` (talent) must be that login.

Anything else needs approval from `@softprobe/openjob-maintainers` and does not auto-merge: a second new post, a file outside those folders, or a post owned by someone else.

To update a post, edit the existing file in a new pull request. Do not add a second file. Keep `posted` unchanged. Set `renewed` to the day you open the pull request when you want to extend the lifetime. The checker rejects a new job whose `company` and `title` already exist, and a new talent file whose `github` login already has a profile.

If the checker fails, the bot comment lists every fix. Apply those lines and push to the same branch.

## Privacy

Do not put a phone number anywhere in the file. Do not put a personal email, a WeChat ID, or a WhatsApp or Telegram handle in the file.

A talent post cannot contain an email at all. Contact is the GitHub pull request, plus optional `website` and `linkedin` (`https://www.linkedin.com/in/…`).

A job may include one hiring address, and only when its domain matches the company website:

- `apply: mailto:jobs@company.example` when email is the only method
- `apply` is an `https://` careers or application link, and `apply_email: mailto:jobs@company.example` when you also want email

Do not set both fields to `mailto:`. Do not copy the address into the body. A company page has no hiring address. Use `website`, `careers`, and an optional `logo` that is already hosted at an `https://` URL. Do not commit the image.

`example.com`, `example.org`, `example.net`, and `example.edu` are accepted in documentation. A real post uses the real company domain.

## Shared fields

- `remote`: `true` or `remote`, `false` or `onsite`, or `hybrid`.
- `languages`: one to four of `en`, `zh`, `ja`, `ko`, `es`, `fr`, `de`, `pt`, `ru`.
- `tags`: up to eight lowercase slugs (`reliability`, not `Site Reliability`).
- `posted`: `YYYY-MM-DD`, within the last 45 days, and not more than two days in the future. Use the day you open the pull request.
- Quote YAML values that would otherwise become booleans, such as a title of `yes`.

A job lasts 60 days from `posted` or `renewed`. A talent profile lasts 180 days. A company page does not expire. You may set `expires` sooner on a job or talent post. You may not set it later than the cap.

## Job

Path: `jobs/YYYY/MM/<company>-<role-slug>.md`. `YYYY/MM` is the `posted` month. `<company>` and `<role-slug>` are the `company` and `role_slug` fields. New file: <https://github.com/softprobe/openjob/new/main/jobs>.

Required front matter: `kind` (`job`), `title` (4–120 characters), `company` (slug), `company_name` (1–80), `role_slug` (slug), `location` (1–80), `remote`, `languages`, `tags`, `apply`, `posted`, `posted_by`.

Optional: `apply_email`, `website` (required for a hiring address when the company page does not exist yet), `compensation` (a short note, not a made-up number), `employment_type` (`FULL_TIME`, `PART_TIME`, `CONTRACTOR`, `TEMPORARY`, `INTERN`, `VOLUNTEER`, `PER_DIEM`, `OTHER`, or a list), `salary` (`min`, optional `max` at least `min`, ISO 4217 `currency`, `unit` of `HOUR`, `DAY`, `WEEK`, `MONTH`, or `YEAR`), `locations` (`city`, `region`, ISO 3166-1 alpha-2 `country`). Leave `salary` out unless the number is real. `location` is still required when `locations` is set.

```yaml
---
kind: job
title: Site reliability engineer
company: northwind
company_name: Northwind
role_slug: site-reliability-engineer
location: Berlin
remote: hybrid
languages: [en]
tags: [reliability, kubernetes]
apply: https://example.com/jobs/site-reliability-engineer
employment_type: FULL_TIME
locations:
  - city: Berlin
    country: DE
posted: 2026-11-14
posted_by: ada
---

Northwind is hiring a site reliability engineer in Berlin. The work is keeping the production platform healthy: incidents, capacity, and the path from commit to deploy. Hybrid, with the team in Berlin. Apply at the careers link in the front matter.
```

Replace `ada` with the pull request author. Replace `posted` with the day you open the pull request. Replace Northwind, the city, and the apply link with the real ones.

## Talent profile

Path: `talents/<first-letter>/<github-login>.md`, lowercase. The letter is the first character of the login. `github` is that same login. New file: <https://github.com/softprobe/openjob/new/main/talents>.

Required: `kind` (`talent`), `name`, `github`, `headline` (4–140), `location`, `remote`, `languages`, `tags`, `open_to`, `posted`.

`open_to` is one to four of `full-time`, `part-time`, `contract`, `internship`.

Optional: `website`, `linkedin`. No email field.

To keep the long profile in your own repo, use `kind: talent-ref` and `profile_url: https://github.com/<login>/openjob-profile` at the same path. See [`templates/talent-ref.md`](templates/talent-ref.md) and <https://openjob.softprobe.ai/schema/talent-ref.json>.

```yaml
---
kind: talent
name: Ada Lovelace
github: ada
headline: Site reliability engineer open to contract work
location: London
remote: true
languages: [en]
tags: [reliability, kubernetes]
open_to: [contract]
website: https://example.com
posted: 2026-11-14
---

Ada Lovelace is a site reliability engineer based in London and open to contract work. The work she wants is production platforms, incidents, and the path from commit to deploy. The personal site is the website in the front matter.
```

Replace `ada` with the pull request author, and replace the name, city, and site with the real ones. `posted` is the day you open the pull request.

## Company

Path: `companies/<first-letter>/<slug>.md`. The letter is the first character of `slug`. New file: <https://github.com/softprobe/openjob/new/main/companies>.

Required: `kind` (`company`), `slug`, `name`, `website`, `location`, `tags`, `posted`, `posted_by`.

Optional: `careers`, `logo` (https URL of an image hosted outside this repository), `remote`, `languages`. No email. A job for this company is a later pull request, not a second file in this one.

```yaml
---
kind: company
slug: northwind
name: Northwind
website: https://example.com
careers: https://example.com/jobs
location: Berlin
tags: [reliability]
languages: [en]
posted: 2026-11-14
posted_by: ada
---

Northwind builds a production platform and hires through the careers page linked above. This page names the company and the site. Open roles are separate job files.
```

## If you cannot open the pull request

Print the finished Markdown file and tell the person to paste it at the new-file URL for that folder, then commit and open the pull request. Do not invent a salary. Do not add a phone number or a personal email to make the file look complete.

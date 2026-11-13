# Contributing

Posts are pull requests. One post per pull request. The checker squash-merges it when the file is valid and the pull request does not touch anything else.

English is the normative set of rules. A short Chinese walkthrough is at the bottom.

## Privacy

Do not publish a phone number or a personal email address. Not in the post, not in the pull request body, not in an issue.

Use one of these instead:

- a LinkedIn profile URL (`https://www.linkedin.com/in/…`)
- the GitHub profile implied by your login
- a personal site (`https://…`)
- a company careers or apply link

The checker rejects addresses that use `@`, and disguises such as `name [at] domain [dot] com`, `(at)` / `(dot)`, fullwidth `＠` and `．`, HTML entities, and `%40`. It rejects phone numbers in international form, Chinese mobiles (including `+86` and numbers written with Chinese numerals such as `一三八…`), landlines written with a separator, and `tel:` links.

It allows only two narrow cases, so the docs and tests can talk about the format:

- email domains `example.com`, `example.org`, `example.net`, and `example.edu`
- fictional NANP numbers whose exchange is `555` and whose line starts with `01`, such as `(415) 555-0100`, when they are formatted as phone numbers

A bare number such as `13800138000` is rejected. People paste it as a placeholder, and it looks like a real mobile.

There is no `email` or `phone` field. `additionalProperties` is false. WeChat IDs, WhatsApp links, and Telegram handles are not allowed contact channels either. The checker may miss a handle that is not a phone number; maintainers remove those on report.

## Post a job

1. Copy `templates/job.md`.
2. Save it as `jobs/YYYY/MM/<company>-<role-slug>.md`. `YYYY/MM` is the `posted` month. Example: `jobs/2026/11/example-studio-open-source-maintainer.md`.
3. Set `posted_by` to your GitHub login. That login has to be the pull request author.
4. Set `apply` to an `https://` careers or application link. No shorteners (`bit.ly`, `t.co`, `t.cn`, `lnkd.in`, and similar).
5. Open a pull request that changes only that file.

`remote` is `true`, `false`, or `hybrid`. `languages` use the codes in the schema (`en`, `zh`, `ja`, `ko`, `es`, `fr`, `de`, `pt`, `ru`). Tags are lowercase slugs. Quote YAML values that are `yes`, `no`, `on`, or `off`.

A job lasts 60 days from `posted`, or from `renewed` if you set it. You may set `expires` sooner. You may not set it later than that cap.

## Post a talent profile

Save `templates/talent.md` as `talents/<first-letter>/<github-username>.md`, lowercase. Example: `talents/z/zwobill.md`.

`github` must match the filename and the pull request author. A profile lasts 180 days unless you renew it.

`open_to` is one or more of `full-time`, `part-time`, `contract`, `internship`.

## Post a company

Save `templates/company.md` as `companies/<first-letter>/<slug>.md`. Company pages do not expire. The account in `posted_by` owns later edits. Jobs are separate files, so one pull request cannot add both.

## Federation

You can keep the canonical profile in your own repository and store only an index entry here.

1. Create a public repository named `openjob-profile` on your account.
2. Add `profile.md` there. Use the same front matter as `schema/talent.schema.json`.
3. Open a pull request here that adds `talents/<letter>/<handle>.md` from `templates/talent-ref.md`.

`profile_url` must be `https://github.com/<your-login>/openjob-profile` or a file under that repository on `raw.githubusercontent.com`. The login in the URL, the `github` field, the filename, and the pull request author all have to match. The entry is searchable. The site links out. It does not fetch the other repository at browse time.

The entry expires like any other talent post (180 days, or sooner if you set `expires`). Renew it with a pull request that sets `renewed`, or delete it.

## Expiry and the archive

| Kind | Default lifetime | Cap |
| --- | --- | --- |
| Job | 60 days from `posted` or `renewed` | 60 days |
| Talent and talent-ref | 180 days from `posted` or `renewed` | 180 days |
| Company | does not expire | — |
| `example: true` | kept until a maintainer deletes it | samples only |

`posted` never changes after the file is merged. To renew, set `renewed` to the day you open the pull request and leave `posted` alone. A new post's `posted` date has to be within the last 45 days (and not more than two days in the future).

**Git history is the archive.** A scheduled workflow deletes expired files from the live tree and opens a pull request listing them. Copies under `archive/` would grow the repository forever and crowd directories, so they are not kept. To restore a post, take the file from the parent of the expiry commit, set `renewed`, keep the original `posted`, and open a new pull request. If the `posted` month and the path disagree, fix the path in that same pull request only when you are the owner; a path change is a delete plus an add and counts as one post.

Sample posts (`example: true`) are not removed by the expiry workflow. They are not on the live board. The three original samples (a job, a talent profile, and a company page) are fixtures under `tests/fixtures/samples/`. The tests copy them into a temporary tree. `templates/` stays the files a contributor copies. The site build indexes `jobs/`, `talents/`, and `companies/` only, so nothing under `tests/` or `templates/` is published.

When a letter directory approaches about 800 files, maintainers should add a second shard (`talents/a/b/…`) in a deliberate migration. Version 1 is one letter, one directory, which is the layout contributors should use now. Jobs are already sharded by month.

## What the check enforces

On a pull request the `validate` workflow runs the unit tests and `python -m validator check-pr`. It comments on failure with the code and a fix. The post checker still runs when the unit tests fail, so the comment includes that fix. The pull request stays open.

- JSON Schema for the `kind`
- path and filename
- UTF-8 text, 10 KB maximum, no images, PDFs, or other binaries
- privacy, as above
- one post per pull request (a rename is one delete and one add of the same kind and owner)
- the author owns the file, on add, edit, and delete
- link count (12), `https` on the structured links, no shorteners, no `javascript:` URLs
- files over 1 MB are rejected even outside the post folders

If the pull request also edits workflows, docs, or the site, the post checks can still pass, but auto-merge stays off. `@zwobill` merges those.

After this workflow file is on `main`, `.github/workflows/automerge.yml` repeats the check from the base branch (so a pull request cannot swap in a weaker checker). A single-post pull request squash-merges itself when that trusted check accepts it and the `validate` check succeeded for the same head commit. The workflow then comments with the permalink and the share links. A deletion has no permalink to share, so that comment is skipped.

Posts are not reviewed by hand. The checker is the gate. If `validate` fails, is still running when the wait ends, is missing, or belongs to a different commit, auto-merge comments and leaves the pull request open. Push a fix and both checks run again. Edits to workflows, the checker, the site, or the docs are not auto-merged; a maintainer merges those.

Pull requests #2 and #3 merged while `validate` was red, because auto-merge did not look at that check and branch protection was off. The merge job now waits for the `validate` check on the pull request head SHA and runs `python -m validator merge-gate` before it calls the merge API. The squash is pinned to that SHA. The gate exits 0 only when the conclusion is `success` and the check SHA is that head SHA. Any other conclusion, a missing check, or a different SHA exits 1, the job comments, and the squash step does not run.

`tests/test_gate.py` is the automated proof. The same command is the manual check:

```bash
python -m validator merge-gate \
  --automerge true \
  --validate-conclusion failure \
  --validate-sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --head-sha aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

That exits 1 and prints the “left this pull request open” comment. Repeat it with `--validate-conclusion success` and the same SHA twice: it exits 0. A green Validate on a different SHA still exits 1. In the workflow, exit 0 is what allows the squash; exit 1 stops the job first.

The expiry workflow opens its own pull request as `github-actions[bot]`. Pull requests created with `GITHUB_TOKEN` do not trigger other workflows, so that pull request will not receive the `validate` check. Merge it by hand, or allow the Actions bot to bypass branch protection. The bot may only delete posts that are already expired.

## Share your post

The permalink of a merged post is:

`https://softprobe.github.io/openjob/p/` plus the file path without `.md`, with a trailing slash.

The Pages workflow writes that HTML file when it builds the site. The board hash `#` plus the same path (no `.md`) scrolls to the entry. Share buttons and unfurls use the permalink, because that page carries the Open Graph and Twitter card tags.

| Kind | Prefilled text |
| --- | --- |
| Job | role, company, and location |
| Talent and talent-ref | headline |
| Company | name and location |

The text is built only from those fields. `apply`, `website`, `linkedin`, `careers`, `profile_url`, phone numbers, and email addresses are not copied into it, including `example.com` addresses and fictional `555-01xx` numbers. If one of those fields itself contains a phone number or an email address, the share text is replaced with `OpenJob` and the permalink is still shared.

LinkedIn and Facebook do not accept a prefilled body. Their buttons open the network's share page with the permalink, and the card uses the page title and description. Hacker News receives the same text, cut at 80 characters. Copy link copies the permalink. WeChat has no public share URL. The QR code on the page is the permalink, drawn by `site/vendor/qrcode.js` in the browser.

The auto-merge comment repeats these links. It does not repeat the apply link.

## Local commands

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m validator check-tree --root .
python -m validator build-index --root . --out site/index.json --pages site
python -m validator expire --root . --today 2026-11-13
```

## 中文步骤

1. 不要写电话或个人邮箱，包括 `名字 [at] 域名 [dot] com`、全角 `＠`、以及 `一三八……` 这种中文数字。联系方式只用 LinkedIn、GitHub、个人网站，或公司的招聘/申请链接。
2. 职位文件放在 `jobs/年/月/公司-职位.md`，`posted_by` 必须是你的 GitHub 用户名。默认 60 天后过期。
3. 人才档案放在 `talents/首字母/用户名.md`，`github` 必须是你自己。默认 180 天。也可以在自己的 `openjob-profile` 仓库放全文，这里只提交 `kind: talent-ref` 的索引。
4. 公司页放在 `companies/首字母/slug.md`，不过期。
5. 一个 Pull Request 只改一篇帖子。检查通过后会 squash 合并。改工作流或文档需要维护者合并。
6. 续期时不要改 `posted`，把 `renewed` 设成提交当天。过期文件会从目录删除，Git 历史就是归档，需要时从历史恢复再续期。
7. 合并后的永久链接是 `https://softprobe.github.io/openjob/p/` 加上去掉 `.md` 的路径。分享文案只有职位、公司和地点，或 headline，或公司名和地点，不含电话、邮箱和申请链接。自动合并的评论里会带上这些分享链接。

# Contributing

Posts are pull requests. A pull request may change any number of posts. The checker squash-merges it when every changed path is a post file under `jobs/`, `talents/`, or `companies/` and each file is valid. Anything else needs approval from the Softprobe team.

English is the normative set of rules. A short Chinese walkthrough is at the bottom.

## Privacy

Do not publish a phone number. Do not publish a personal email address. Not in the post, not in the pull request body, not in an issue.

Talent posts cannot contain an email at all. A job may contain one employer hiring address, and only in `apply` or `apply_email`:

- `apply: mailto:jobs@company.example` when that is the only application method
- `apply_email: mailto:jobs@company.example` when `apply` is an `https://` careers or application link

The domain has to match the company website. A leading `www.` on the website host is ignored, and a subdomain of that host matches. The company page's `website` is the source when `companies/<letter>/<company>.md` exists. Otherwise the job's own `website` is the source. `hr@gmail.com` does not match `softprobe.ai`. The same address copied into the job body is still rejected. Phone numbers are rejected even when the hiring address is allowed.

The site may render that address as an Apply by email button. Share text does not include it.

Use one of these for every other contact:

- a LinkedIn profile URL (`https://www.linkedin.com/in/…`)
- the GitHub profile implied by your login
- a personal site (`https://…`)
- a company careers or apply link

The checker rejects addresses that use `@`, and disguises such as `name [at] domain [dot] com`, `(at)` / `(dot)`, fullwidth `＠` and `．`, HTML entities, and `%40`. It rejects phone numbers in international form, Chinese mobiles (including `+86` and numbers written with Chinese numerals such as `一三八…`), landlines written with a separator, and `tel:` links.

It allows only two narrow cases besides that one hiring address, so the docs and tests can talk about the format:

- email domains `example.com`, `example.org`, `example.net`, and `example.edu`
- fictional NANP numbers whose exchange is `555` and whose line starts with `01`, such as `(415) 555-0100`, when they are formatted as phone numbers

A bare number such as `13800138000` is rejected. People paste it as a placeholder, and it looks like a real mobile.

There is no `phone` field, and no general `email` field. `additionalProperties` is false. WeChat IDs, WhatsApp links, and Telegram handles are not allowed contact channels either. The checker may miss a handle that is not a phone number; maintainers remove those on report.

## Post a job

1. Copy `templates/job.md`.
2. Save it as `jobs/YYYY/MM/<company>-<role-slug>.md`. `YYYY/MM` is the `posted` month. Example: `jobs/2026/11/example-studio-open-source-maintainer.md`.
3. Set `posted_by` to your GitHub login. That login has to be the pull request author.
4. Set `apply` to an `https://` careers or application link, or to `mailto:jobs@company.example` for a hiring address on the company domain. To keep the https link and also offer email, leave `apply` as the https link and set `apply_email` to the `mailto:` address. No shorteners (`bit.ly`, `t.co`, `t.cn`, `lnkd.in`, and similar).
5. Open a pull request that changes only post files. Another post may be in the same pull request.

`remote` is `true`, `false`, or `hybrid`. `languages` use the codes in the schema (`en`, `zh`, `ja`, `ko`, `es`, `fr`, `de`, `pt`, `ru`). Tags are lowercase slugs. Quote YAML values that are `yes`, `no`, `on`, or `off`.

A job lasts 60 days from `posted`, or from `renewed` if you set it. You may set `expires` sooner. You may not set it later than that cap.

## Post a talent profile

Save `templates/talent.md` as `talents/<first-letter>/<github-username>.md`, lowercase. Example: `talents/z/zwobill.md`.

`github` must match the filename and the pull request author. A profile lasts 180 days unless you renew it.

`open_to` is one or more of `full-time`, `part-time`, `contract`, `internship`.

## Post a company

Save `templates/company.md` as `companies/<first-letter>/<slug>.md`. Company pages do not expire. The account in `posted_by` owns later edits. A job for that company is a separate file. Both files may be in one pull request when you own each of them.

An optional `logo` is an `https://` URL of an image already hosted somewhere else. Do not commit the image. The board and the permalink page render it. Share text does not include the URL. A company page still cannot contain an email address. The hiring address belongs on the job.

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

**Git history is the archive.** A scheduled workflow deletes expired files from the live tree and opens a pull request listing them. Copies under `archive/` would grow the repository forever and crowd directories, so they are not kept. To restore a post, take the file from the parent of the expiry commit, set `renewed`, keep the original `posted`, and open a new pull request. If the `posted` month and the path disagree, fix the path in a pull request you own. A path change is a delete plus an add, and ownership is checked on each file.

Sample posts (`example: true`) are not removed by the workflow. They exist so the first page is not empty. A maintainer can delete them once real posts exist.

When a letter directory approaches about 800 files, maintainers should add a second shard (`talents/a/b/…`) in a deliberate migration. Version 1 is one letter, one directory, which is the layout contributors should use now. Jobs are already sharded by month.

## What the check enforces

On a pull request the `validate` workflow runs the unit tests and `python -m validator check-pr`. It comments on failure with the code and a fix. The post checker still runs when the unit tests fail, so the comment includes that fix. The pull request stays open.

- JSON Schema for the `kind`
- path and filename
- UTF-8 text, 10 KB maximum, no images, PDFs, or other binaries
- privacy, as above
- every changed path is a post file under `jobs/`, `talents/`, or `companies/` (several posts are fine; a rename is a delete plus an add)
- the author owns each file, on add, edit, and delete
- link count (12), `https` on the structured links, no shorteners, no `javascript:` URLs
- files over 1 MB are rejected even outside the post folders

If the pull request also edits workflows, docs, or the site, the post checks can still pass, but auto-merge stays off. The bot comment says the Softprobe team (`@softprobe/openjob-maintainers`) has to approve it. `@zwobill` can still do maintainer-only actions in the checker, such as sample posts.

After this workflow file is on `main`, `.github/workflows/automerge.yml` repeats the check from the base branch (so a pull request cannot swap in a weaker checker). A pull request that only changes post files squash-merges itself when that trusted check accepts every file and the `validate` check succeeded for the same head commit. The workflow then comments with the permalink and the share links for each added or edited post. A deletion has no permalink to share, so that comment is skipped.

Posts are not reviewed by hand. The checker is the gate. If `validate` fails, is still running when the wait ends, is missing, or belongs to a different commit, auto-merge comments and leaves the pull request open. Push a fix and both checks run again. Edits to workflows, the checker, the site, or the docs are not auto-merged; the Softprobe team merges those.

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

The text is built only from those fields. `apply`, `apply_email`, `website`, `logo`, `linkedin`, `careers`, `profile_url`, phone numbers, and email addresses are not copied into it, including `example.com` addresses, a matching hiring address, and fictional `555-01xx` numbers. If one of those fields itself contains a phone number or an email address, the share text is replaced with `OpenJob` and the permalink is still shared. The permalink page may show an Apply by email button. That button is not part of the share text.

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

1. 不要写电话。人才帖不能写邮箱。职位只能在 `apply` 或 `apply_email` 里写一个 `mailto:jobs@公司域名`，域名必须和公司网站一致（公司页存在时以公司页的 `website` 为准，忽略 `www.`）。正文里的邮箱会被拒绝。其他联系方式只用 LinkedIn、GitHub、个人网站，或公司的招聘/申请链接。`名字 [at] 域名 [dot] com`、全角 `＠`、以及 `一三八……` 这种中文数字同样会被拒绝。
2. 职位文件放在 `jobs/年/月/公司-职位.md`，`posted_by` 必须是你的 GitHub 用户名。默认 60 天后过期。
3. 人才档案放在 `talents/首字母/用户名.md`，`github` 必须是你自己。默认 180 天。也可以在自己的 `openjob-profile` 仓库放全文，这里只提交 `kind: talent-ref` 的索引。
4. 公司页放在 `companies/首字母/slug.md`，不过期。
5. 一个 Pull Request 可以改多篇帖子，但每个文件都要在 `jobs/`、`talents/` 或 `companies/` 里。检查通过后会 squash 合并。改工作流或文档需要 Softprobe 团队批准。
6. 续期时不要改 `posted`，把 `renewed` 设成提交当天。过期文件会从目录删除，Git 历史就是归档，需要时从历史恢复再续期。
7. 合并后的永久链接是 `https://softprobe.github.io/openjob/p/` 加上去掉 `.md` 的路径。分享文案只有职位、公司和地点，或 headline，或公司名和地点，不含电话、邮箱和申请链接。页面可以显示「邮件申请」按钮，那个地址不在分享文案里。自动合并的评论里会带上每一篇新增或修改的帖子的分享链接。

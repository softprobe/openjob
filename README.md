# OpenJob

OpenJob is an open, privacy-first job board on GitHub where anyone posts jobs and resumes as Markdown pull requests, auto-validated and auto-merged, with no phone numbers and no personal email except one company hiring address on a job.

The live board is <https://softprobe.github.io/openjob/>.

[![Validate](https://github.com/softprobe/openjob/actions/workflows/validate.yml/badge.svg)](https://github.com/softprobe/openjob/actions/workflows/validate.yml)

[中文](#中文)

## Quick start

Posts only. Copy a template into a new post and leave `templates/` unchanged. A pull request may change any number of posts. Every changed file has to stay under `jobs/`, `talents/`, or `companies/`. You can do every step in the GitHub web UI (**Add file → Create new file**, or edit on github.com). If you cannot push here, GitHub asks you to fork the repository and open the pull request from the fork.

**Find jobs and talent:** search <https://softprobe.github.io/openjob/>. The live board lists `jobs/`, `talents/`, and `companies/` only.

### Post a job

1. Copy [`templates/job.md`](templates/job.md).
2. Create the file with [Add file in `jobs/`](https://github.com/softprobe/openjob/new/main/jobs). The file name field is already relative to `jobs/`. Enter `YYYY/MM/<company>-<role-slug>.md`. `YYYY/MM` is the month of `posted`. The filename is the `company` slug, a hyphen, and `role_slug`. Example: `2026/11/example-studio-open-source-maintainer.md`.
3. Replace the placeholders: `title`, `company`, `company_name`, `role_slug`, `location`, `remote` (`true`, `false`, or `hybrid`), `languages`, `tags`, `posted` (`YYYY-MM-DD`), and `posted_by` (your GitHub login). `apply` is required. Set it to an `https://` link for an ATS, careers page, or job posting, or to `mailto:jobs@company.example` on the company website's domain. To offer both, keep the https link in `apply` and set `apply_email` to that `mailto:`. Do not set both to `mailto:`. Personal and other-domain addresses are rejected, and so are phone numbers. Do not put an email in the body. Examples: [Application methods](CONTRIBUTING.md#application-methods).
4. Open a pull request that changes only post files. On that new-file page, commit and start a pull request. The edit stays in the browser. Another post can be a second file in the same pull request.
5. The validator runs on the pull request and auto-merges it if the file passes. Share `https://softprobe.github.io/openjob/p/jobs/YYYY/MM/<company>-<role-slug>/` with the share buttons on that page. The merge comment links the same URL.

### Post your resume (talent)

1. Copy [`templates/talent.md`](templates/talent.md).
2. Create the file with [Add file in `talents/`](https://github.com/softprobe/openjob/new/main/talents). The file name field is already relative to `talents/`. Enter `<first-letter>/<github-username>.md`, lowercase. The letter is the first character of your GitHub login, and the filename is that login. Example: `z/zwobill.md` is `talents/z/zwobill.md`.
3. Set `github` to that same login. It has to match the filename and the pull request author. Fill in `name`, `headline`, `location`, `remote`, `languages`, `tags`, `open_to` (`full-time`, `part-time`, `contract`, or `internship`), and `posted`. Optional: `website`, or `linkedin` (`https://www.linkedin.com/in/…`). No phone number, email address, or WeChat ID.
4. Open a pull request that changes only post files, entirely in the GitHub web UI (**Add file**, then commit and start a pull request).
5. The validator runs and auto-merges the pull request if the file passes. Share `https://softprobe.github.io/openjob/p/talents/<letter>/<github-username>/` with the share buttons on that page.

To keep the full résumé in your own repository, copy [`templates/talent-ref.md`](templates/talent-ref.md) to the same kind of path. This repository stores the index entry. See [Federation](CONTRIBUTING.md#federation).

### Add a company page

1. Copy [`templates/company.md`](templates/company.md).
2. Create the file with [Add file in `companies/`](https://github.com/softprobe/openjob/new/main/companies). The file name field is already relative to `companies/`. Enter `<first-letter>/<slug>.md`. The letter is the first character of `slug`. Example: `s/softprobe.md` is `companies/s/softprobe.md`.
3. Fill in `slug`, `name`, `website`, `careers`, `location`, `tags`, `languages`, `posted`, and `posted_by` (your GitHub login). Use `https://` links. Optional `logo` is an `https://` image URL; do not commit the file. Do not put a recruiting phone number or a recruiting email on the page. The hiring address belongs on the job.
4. Open a pull request that changes only post files, entirely in the GitHub web UI. A job for that company can be another post file in the same pull request.
5. The validator runs and auto-merges the pull request if the file passes. Company pages stay until the owner deletes them. Share `https://softprobe.github.io/openjob/p/companies/<letter>/<slug>/` with the share buttons on that page.

If a check fails, the bot comments and leaves the pull request open. Fix the file and push to the same pull request. Lifetimes, the privacy rules, and the schemas are in the sections below and in [CONTRIBUTING.md](CONTRIBUTING.md).

## Post something

The board is the repository. Search is a static page. There is no account system and no inbox. This is a public alternative to LinkedIn and BOSS直聘 for people who want the listing itself to be the product: a text file, a link, and an expiry date. It does not try to be a social network.

**Privacy first.** Do not publish a phone number. Do not publish a personal email address. Not in a post, not in a pull request, and not in an issue. Talent posts cannot contain an email at all. A job may put one employer hiring address in `apply` (`mailto:jobs@company.example`) or in `apply_email`, and only when that domain matches the company website (`www.` is ignored). The address is not copied into share text. The site may show it as an Apply by email button. Every other email is rejected, including the job body and a mismatched domain such as gmail.com. Other contact goes through a LinkedIn URL, a GitHub profile, a personal site, or a company careers/apply link. The checker rejects ordinary addresses and common disguises (`name [at] domain`, fullwidth characters, HTML entities, `%40`, `+86` mobiles, and Chinese numerals). See [Contributing](CONTRIBUTING.md#privacy).

The live board is only `jobs/`, `talents/`, and `companies/`. Sample posts used to sit there so the first page was not empty. They now live under `tests/fixtures/samples/` and are not published. A file with `example: true` is a sample. It is not a real opening, a real résumé, or a real company. Files in `templates/` are starting points for a pull request. The site index does not read `tests/` or `templates/`.

| Kind | Path | Lifetime |
| --- | --- | --- |
| Job | `jobs/YYYY/MM/<company>-<role-slug>.md` | 60 days, then renew or it is removed |
| Talent | `talents/<first-letter>/<github-username>.md` | 180 days |
| Federated talent | same talent path, `kind: talent-ref` | 180 days; the full profile stays in your repo |
| Company | `companies/<first-letter>/<slug>.md` | kept until the owner deletes it |

Copy a file from `templates/`. A pull request may add, edit, or delete any number of posts. Set `posted_by` or `github` on each file to your GitHub login. The check squash-merges the pull request when every changed path is a post under `jobs/`, `talents/`, or `companies/` and each file is valid. Anything outside those directories waits for the Softprobe team (`@softprobe/openjob-maintainers`).

Posts are text, UTF-8, and at most 10 KB. Images, PDFs, and other binaries are rejected.

The click-through steps are in [Quick start](#quick-start). Field rules, the federation layout, and the renewal rules are in [CONTRIBUTING.md](CONTRIBUTING.md). Schemas are the JSON files in `schema/`.

## Share your post

Each job, talent profile, and company page has a permalink:

`https://softprobe.github.io/openjob/p/<path-without-.md>/`

Example: `https://softprobe.github.io/openjob/p/jobs/2026/11/softprobe-software-engineer/`

That page is static HTML. Its title and description are Open Graph and Twitter card tags, so a link unfurls as the public listing. The board also opens the same entry at `#<path-without-.md>`, for example `#jobs/2026/11/softprobe-software-engineer`.

The page has share buttons for LinkedIn, X, Reddit, Hacker News, Facebook, Telegram, WhatsApp, and Weibo. They are ordinary share-intent links. There is no SDK and no third-party script. Copy link copies the permalink. WeChat has no share URL; the page draws a QR code of the permalink in the browser with the MIT library in `site/vendor/`.

The prefilled text is the role, company, and location for a job, the headline for a talent profile, and the name and location for a company. It does not include an apply link, a profile URL, a phone number, or an email address. A permalink may show an Apply by email button. That address is not part of the share text. LinkedIn and Facebook take the permalink and read the title from the page. Hacker News uses the same text, shortened to 80 characters.

After auto-merge, the bot comments on the pull request with that permalink and the same links. The comment is part of `automerge.yml`, so it starts once that workflow is on `main`. The permalink itself goes live when the Pages workflow finishes.

## How it stays small

- Sharded paths, so a single directory does not collect every post. Jobs are grouped by month. Talent and company files are grouped by the first letter. If a letter directory approaches about 800 files, maintainers add a second level in a separate change.
- No binaries in posts.
- Jobs and talent posts expire. **Git history is the archive.** The scheduled workflow opens a pull request that deletes expired files. Restore one from that commit, set `renewed`, and send it again. Company pages are not auto-removed. A post marked `example: true` is kept too, but the live tree does not contain one. The samples are test fixtures.

## Federation

A profile can live in `<your-username>/openjob-profile`. This repository then holds a short index entry (`kind: talent-ref`) with the same path as a normal talent file. The search page lists it and links to your repository. It does not download the profile at browse time. The index entry still expires, so a stale pointer does not sit here forever.

`schema/talent-ref.schema.json` describes the entry. `schema/index.schema.json` describes the JSON file the site searches.

## What the automation does

| Workflow | When | Effect |
| --- | --- | --- |
| `validate` | every pull request | tests, schema, path, size, privacy, ownership, scope; comments on failure |
| `automerge` | pull requests after this file is on `main` | runs the trusted checker and its unit tests from `main`, then squash-merges a pull request whose changes are only post files once `validate` has succeeded for that same commit. Several posts are fine. A failed or missing check is commented and left open. Anything outside `jobs/`, `talents/`, and `companies/` stays for the Softprobe team |
| `expire` | daily, 03:17 UTC | opens a pull request that deletes expired posts |
| `pages` | push to `main` | builds `index.json` and the permalink pages, then deploys the site |

`validate` is the check on this pull request. `automerge` cannot run until that workflow exists on the default branch, because `pull_request_target` uses the workflow from `main`, not from the pull request. That is deliberate: a pull request must not be able to replace the checker and then merge itself.

## Repository settings the owner turns on

The workflows cannot flip these switches.

1. **Settings → Actions → General → Workflow permissions:** Read and write.
2. **Allow GitHub Actions to create and approve pull requests.** The expiry job needs this to open its pull request.
3. **Settings → General → Pull Requests:** Allow squash merging. Allow auto-merge.
4. **Branch protection or a ruleset on `main`:**
   - Require a pull request.
   - Require the status check `validate`. After `automerge.yml` has run once, also require `trusted-validate`.
   - Set required approving reviews to **0**.
   - Turn **on** "Require review from Code Owners". `CODEOWNERS` gives `*` to `@softprobe/openjob-maintainers`, then lists `/jobs/`, `/talents/`, and `/companies/` with no owner. A content-only pull request has nobody to request, so it needs no review. Every other change needs a team approval. `@zwobill` remains a maintainer in the checker.
   - Pull requests opened by `GITHUB_TOKEN` do not trigger other workflows. The expiry pull request will sit without `validate`. Merge it yourself, or let the GitHub Actions bot bypass the rule.
5. **Settings → Pages → Build and deployment → Source:** GitHub Actions. The site URL is `https://softprobe.github.io/openjob/`. Until this is on, the Pages workflow builds the site and then `deploy-pages` fails with HTTP 404, “Ensure GitHub Pages has been enabled.”
6. Optional: set the repository description, the homepage URL above, and topics such as `jobs`, `hiring`, and `privacy`.

GitHub also asks a maintainer to approve Actions the first time a new fork contributor opens a pull request. That click is manual.

## Layout

```
jobs/YYYY/MM/<company>-<role-slug>.md
talents/<letter>/<github-username>.md
companies/<letter>/<slug>.md
schema/          JSON Schema for each kind, plus the public index
templates/       starting files; not indexed
validator/       checker, index builder, expiry selection, share text
site/            static search page; permalink HTML is generated into site/p/
tests/fixtures/  privacy, path, size, binary, and sample posts; not indexed
```

`site/p/` is build output. It is not committed. Git history remains the archive for posts; the Pages site is rebuilt from the live tree.

Run the checker locally:

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m validator build-index --root . --out site/index.json --pages site
```

## Licenses

Code, schemas, workflows, and the site are [MIT](LICENSE). The QR code library in `site/vendor/` is also MIT, under its own copyright (`site/vendor/LICENSE-qrcode.txt`). Posts and templates are [CC BY 4.0](LICENSE-CONTENT.md). Say who wrote the post and link the file if you reuse it.

Abuse reports and the takedown path are in [SECURITY.md](SECURITY.md). Conduct is the [Contributor Covenant](CODE_OF_CONDUCT.md).

## 中文

[English](#openjob)

OpenJob 是一个放在 GitHub 上的开放、隐私优先的职位板：谁都可以用 Markdown Pull Request 发布职位和简历，自动校验并自动合并。不留电话。除了职位上一个公司域名的招聘邮箱，不留个人邮箱。

在线看板：<https://softprobe.github.io/openjob/>。

### 快速开始

只改帖子。把模板复制成新文件，不要在这个 Pull Request 里修改 `templates/`。一个 Pull Request 可以改多篇帖子，但每个改动都必须在 `jobs/`、`talents/` 或 `companies/` 里。全程可以在 GitHub 网页上完成（**Add file → Create new file**，或直接在 github.com 上编辑）。没有写权限时，GitHub 会让你先 Fork，再从 Fork 开 Pull Request。

**找职位和人才：** 在 <https://softprobe.github.io/openjob/> 搜索。在线看板只列出 `jobs/`、`talents/` 和 `companies/`。

#### 发布职位

1. 复制 [`templates/job.md`](templates/job.md)。
2. 用 [在 `jobs/` 里新建文件](https://github.com/softprobe/openjob/new/main/jobs) 创建帖子。文件名输入框已经相对于 `jobs/`。填 `YYYY/MM/<company>-<role-slug>.md`。`YYYY/MM` 是 `posted` 的年月，文件名是 `company`、连字符和 `role_slug`。例如 `2026/11/example-studio-open-source-maintainer.md`。
3. 替换占位符：`title`、`company`、`company_name`、`role_slug`、`location`、`remote`（`true`、`false` 或 `hybrid`）、`languages`、`tags`、`posted`（`YYYY-MM-DD`）、`posted_by`（你的 GitHub 登录名）。`apply` 必填：`https://` 指向 ATS、招聘页或职位链接，或公司域名上的 `mailto:jobs@公司域名`。两者都要时，`apply` 保持 https，`apply_email` 写这个 `mailto:`。不能两个都写成 `mailto:`。个人邮箱和其他域名会被拒绝，电话也会被拒绝。不要在正文里写邮箱。示例见 [申请方式](CONTRIBUTING.md#application-methods)。
4. 打开一个只改帖子文件的 Pull Request。在新建文件的页面上提交并创建 Pull Request，编辑留在浏览器里完成。同一请求里可以再加一篇帖子。
5. 校验会在 Pull Request 上运行，通过后自动合并。用页面上的分享按钮分享 `https://softprobe.github.io/openjob/p/jobs/YYYY/MM/<company>-<role-slug>/`。合并评论里也有这个链接。

#### 发布简历（人才）

1. 复制 [`templates/talent.md`](templates/talent.md)。
2. 用 [在 `talents/` 里新建文件](https://github.com/softprobe/openjob/new/main/talents) 创建档案。文件名输入框已经相对于 `talents/`。填 `<首字母>/<github用户名>.md`，全部小写。首字母是 GitHub 登录名的第一个字符，文件名就是这个登录名。例如 `z/zwobill.md`，完整路径是 `talents/z/zwobill.md`。
3. `github` 必须是这个登录名，并且与文件名、Pull Request 作者一致。填好 `name`、`headline`、`location`、`remote`、`languages`、`tags`、`open_to`（`full-time`、`part-time`、`contract` 或 `internship`）和 `posted`。可选 `website`，或 `linkedin`（`https://www.linkedin.com/in/…`）。不要写电话、邮箱或微信号。
4. 打开一个只改帖子文件的 Pull Request，全程在 GitHub 网页上完成（**Add file**，然后提交并创建 Pull Request）。
5. 校验通过后自动合并。用分享按钮分享 `https://softprobe.github.io/openjob/p/talents/<首字母>/<用户名>/`。

简历全文可以放在你自己的仓库里。把 [`templates/talent-ref.md`](templates/talent-ref.md) 复制到同样规则的路径，本仓库只留索引。见 [联邦档案](CONTRIBUTING.md#federation)。

#### 添加公司页

1. 复制 [`templates/company.md`](templates/company.md)。
2. 用 [在 `companies/` 里新建文件](https://github.com/softprobe/openjob/new/main/companies) 创建页面。文件名输入框已经相对于 `companies/`。填 `<首字母>/<slug>.md`。首字母是 `slug` 的第一个字符。例如 `s/softprobe.md`，完整路径是 `companies/s/softprobe.md`。
3. 填好 `slug`、`name`、`website`、`careers`、`location`、`tags`、`languages`、`posted` 和 `posted_by`（你的 GitHub 登录名）。链接用 `https://`。可选 `logo` 是仓库外的 https 图片地址，不要提交图片文件。不要写招聘电话或招聘邮箱。招聘邮箱写在职位帖上。
4. 打开一个只改帖子文件的 Pull Request，全程在 GitHub 网页上完成。该公司的职位可以是同一个 Pull Request 里的另一篇帖子。
5. 校验通过后自动合并。公司页会一直保留，直到所有者删除。用分享按钮分享 `https://softprobe.github.io/openjob/p/companies/<首字母>/<slug>/`。

检查没通过时，机器人会在 Pull Request 里留言并保持打开。改完文件后再推送到同一个 Pull Request。期限、隐私规则和 schema 见下文和 [CONTRIBUTING.md](CONTRIBUTING.md)。

### 参考

仓库就是公告板，搜索页是静态的，没有账号，也没有站内信。它是 LinkedIn 和 BOSS直聘 的公开替代：公告本身就是一份文本、一个链接和一个到期日，而不是社交网络。

**隐私优先。** 不要公开电话号码，也不要公开个人邮箱，帖子、Pull Request 和 Issue 里都不要。人才帖不能写邮箱。职位可以在 `apply` 写 `mailto:jobs@公司域名`，或另写 `apply_email`，但域名必须和公司网站一致（忽略 `www.`）。这个地址不会进入分享文案。网站可以显示「邮件申请」按钮。正文里的邮箱、人才帖里的邮箱，以及 gmail.com 这类不匹配的域名，都会被拒绝。其他联系方式只能是 LinkedIn、GitHub 主页、个人网站，或公司的招聘/申请链接。检查脚本也会拒绝 `name [at] domain`、全角字符、`%40`、`+86` 手机号和中文数字写法。细节见 [CONTRIBUTING.md](CONTRIBUTING.md#privacy)。

在线看板只有 `jobs/`、`talents/` 和 `companies/`。示例帖曾经放在这三处，现在在 `tests/fixtures/samples/`，不会发布。带 `example: true` 的文件是示例，不是真实招聘、简历或公司。`templates/` 是开 Pull Request 时复制的起点。站点索引不读取 `tests/` 或 `templates/`。

| 类型 | 路径 | 期限 |
| --- | --- | --- |
| 职位 | `jobs/年/月/公司-职位.md` | 默认 60 天 |
| 人才 | `talents/首字母/用户名.md` | 默认 180 天 |
| 联邦档案 | 同上，`kind: talent-ref` | 正文放在你自己的 `openjob-profile` 仓库，这里只留索引 |
| 公司 | `companies/首字母/slug.md` | 不自动过期 |

一个 Pull Request 可以提交多篇帖子。路径、大小（10 KB 以内）、纯文本、所有权和隐私都通过，且改动都在 `jobs/`、`talents/`、`companies/` 里时，会自动 squash 合并。改工作流、网站或文档需要 Softprobe 团队 `@softprobe/openjob-maintainers` 批准。

过期帖子从目录中删除。**Git 历史就是归档。** 想恢复时，从删除那次提交里取出文件，把 `renewed` 设为新的日期，再开一个 Pull Request。不要修改原来的 `posted`。

搜索页可以按职位、地点、远程、标签和语言筛选。公告板上只有 `jobs/`、`talents/`、`companies/` 里的帖子。示例帖在 `tests/fixtures/samples/`，模板在 `templates/`，这两处都不会进入索引。

每篇帖子有一个永久链接：`https://softprobe.github.io/openjob/p/<去掉.md的路径>/`。页面带分享按钮（LinkedIn、X、Reddit、Hacker News、Facebook、Telegram、WhatsApp、微博）和复制链接。微信没有分享链接，页面在浏览器里把永久链接画成二维码。分享文案只包含职位、公司和地点，或人才的 headline，或公司名和地点，不含申请链接、电话或邮箱。职位页可以有「邮件申请」按钮，那个地址不在分享文案里。自动合并后，机器人会在 Pull Request 里留下这些链接。

代码用 MIT，帖子用 CC BY 4.0。举报和删除流程在 [SECURITY.md](SECURITY.md)。工作流、仓库设置和目录布局见上方英文部分。

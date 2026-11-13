# OpenJob

[![Validate](https://github.com/zwobill/openjob/actions/workflows/validate.yml/badge.svg)](https://github.com/zwobill/openjob/actions/workflows/validate.yml)

An open, GitHub-native job board. Anyone can post a job or a talent profile by opening a pull request. The board is the repository. Search is a static page. There is no account system and no inbox.

This is a public alternative to LinkedIn and BOSS直聘 for people who want the listing itself to be the product: a text file, a link, and an expiry date. It does not try to be a social network.

**Privacy first.** Do not publish a phone number or a personal email address. Not in a post, not in a pull request, and not in an issue. Contact goes through a LinkedIn URL, a GitHub profile, a personal site, or a company careers/apply link. The checker rejects ordinary addresses and common disguises (`name [at] domain`, fullwidth characters, HTML entities, `%40`, `+86` mobiles, and Chinese numerals). See [Contributing](CONTRIBUTING.md#privacy).

Browse the board at <https://zwobill.github.io/openjob/> after GitHub Pages is enabled. Until then, read the files under `jobs/`, `talents/`, and `companies/`.

The three files there today are samples (`example: true`). They are not a real opening, a real résumé, or a real company.

## Post something

| Kind | Path | Lifetime |
| --- | --- | --- |
| Job | `jobs/YYYY/MM/<company>-<role-slug>.md` | 60 days, then renew or it is removed |
| Talent | `talents/<first-letter>/<github-username>.md` | 180 days |
| Federated talent | same talent path, `kind: talent-ref` | 180 days; the full profile stays in your repo |
| Company | `companies/<first-letter>/<slug>.md` | kept until the owner deletes it |

Copy a file from `templates/`. One post per pull request. Set `posted_by` or `github` to your GitHub login. The check squash-merges the pull request when it only touches that file and the file is valid. Anything else waits for a maintainer (`@zwobill`).

Posts are text, UTF-8, and at most 10 KB. Images, PDFs, and other binaries are rejected.

Full steps, the federation layout, and the renewal rules are in [CONTRIBUTING.md](CONTRIBUTING.md).

## How it stays small

- Sharded paths, so a single directory does not collect every post. Jobs are grouped by month. Talent and company files are grouped by the first letter. If a letter directory approaches about 800 files, maintainers add a second level in a separate change.
- No binaries in posts.
- Jobs and talent posts expire. **Git history is the archive.** The scheduled workflow opens a pull request that deletes expired files. Restore one from that commit, set `renewed`, and send it again. Company pages and sample posts are not auto-removed.

## Federation

A profile can live in `<your-username>/openjob-profile`. This repository then holds a short index entry (`kind: talent-ref`) with the same path as a normal talent file. The search page lists it and links to your repository. It does not download the profile at browse time. The index entry still expires, so a stale pointer does not sit here forever.

`schema/talent-ref.schema.json` describes the entry. `schema/index.schema.json` describes the JSON file the site searches.

## What the automation does

| Workflow | When | Effect |
| --- | --- | --- |
| `validate` | every pull request | tests, schema, path, size, privacy, ownership, scope; comments on failure |
| `automerge` | pull requests after this file is on `main` | repeats the check with the code already on `main`, then squash-merges a single-post pull request |
| `expire` | daily, 03:17 UTC | opens a pull request that deletes expired posts |
| `pages` | push to `main` | builds `index.json` and deploys the search page |

`validate` is the check on this pull request. `automerge` cannot run until that workflow exists on the default branch, because `pull_request_target` uses the workflow from `main`, not from the pull request. That is deliberate: a pull request must not be able to replace the checker and then merge itself.

## Repository settings the owner turns on

The workflows cannot flip these switches.

1. **Settings → Actions → General → Workflow permissions:** Read and write.
2. **Allow GitHub Actions to create and approve pull requests.** The expiry job needs this to open its pull request.
3. **Settings → General → Pull Requests:** Allow squash merging. Allow auto-merge.
4. **Branch protection or a ruleset on `main`:**
   - Require a pull request.
   - Require the status check `validate`. After `automerge.yml` has run once, also require `trusted-validate`.
   - Leave required approving reviews **off**, and leave "Require review from Code Owners" **off**. Otherwise a valid post waits forever. `CODEOWNERS` still names `@zwobill` for maintainer changes.
   - Pull requests opened by `GITHUB_TOKEN` do not trigger other workflows. The expiry pull request will sit without `validate`. Merge it yourself, or let the GitHub Actions bot bypass the rule.
5. **Settings → Pages → Build and deployment → Source:** GitHub Actions. The site URL is `https://zwobill.github.io/openjob/`.
6. Optional: set the repository description, the homepage URL above, and topics such as `jobs`, `hiring`, and `privacy`.

GitHub also asks a maintainer to approve Actions the first time a new fork contributor opens a pull request. That click is manual.

## Layout

```
jobs/YYYY/MM/<company>-<role-slug>.md
talents/<letter>/<github-username>.md
companies/<letter>/<slug>.md
schema/          JSON Schema for each kind, plus the public index
templates/       starting files
validator/       checker, index builder, expiry selection
site/            static search page
tests/fixtures/  privacy, path, size, and binary cases
marketing/       launch drafts, not posted anywhere
```

Run the checker locally:

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m validator build-index --root . --out site/index.json
```

## Licenses

Code, schemas, workflows, and the site are [MIT](LICENSE). Posts, templates, and the marketing drafts are [CC BY 4.0](LICENSE-CONTENT.md). Say who wrote the post and link the file if you reuse it.

Abuse reports and the takedown path are in [SECURITY.md](SECURITY.md). Conduct is the [Contributor Covenant](CODE_OF_CONDUCT.md).

## 中文

OpenJob 是一个放在 GitHub 里的公开职位板。谁都可以用 Pull Request 发布职位或人才档案，用来替代把电话交给 LinkedIn 或 BOSS直聘。仓库就是公告板，搜索页是静态的，没有账号，也没有站内信。

**隐私优先。** 不要公开电话号码或个人邮箱，帖子、Pull Request 和 Issue 里都不要。联系方式只能是 LinkedIn、GitHub 主页、个人网站，或公司的招聘/申请链接。检查脚本会拒绝普通邮箱，也会拒绝 `name [at] domain`、全角字符、`%40`、`+86` 手机号和中文数字写法。细节见 [CONTRIBUTING.md](CONTRIBUTING.md#privacy)。

| 类型 | 路径 | 期限 |
| --- | --- | --- |
| 职位 | `jobs/年/月/公司-职位.md` | 默认 60 天 |
| 人才 | `talents/首字母/用户名.md` | 默认 180 天 |
| 联邦档案 | 同上，`kind: talent-ref` | 正文放在你自己的 `openjob-profile` 仓库，这里只留索引 |
| 公司 | `companies/首字母/slug.md` | 不自动过期 |

一个 Pull Request 只提交一篇。路径、大小（10 KB 以内）、纯文本、所有权和隐私都通过后，会自动 squash 合并。改工作流、网站或文档需要维护者 `@zwobill` 合并。

过期帖子从目录中删除。**Git 历史就是归档。** 想恢复时，从删除那次提交里取出文件，把 `renewed` 设为新的日期，再开一个 Pull Request。不要修改原来的 `posted`。

启用 GitHub Pages 之后，搜索页在 <https://zwobill.github.io/openjob/>。页面上可以按职位、地点、远程、标签和语言筛选。当前三篇是示例，不是真实招聘或简历。

代码用 MIT，帖子用 CC BY 4.0。举报和删除流程在 [SECURITY.md](SECURITY.md)。

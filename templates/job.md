---
kind: job
title: "Role title"
company: company-slug
company_name: "Company name"
role_slug: role-slug
location: "City or Remote"
remote: true
languages: [en]
tags: [example-tag]
apply: https://example.com/careers/ROLE
# Optional. One mailto on the company domain, used with the https link above.
# apply_email: mailto:jobs@example.com
# website: https://example.com
posted: YYYY-MM-DD
posted_by: YOUR_GITHUB
compensation: "Optional short note"
---

Replace every placeholder, then move this file to `jobs/YYYY/MM/<company>-<role-slug>.md`. `YYYY/MM` is the `posted` month. `remote` may be `true`, `false`, or `hybrid`.

Describe the work in English, Chinese, or both. Link to a careers page or application form. A hiring address is allowed only as `mailto:` in `apply` or `apply_email`, and only on the company website's domain. Do not put an email in the body. Do not add a phone number.

## 说明

把占位符换成真实内容，文件放到 `jobs/年/月/公司-职位.md`。邮箱只能是公司域名上的 `mailto:`，放在 `apply` 或 `apply_email`。不要在正文里写邮箱，也不要写电话。

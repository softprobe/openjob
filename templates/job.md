---
kind: job
title: "Role title"
company: company-slug
company_name: "Company name"
role_slug: role-slug
location: "City or Remote"
remote: true
# Optional. true or remote, false or onsite, or hybrid.
# Optional schema.org employmentType. One value or a list:
# FULL_TIME, PART_TIME, CONTRACTOR, TEMPORARY, INTERN, VOLUNTEER, PER_DIEM, OTHER.
# employment_type: [FULL_TIME]
# Optional structured pay. Do not invent a number. currency is ISO 4217.
# salary:
#   min: 100000
#   max: 140000
#   currency: USD
#   unit: YEAR
# Optional structured places. country is ISO 3166-1 alpha-2.
# locations:
#   - city: Los Altos
#     region: CA
#     country: US
languages: [en]
tags: [example-tag]
# Required. Choose one of these two shapes:
#   an https link to an ATS, a careers page, or a LinkedIn job
#   apply: https://jobs.example.com/role
#   or a mailto on the company website's own domain
#   apply: mailto:jobs@example.com
apply: https://example.com/careers/ROLE
# Optional, and only when apply above is an https link.
# One mailto on that same company domain. Rejected when:
#   apply is also a mailto (a job has one hiring address)
#   the email domain does not match the company website
#   the address is personal or on another domain, such as gmail.com
#   any phone number appears in the file
# Do not copy the address into the body. The site prints it in How to apply.
# The company page's website wins when companies/<letter>/<slug>.md exists.
# Otherwise set website here. A leading www. is ignored.
# apply_email: mailto:jobs@example.com
# website: https://example.com
posted: YYYY-MM-DD
posted_by: YOUR_GITHUB
compensation: "Optional short note"
---

Replace every placeholder, then move this file to `jobs/YYYY/MM/<company>-<role-slug>.md`. `YYYY/MM` is the `posted` month. `remote` may be `true`, `false`, `hybrid`, or the words `remote`, `onsite`, and `hybrid`. Optional fields: `employment_type`, `salary` (`min`, `max`, ISO 4217 `currency`, `unit` of `HOUR`, `DAY`, `WEEK`, `MONTH`, or `YEAR`), and `locations` (`city`, `region`, ISO 3166-1 alpha-2 `country`). Leave `salary` out unless the number is real.

Describe the work in English, Chinese, or both. `apply` is required. Use an `https://` link to an ATS, careers page, or job posting, or `mailto:jobs@company.example` on the company website's domain. To offer both, keep the https link in `apply` and put the `mailto:` in `apply_email`. Do not set both to `mailto:`. Do not put an email in the body. Do not add a phone number. See `CONTRIBUTING.md` under Application methods.

## 说明

把占位符换成真实内容，文件放到 `jobs/年/月/公司-职位.md`。`apply` 必填：要么是 ATS、招聘页或职位链接的 `https://`，要么是公司域名上的 `mailto:`。两者都要时，`apply` 保持 https，`apply_email` 写 `mailto:`。不能两个都写成 `mailto:`。不要在正文里写邮箱，也不要写电话。可选 `employment_type`、`salary` 和 `locations`。没有真实薪资就不要写 `salary`。规则见 CONTRIBUTING.md 的 Application methods。

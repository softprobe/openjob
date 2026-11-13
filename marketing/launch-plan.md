# Launch plan

Draft. Do not post any of the channel drafts until the steps below are done.

## Before anyone outside sees a link

1. Merge the initial pull request.
2. Turn on the repository settings listed in the README: Actions read/write, squash merges, auto-merge, branch protection that requires `validate` and does not require a human review, Pages with the GitHub Actions source.
3. Open one real post as a pull request from a non-owner account if you can, and confirm it squash-merges and then appears on the Pages site. If you cannot, do the same flow from a second branch you own and watch the logs.
4. Read the sample posts. Delete them when real ones exist, or leave them labeled as samples. Do not announce a board that only contains samples.
5. Skim the first posts yourself even though CI is green. The checker misses some contact handles that are not phone numbers.

## Order

Do not post the same announcement everywhere on the same hour.

1. A short note to people who would actually submit a job or a profile. Ask them to use the pull request, not to email you a PDF.
2. V2EX (`v2ex.md`) and the X thread (`x-thread.md`) on a weekday. V2EX in the China evening, the English thread when the US east coast is awake, if you want both audiences.
3. Show HN (`hacker-news.md`) once the site loads and at least a few real posts are merged. The title has to match the site a reader lands on.
4. LinkedIn (`linkedin.md`) and 即刻 (`jike.md`) the same day or the next day, as a personal post from the maintainer, not a brand blast.
5. Product Hunt (`product-hunt.md`) a few days later, after the first comments on HN or V2EX have been answered. A Product Hunt page with an empty board looks abandoned.
6. 小红书 (`xiaohongshu.md`) as a practical note, with a screenshot you take yourself of the search page. The draft is text only.
7. Reddit (`reddit.md`) last, and only in one appropriate subreddit. Do not cross-post a stack of them.

## What to measure

- Pull requests opened and merged, by kind (job, talent, company, talent-ref).
- Checker failures, especially privacy, so the error text can be improved.
- Pages loads only if you later add a privacy-respecting counter. Do not add a tracker for launch.

## What not to do

- Do not buy ads that ask people to leave a phone number.
- Do not paste résumés into the repository for someone else.
- Do not post the drafts in this folder unchanged if a sentence is no longer true.
- Do not enable required code-owner review and then wonder why auto-merge stalled.

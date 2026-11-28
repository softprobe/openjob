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




## Where OpenJob is listed
- [LibHunt](https://www.libhunt.com/r/softprobe/openjob)
- [mcpservers.org](https://mcpservers.org/servers/openjob-softprobe-ai)
- [cursor.directory](https://cursor.directory/plugins/openjob)
- [AlternativeTo](https://alternativeto.net/software/openjob/about/)
- [PitchWall](https://pitchwall.co/product/openjob-ai-agent-job-search-database) (under review)
- [Product Hunt](https://www.producthunt.com/products/openjob)


Claude Code users can install the OpenJob plugin in one step (Claude Code 2.1.275 or later):


```text
/plugin install openjob --marketplace softprobe/openjob
```


## Connect your agent

Point your agent at the OpenJob MCP server (Streamable HTTP): `https://openjob.softprobe.ai/api/mcp`. One line per agent, in each agent's own config format:

- **Hermes** — in `~/.hermes/config.yaml`: `mcp_servers: {openjob: {url: "https://openjob.softprobe.ai/api/mcp"}}`
- **OpenClaw** — `openclaw mcp add openjob --url https://openjob.softprobe.ai/api/mcp --transport streamable-http`
- **OpenCode** — in `opencode.json`: `"mcp": {"servers": {"openjob": {"type": "remote", "url": "https://openjob.softprobe.ai/api/mcp"}}}`
- **Goose** — in `~/.config/goose/config.yaml`, under `extensions:`: `openjob: {name: OpenJob, type: streamable_http, uri: "https://openjob.softprobe.ai/api/mcp", enabled: true}`
- **Zed** — in `settings.json`: `"context_servers": {"openjob": {"url": "https://openjob.softprobe.ai/api/mcp"}}`

No MCP setup? **Instinct** has no plugin system, so paste this prompt instead: `Read https://openjob.softprobe.ai/llms.txt and follow it.`

Paste one prompt. The agent reads [llms.txt](https://openjob.softprobe.ai/llms.txt) and [AGENTS.md](AGENTS.md).


### Find me a job


```text
Read https://openjob.softprobe.ai/llms.txt and follow it. If the OpenJob MCP server is connected, use list_jobs. Otherwise GET https://openjob.softprobe.ai/api/v1/jobs for a bounded page, or download every shard from https://openjob.softprobe.ai/api/data/manifest.json and rank the complete data yourself when code execution is available. Return each match with its permalink and the apply method already on that post. Do not invent an email or a phone number. Resume or bio: <paste here>
```


### Post our role


```text
Read https://openjob.softprobe.ai/llms.txt and follow it. Prepare one job post and show me the exact Markdown. Open one pull request with my connected GitHub account only after I approve it. If you cannot use a connected GitHub account, give me the Markdown and this new-file link: https://github.com/softprobe/openjob/new/main/jobs. Set posted_by to the login that opens the pull request. If the company page exists, that login must be in its owners lis

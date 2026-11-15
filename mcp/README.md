# OpenJob MCP server

Agents use this server to search the public board and to open one pull request on behalf of a person.

Read tools use <https://openjob.softprobe.ai/index.json>. They do not need a token.

Write tools need `GITHUB_TOKEN` for the person. The server opens or updates one pull request as that login. It forks the repository when that login cannot push. It sets the filename, `posted_by`, `github`, and `owners`. It does not push to the default branch.

This package is not published to PyPI yet. Install it from git.

```
uvx --from git+https://github.com/softprobe/openjob.git openjob-mcp
```

The same install provides the `openjob` command:

```
uvx --from git+https://github.com/softprobe/openjob.git openjob search-jobs "reliability"
```

From a checkout of this repository:

```
PYTHONPATH=mcp:cli python -m openjob_mcp
PYTHONPATH=mcp:cli python -m openjob_cli search-jobs "reliability"
```

## Tools

| Tool | Token | What it does |
| --- | --- | --- |
| `search_jobs` | No | `query` plus `filters`: `location`, `remote`, `language`, `tag`, `employment_type` |
| `get_job` | No | One job by path or permalink |
| `search_talent` | No | `query` plus `filters`, including `open_to` |
| `get_talent` | No | One profile by GitHub login |
| `validate_post` | No | `kind` (`job`, `talent`, or `company`) and Markdown. No pull request |
| `create_or_update_post` | Yes | `kind` and `fields`. Builds the file and opens the pull request. `dry_run` returns the file only |
| `close_job` | Yes | Pull request that removes a job. `dry_run` returns the path only |

`fields` is the front matter plus `body`. On a new post the server sets `posted_by` or `github` to the token's login. A company page gets that login in `owners`.

## Claude Desktop

Add this to `claude_desktop_config.json`. Put the person's token in the environment. Leave it out when the agent only searches.

```json
{
  "mcpServers": {
    "openjob": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/softprobe/openjob.git", "openjob-mcp"],
      "env": {
        "GITHUB_TOKEN": "github_pat_replace_me"
      }
    }
  }
}
```

## Cursor

Add the same `mcpServers` entry to `~/.cursor/mcp.json`.

## ChatGPT

ChatGPT custom connectors call a remote MCP URL. This server speaks stdio, which Claude Desktop and Cursor run. It does not start an HTTP server.

## Command line

`cli/` is the `openjob` command in this same package. `search-jobs`, `get-job`, `search-talent`, `get-talent`, and `validate` need no token. `post` and `close` need `GITHUB_TOKEN` unless you pass `--dry-run`.

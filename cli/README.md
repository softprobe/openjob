# OpenJob command line

`openjob` is installed with the MCP server. See [mcp/README.md](../mcp/README.md).

```
uvx --from git+https://github.com/softprobe/openjob.git openjob search-jobs "reliability"
```

`search-jobs`, `get-job`, `search-talent`, `get-talent`, and `validate` read the public board or a local file. `post` and `close` open one pull request and need `GITHUB_TOKEN`. `--dry-run` prints the file or the path and does not call GitHub.

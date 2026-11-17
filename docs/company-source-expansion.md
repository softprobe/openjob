# November 2026 company source expansion

This change adds 100 company boards on OpenJob's existing ATS providers and 100 China-based company boards on Moka. Each board is represented by one `sources/<slug>.yml` file and links indexed jobs back to the employer's public careers page and application flow.

## Discovery and verification

The Ashby, Greenhouse, and Lever board candidates were adapted from Deriverge's [Ashby directory](https://deriverge.com/tools/companies-using-ashby/), [Greenhouse directory](https://deriverge.com/tools/companies-using-greenhouse/), and [Lever directory](https://deriverge.com/tools/companies-using-lever/), which are available under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Each selected board was checked against its public provider feed using OpenJob's indexer.

Moka organization and site identifiers were discovered in the MIT-licensed [Hiring-Radar](https://github.com/simonlin1212/Hiring-Radar) and [openings-mcp](https://github.com/amikai/openings-mcp) catalogs. Each selected China-based employer was checked against Moka's public jobs API. The November 17, 2026 verification snapshot found 4,610 open jobs across the 100 global boards and 14,705 across the 100 Moka boards; feed contents can change before an index run.

## Moka feed handling

Moka's [Career website API](https://www.mokahr.com/docs/api/english.index.html) documents the public `GET /api-platform/v1/jobs/{orgId}` endpoint and its `mode`, `siteId`, `status`, `limit`, and `offset` parameters. The source URL is restricted to the employer's `app.mokahr.com` social or campus career page. OpenJob requests only open jobs in pages of 100, follows offsets, and sends no credentials. The adapter retains job facts and official source and apply links; it drops descriptions.

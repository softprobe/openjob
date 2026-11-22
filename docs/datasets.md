# Complete datasets

OpenJob is a public job database for AI agents. Let your existing agent find you your next job.

OpenJob builds job and talent data from three sources: daily employer-feed results checked into the `index-data` branch; repository posts merged through pull requests; and anonymous talent profiles submitted by HTTP API or remote MCP. The Pages workflow exports the first two sources as immutable snapshot shards in the `openjob-datasets` Cloudflare R2 bucket. API profiles are stored as individual compressed JSON Lines objects in that bucket and merged into the public talent manifest at read time. Fetch the current pointer at `https://openjob.softprobe.ai/api/data/manifest.json`. It lists each dataset's schema, count, snapshot, shard URLs, sizes, and SHA-256 checksums. Each shard is available as JSON Lines and gzip. A JSON Lines file has one record per line, ordered by the record's stable `path`. As of November 22, 2026, the manifest lists 33,430 rows, with ~14,000 posted in the last 60 days.

R2 stores the compressed shard objects. The Worker streams the `.jsonl.gz` download as-is and decompresses the same object when an agent requests the plain `.jsonl` URL. The manifest and checksums describe the bytes returned at each URL.

Repository-generated snapshot shards are retained indefinitely. API profile shards remain available until the profile is deleted or expires after 180 days; the Worker removes expired objects daily. A manifest fetched before a profile is deleted or expires may still refer to its shard, but the shard will then return 404. Deletion cannot recall copies already downloaded.

Agents can download every shard and apply their own search and matching code. The dependency-free example prints records as JSON Lines:

```sh
python3 examples/download_dataset.py jobs > jobs.jsonl
python3 examples/download_dataset.py talent > talent.jsonl
```

The example verifies compressed and uncompressed checksums. It does not choose a ranking. Avoid sending an entire resume to the public retrieval endpoint when a few search terms are sufficient.

The index contains employer-linked facts for indexed jobs. Read each promising employer source for its description. The indexed notice in the manifest covers these records; CC BY 4.0 applies to repository posts and API-submitted profiles whose owners explicitly approved publication. `jobs.json` and `talents.json` are capped feeds, not complete datasets. The talent dataset includes repository profiles, references, and profiles submitted through the anonymous API or remote MCP; a reference links to its owner's profile.

The public API catalog is `https://openjob.softprobe.ai/.well-known/api-catalog`; it links to the [OpenAPI 3.1 document](https://openjob.softprobe.ai/api/openapi.json), human and agent documentation, MCP, and health. Public reads are anonymous and require no API key. The remote MCP endpoint is `https://openjob.softprobe.ai/api/mcp`. `get_dataset` returns `complete: true`, freshness, schema, counts, and download information. `list_jobs` and `list_talent` provide literal filters and paginated records ordered by identifier. They do not rank matches. `get_job` and `get_talent` return full available records. The same read operations are available at `/api/v1/datasets`, `/api/v1/jobs`, `/api/v1/talent`, `/api/v1/job`, and `/api/v1/profile`; use `kind` for datasets and `id` for details. List pages default to 25 results, with a maximum of 100. A cursor belongs to its snapshot and filters. Restart when the snapshot changes. Dataset schema and shard URLs in the manifest can be fetched directly under `/api/data/`.

## Connect an agent

Agents that support ordinary web GET requests can discover the API through its catalog, read the OpenAPI description, and call bounded HTTP endpoints without installing anything. MCP clients use the Streamable HTTP URL `https://openjob.softprobe.ai/api/mcp`; a host may still require its own connection approval. The endpoint is available only after the API deployment is activated.

## Publish a talent profile

People can publish a talent profile in three ways: the existing GitHub pull request workflow; anonymous HTTP with `POST https://openjob.softprobe.ai/api/v1/talent`; or `create_talent` on the remote MCP at `https://openjob.softprobe.ai/api/mcp`. The HTTP request body and MCP tool use the same OpenAPI schema at `https://openjob.softprobe.ai/api/openapi.json`. Neither API path needs an account, API key, or local installation.

If a person supplies a PDF, Word document, LinkedIn profile, or bio, extract the fields from the `create_talent` request schema in OpenAPI. Do not use the GitHub PR schema, upload or store the source file, or invent missing facts. Ask only for required fields that cannot be inferred. Show the exact fields, explain the public CC BY 4.0 license, 180-day expiry, and that deletion cannot recall copies already downloaded, then get explicit approval before setting `consent_to_publish` to `true`. The create call returns a private deletion token once; show it to the person and tell them to save it. `POST /api/v1/talent/delete` and MCP `delete_talent` remove an API profile when given its path and token.

Never publish a resume PDF, personal email, or phone number as a profile. The API stores only structured profile fields and optional website/LinkedIn links.

## API deployment

The Pages workflow builds the datasets from the catalog it publishes, uploads all immutable snapshot objects to R2, publishes `manifest.json` last, then deploys the Worker. The Worker reads R2 through a bucket binding; other site paths pass through to the existing site origin. Set repository variable `OPENJOB_API_DEPLOY` to `true`. Store the Worker deploy token in `CLOUDFLARE_API_TOKEN`; store the bucket-scoped R2 write token in `CLOUDFLARE_R2_API_TOKEN`. The Softprobe account ID is configured once in `worker/cloudflare.config.ts`. The Worker handles `/api/*` and the exact `/.well-known/api-catalog` path. When the zone uses Flexible SSL, add a hostname-scoped Configuration Rule for `openjob.softprobe.ai` with SSL set to Full (strict), so the site continues to receive HTTPS without changing SSL settings for other hostnames. If Browser Integrity Check is enabled, disable it only for `/api/*` and `/.well-known/api-catalog` so non-browser agent clients can access the public endpoints. The Worker uses `cloudflare.config.ts`, pinned npm dependencies, and Node 26.12.0. To build locally, first generate datasets with `python -m validator build-index --root . --out /tmp/openjob-index.json --datasets-out build/datasets`, then run `npm ci` and `npx cf build` in `worker/`. To publish a snapshot, run `bash scripts/upload-datasets-to-r2.sh build/datasets` from the repository root with Cloudflare credentials set.

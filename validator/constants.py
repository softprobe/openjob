"""Limits shared by the checker, the index, and the docs."""

MAX_POST_BYTES = 10 * 1024
JOB_DAYS = 60
TALENT_DAYS = 180
MAX_LINKS = 12
MIN_BODY_CHARS = 40
NEW_POST_MAX_AGE_DAYS = 45
FUTURE_SKEW_DAYS = 2
# GitHub account that owns this repository. The maintainer is still @zwobill.
REPO = "softprobe/openjob"
REPO_OWNER = "softprobe"

POST_ROOTS = ("jobs", "talents", "companies")
# Starting files and test fixtures are not posts. The site index, the expiry
# walk, and ``check-tree`` never read these directories.
UNPUBLISHED_ROOTS = frozenset({"tests", "templates"})
KIND_ROOT = {
    "job": "jobs",
    "talent": "talents",
    "talent-ref": "talents",
    "company": "companies",
}

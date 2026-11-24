# How to Validate and Contribute MySQL Entries

Use this procedure to add an open-source MySQL resource, validate entry format, and test Jekyll config safety.

## Prerequisites

- Confirm Git and Python 3 are installed on the host.
- Confirm your entry meets open-source criteria inside [`CONTRIBUTING.md`](../../CONTRIBUTING.md).

NOTE: Review alphabetical rules and entry format rules in [Categories, Jekyll, and Entry Specification Reference](../03-reference/categories-jekyll-and-entry-spec.md).

## Procedure

### Format and Place a New Resource

CAUTION: Never add proprietary tools, paid websites, or login-gated links. Rejected entries fail pull request checks.

1. Sort the target category and item label alphabetically under `utf8_general_ci`.
2. Write the entry with one link and one lowercase description:

```markdown
- [Orchestrator](https://github.com/openark/orchestrator) - replication topology management tool for MySQL.
```

3. Keep nested files inside `docs/` free of Jekyll `layout: default` headers.

### Verify Jekyll Configuration and Automated Tests

1. Confirm `_config.yml` excludes both `README.md` and `tests/`:

```bash
python3 -c "import yaml; c=yaml.safe_load(open('_config.yml')); assert 'tests/' in c['exclude']; print(c['exclude'])"
```

2. Run the full verification suite from the repository root:

```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

## Validation

Confirm all tests pass with exit code `0` and inspect `git diff` cleanly:

```bash
git status --short
```

## Rollback

If an entry fails validation or breaks tests, revert your edited Markdown file cleanly:

```bash
git checkout -- README.md index.md
```

Read design rationale and branch background in [Curated List Design and `gh-pages` Layout](../04-explanation/curated-list-design-and-gh-pages.md).

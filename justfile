# Perth BitDevs — static site helpers

# Create the Python environment used by local helpers
setup-newswatch:
    python3 -m venv .venv
    . .venv/bin/activate && python -m pip install -r tools/newswatch/requirements.txt

# Validate curated newswatch source config
news-validate-sources:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -x .venv/bin/python ]; then
      echo "Missing .venv. Run: just setup-newswatch" >&2
      exit 1
    fi
    . .venv/bin/activate
    python tools/newswatch/newswatch.py validate-sources

# Scan curated sources, optional meetup issue topics, and optional local imports.
# Example: just news-scan since=2026-05-07 issue=36 import=tools/newswatch/imports/local.json
news-scan since="" issue="" import="":
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -x .venv/bin/python ]; then
      echo "Missing .venv. Run: just setup-newswatch" >&2
      exit 1
    fi
    . .venv/bin/activate
    args=()
    since_arg="{{since}}"
    since_arg="${since_arg#since=}"
    if [ -n "$since_arg" ]; then
      args+=(--since "$since_arg")
    fi
    issue_arg="{{issue}}"
    issue_arg="${issue_arg#issue=}"
    if [ -n "$issue_arg" ]; then
      args+=(--github-issue "$issue_arg")
    fi
    import_arg="{{import}}"
    import_arg="${import_arg#import=}"
    if [ -n "$import_arg" ]; then
      args+=(--import-packet "$import_arg")
    fi
    python tools/newswatch/newswatch.py scan "${args[@]}"

# Run newswatch tests
news-test:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -x .venv/bin/python ]; then
      echo "Missing .venv. Run: just setup-newswatch" >&2
      exit 1
    fi
    . .venv/bin/activate
    python -m unittest discover -s tools/newswatch/tests

# Validate local static-site contracts without network access
site-check:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -x .venv/bin/python ]; then
      echo "Missing .venv. Run: just setup-newswatch" >&2
      exit 1
    fi
    . .venv/bin/activate
    python tools/site_check.py

# Run all local validation checks
check:
    just site-check
    just news-validate-sources
    just news-test

# Serve the site locally with working absolute links
dev:
    #!/usr/bin/env bash
    set -euo pipefail
    ruby -run -e httpd . -p 8000

# Open the site in the default browser
open:
    open http://localhost:8000

# Serve and open in one step
run:
    #!/usr/bin/env bash
    set -euo pipefail
    ruby -run -e httpd . -p 8000 &
    sleep 0.5
    open http://localhost:8000
    wait

# Remove local generated outputs
clean:
    rm -rf tools/newswatch/runs tools/newswatch/state.local.json

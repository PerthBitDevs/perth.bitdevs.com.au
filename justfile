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

# Preview a scan without advancing the local state cursor.
# Example: just news-scan-preview since=2026-05-07 issue=36 import=tools/newswatch/imports/local.json
news-scan-preview since="" issue="" import="":
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -x .venv/bin/python ]; then
      echo "Missing .venv. Run: just setup-newswatch" >&2
      exit 1
    fi
    . .venv/bin/activate
    args=(--no-state-update)
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
dev port="8000":
    #!/usr/bin/env bash
    set -euo pipefail
    port_arg="{{port}}"
    port="${port_arg#port=}"
    ruby -run -e httpd . -p "$port"

# Open the site in the default browser
open port="8000":
    #!/usr/bin/env bash
    set -euo pipefail
    port_arg="{{port}}"
    port="${port_arg#port=}"
    open "http://localhost:$port"

# Serve and open in one step
run port="8000":
    #!/usr/bin/env bash
    set -euo pipefail
    port_arg="{{port}}"
    port="${port_arg#port=}"
    if ! [[ "$port" =~ ^[0-9]+$ ]] || [ "$port" -lt 1 ] || [ "$port" -gt 65535 ]; then
      echo "Invalid port: $port" >&2
      exit 2
    fi
    if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
      echo "Port $port is already in use. Choose another port, e.g. just run port=8001" >&2
      exit 1
    fi

    server_log="$(mktemp -t perth-bitdevs-server.XXXXXX)"
    server_pid=""
    cleanup() {
      if [ -n "$server_pid" ] && kill -0 "$server_pid" 2>/dev/null; then
        kill "$server_pid" 2>/dev/null || true
        wait "$server_pid" 2>/dev/null || true
      fi
      rm -f "$server_log"
    }
    trap cleanup EXIT
    trap 'cleanup; exit 130' INT
    trap 'cleanup; exit 143' TERM

    ruby -run -e httpd . -p "$port" >"$server_log" 2>&1 &
    server_pid=$!
    url="http://localhost:$port"

    for _ in {1..50}; do
      if curl -fsS "http://127.0.0.1:$port/" >/dev/null 2>&1; then
        echo "Serving $url (Ctrl-C to stop)"
        open "$url"
        wait "$server_pid"
        exit $?
      fi
      if ! kill -0 "$server_pid" 2>/dev/null; then
        echo "Server exited before becoming ready:" >&2
        cat "$server_log" >&2
        exit 1
      fi
      sleep 0.1
    done

    echo "Server did not become ready on port $port" >&2
    cat "$server_log" >&2
    exit 1

# Remove local generated outputs
clean:
    rm -rf tools/newswatch/runs tools/newswatch/state.local.json

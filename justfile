# Perth BitDevs — static site helpers

# Serve the site locally with working absolute links
dev:
    python3 -m http.server 8000

# Open the site in the default browser
open:
    open http://localhost:8000

# Serve and open in one step
run:
    #!/usr/bin/env bash
    python3 -m http.server 8000 &
    sleep 0.5
    open http://localhost:8000
    wait

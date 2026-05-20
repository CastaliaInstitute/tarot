#!/usr/bin/env bash
# Enable GitHub Pages HTTPS once GitHub has issued the custom-domain certificate.

set -euo pipefail

REPO="${REPO:-CastaliaInstitute/tarot}"
CNAME="${CNAME:-tarot.castalia.institute}"

gh api "repos/${REPO}/pages" \
  -X PUT \
  -F "cname=${CNAME}" \
  -F https_enforced=true

gh api "repos/${REPO}/pages" \
  --jq '{html_url, cname, https_enforced, protected_domain_state, pending_domain_unverified_at}'

#!/bin/bash
# MetLife Pet Insurance API helper
# Source this at the start of every Bash tool call that needs API access.
# All secrets (tokens) stay in .metlife-cache/ which is gitignored.

METLIFE_CACHE_DIR=".metlife-cache"
TOKEN_FILE="$METLIFE_CACHE_DIR/.token"

# Public client keys (embedded in mypets.metlife.com SPA JavaScript)
APIM_KEY="979fd0c2ea204f1095d7faa8154c39b0"
IBM_CLIENT_ID="634dc387-c737-4a6a-86ef-f49056e30898"
CHANNEL_ID="PetMobile"
APP_VERSION="4.5.1"
ORIGIN="https://mypets.metlife.com"
REFERER="https://mypets.metlife.com/"

# Gateway base URLs
APIM_BASE="https://apis.metlife.com/external/pet-services"
IBM_BASE="https://api.metlife.com/metlife/production/api/pet-services/pingv2"

# ── Utilities ────────────────────────────────────────────────────────────────

_session_id() {
  python3 -c "import time,random,string; print(str(int(time.time()*1000))+''.join(random.choices(string.ascii_lowercase,k=3)))"
}

_pkce() {
  python3 -c "import os,base64; print(base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode())"
}

# ── Token storage ────────────────────────────────────────────────────────────
# File format (4 lines): bearer_token / refresh_token / expiry_epoch / session_id

load_tokens() {
  METLIFE_BEARER_TOKEN=$(sed -n '1p' "$TOKEN_FILE" 2>/dev/null)
  METLIFE_REFRESH_TOKEN=$(sed -n '2p' "$TOKEN_FILE" 2>/dev/null)
  METLIFE_TOKEN_EXPIRY=$(sed -n '3p' "$TOKEN_FILE" 2>/dev/null)
  METLIFE_SESSION_ID=$(sed -n '4p' "$TOKEN_FILE" 2>/dev/null)
  [ -z "$METLIFE_SESSION_ID" ] && METLIFE_SESSION_ID=$(_session_id)
}

save_tokens() {
  mkdir -p "$METLIFE_CACHE_DIR"
  printf '%s\n%s\n%s\n%s\n' \
    "$METLIFE_BEARER_TOKEN" \
    "$METLIFE_REFRESH_TOKEN" \
    "$METLIFE_TOKEN_EXPIRY" \
    "$METLIFE_SESSION_ID" > "$TOKEN_FILE"
}

token_is_expired() {
  [ -z "$METLIFE_BEARER_TOKEN" ] || [ -z "$METLIFE_TOKEN_EXPIRY" ] && return 0
  local now; now=$(date +%s)
  [ "$now" -ge $((METLIFE_TOKEN_EXPIRY - 120)) ]
}

# ── Login ────────────────────────────────────────────────────────────────────
# Usage: metlife_login "email" "password"

metlife_login() {
  local username="$1" password="$2"
  [ -z "$username" ] || [ -z "$password" ] && { echo "ERROR: Username and password required" >&2; return 1; }

  METLIFE_SESSION_ID=$(_session_id)
  local cv; cv=$(_pkce)

  # Step 1: POST /authentication/login
  echo "Logging in..." >&2
  local body
  body=$(python3 -c "import json,sys; print(json.dumps({'userName':sys.argv[1],'password':sys.argv[2],'codeChallenge':sys.argv[3]}))" "$username" "$password" "$cv")

  local r1
  r1=$(curl -s "$APIM_BASE/authentication/login" \
    -H 'content-type: application/json' \
    -H "channel-id: $CHANNEL_ID" \
    -H 'is-ping-token: true' \
    -H "ocp-apim-subscription-key: $APIM_KEY" \
    -H "origin: $ORIGIN" -H "referer: $REFERER" \
    -H "session-id: $METLIFE_SESSION_ID" \
    -H "transaction-id: $METLIFE_SESSION_ID" \
    -H "x-app-version: $APP_VERSION" \
    -H 'cache-control: no-cache, no-store' \
    --data-raw "$body" 2>/dev/null)

  local flow_id corr_id status
  read -r flow_id corr_id status < <(echo "$r1" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d.get('id',''), d.get('extension',{}).get('correlationId',''), d.get('status',''))
" 2>/dev/null)

  if [ -z "$flow_id" ]; then
    echo "ERROR: Login failed. Response: $r1" >&2
    return 1
  fi
  echo "Login step 1 OK (status: $status). Completing auth..." >&2

  # Brief pause — server needs a moment after device profile check
  sleep 2

  # Step 2: POST /authentication/profileDevice
  local body2
  body2=$(python3 -c "import json,sys; print(json.dumps({'flowId':sys.argv[1],'codeVerifier':sys.argv[2],'extension':{'correlationId':sys.argv[3]}}))" "$flow_id" "$cv" "$corr_id")

  local r2
  r2=$(curl -s "$APIM_BASE/authentication/profileDevice" \
    -H 'content-type: application/json' \
    -H "channel-id: $CHANNEL_ID" \
    -H 'is-ping-token: true' \
    -H "ocp-apim-subscription-key: $APIM_KEY" \
    -H "origin: $ORIGIN" -H "referer: $REFERER" \
    -H "session-id: $METLIFE_SESSION_ID" \
    -H "transaction-id: $METLIFE_SESSION_ID" \
    -H "x-app-version: $APP_VERSION" \
    -H 'cache-control: no-cache, no-store' \
    --data-raw "$body2" 2>/dev/null)

  local auth_status
  auth_status=$(echo "$r2" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
  if [ "$auth_status" != "COMPLETED" ]; then
    echo "ERROR: Auth failed (status: $auth_status). Response: $r2" >&2
    return 1
  fi

  # Extract tokens
  local now; now=$(date +%s)
  read -r METLIFE_BEARER_TOKEN METLIFE_REFRESH_TOKEN expires_in < <(echo "$r2" | python3 -c "
import sys,json
t=json.load(sys.stdin)['tokenResponse']
print(t['access_token'], t['refresh_token'], t['expires_in'])
" 2>/dev/null)
  METLIFE_TOKEN_EXPIRY=$((now + expires_in))

  if [ -z "$METLIFE_BEARER_TOKEN" ] || [ "$METLIFE_BEARER_TOKEN" = "None" ]; then
    echo "ERROR: No access token in response" >&2; return 1
  fi

  save_tokens
  echo "Login successful. Token expires in ${expires_in}s (~$((expires_in/60))m)." >&2
}

# ── Token refresh ────────────────────────────────────────────────────────────

refresh_token() {
  load_tokens
  [ -z "$METLIFE_REFRESH_TOKEN" ] && { echo "ERROR: No refresh token. Login required." >&2; return 1; }

  local sid; sid=$(_session_id)
  echo "Refreshing token..." >&2
  local r
  r=$(curl -s "$APIM_BASE/authentication/v2/refreshToken_v2" \
    -H 'content-type: application/json' \
    -H "channel-id: $CHANNEL_ID" \
    -H 'is-ping-token: true' \
    -H "ocp-apim-subscription-key: $APIM_KEY" \
    -H "origin: $ORIGIN" -H "referer: $REFERER" \
    -H "session-id: $sid" -H "transaction-id: $sid" \
    -H "x-app-version: $APP_VERSION" \
    -H 'cache-control: no-cache, no-store' \
    --data-raw "\"$METLIFE_REFRESH_TOKEN\"" 2>/dev/null)

  local new_tok new_ref exp_in
  read -r new_tok new_ref exp_in < <(echo "$r" | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d.get('access_token',''), d.get('refresh_token',''), d.get('expires_in',899))
" 2>/dev/null)

  if [ -n "$new_tok" ] && [ "$new_tok" != "None" ]; then
    local now; now=$(date +%s)
    METLIFE_BEARER_TOKEN="$new_tok"
    [ -n "$new_ref" ] && [ "$new_ref" != "None" ] && METLIFE_REFRESH_TOKEN="$new_ref"
    METLIFE_TOKEN_EXPIRY=$((now + exp_in))
    save_tokens
    echo "Token refreshed. Expires in ${exp_in}s (~$((exp_in/60))m)." >&2
    return 0
  fi
  echo "ERROR: Refresh failed. Response: $r" >&2
  return 1
}

# ── Auth gate ────────────────────────────────────────────────────────────────
# Call before any API operation. Returns 0 if ready, 1 if login needed.
# On failure, prints AUTH_NEEDED to stdout so the caller can detect it.

ensure_auth() {
  load_tokens
  if token_is_expired; then
    if [ -n "$METLIFE_REFRESH_TOKEN" ]; then
      refresh_token && return 0
    fi
    echo "AUTH_NEEDED"
    return 1
  fi
  return 0
}

# ── Response validation ──────────────────────────────────────────────────────

_is_error() {
  echo "$1" | grep -q '"httpCode":"401"\|"Unauthorized"\|"Token is not active"\|"httpCode":"403"'
}

is_cacheable() {
  [ -n "$1" ] && ! _is_error "$1"
}

# ── API wrappers ─────────────────────────────────────────────────────────────

# IBM API Connect gateway: claims, customer details, payments, search
# Usage: metlife_ibm "URL" [extra curl args...]
metlife_ibm() {
  load_tokens
  local url="$1"; shift
  local r
  r=$(curl -s "$url" \
    -H "authorization: Bearer $METLIFE_BEARER_TOKEN" \
    -H "x-ibm-client-id: $IBM_CLIENT_ID" \
    -H "x-session-id: $METLIFE_SESSION_ID" \
    -H "x-app-version: $APP_VERSION" \
    -H "app-version: $APP_VERSION" \
    -H 'cache-control: no-cache, no-store' \
    -H "origin: $ORIGIN" -H "referer: $REFERER" \
    -H 'accept: */*' \
    "$@")

  if _is_error "$r"; then
    echo "Got 401, refreshing..." >&2
    if refresh_token; then
      r=$(curl -s "$url" \
        -H "authorization: Bearer $METLIFE_BEARER_TOKEN" \
        -H "x-ibm-client-id: $IBM_CLIENT_ID" \
        -H "x-session-id: $METLIFE_SESSION_ID" \
        -H "x-app-version: $APP_VERSION" \
        -H "app-version: $APP_VERSION" \
        -H 'cache-control: no-cache, no-store' \
        -H "origin: $ORIGIN" -H "referer: $REFERER" \
        -H 'accept: */*' \
        "$@")
    fi
  fi
  echo "$r"
}

# Azure APIM gateway: pets, policies, rewards
# Usage: metlife_apim "URL" [extra curl args...]
metlife_apim() {
  load_tokens
  local url="$1"; shift
  local r
  r=$(curl -s "$url" \
    -H "authorization: Bearer $METLIFE_BEARER_TOKEN" \
    -H "ocp-apim-subscription-key: $APIM_KEY" \
    -H "channel-id: $CHANNEL_ID" \
    -H 'is-ping-token: true' \
    -H "session-id: $METLIFE_SESSION_ID" \
    -H "transaction-id: $METLIFE_SESSION_ID" \
    -H "x-app-version: $APP_VERSION" \
    -H 'cache-control: no-cache, no-store' \
    -H "origin: $ORIGIN" -H "referer: $REFERER" \
    -H 'accept: */*' \
    "$@")

  if _is_error "$r"; then
    echo "Got 401, refreshing..." >&2
    if refresh_token; then
      r=$(curl -s "$url" \
        -H "authorization: Bearer $METLIFE_BEARER_TOKEN" \
        -H "ocp-apim-subscription-key: $APIM_KEY" \
        -H "channel-id: $CHANNEL_ID" \
        -H 'is-ping-token: true' \
        -H "session-id: $METLIFE_SESSION_ID" \
        -H "transaction-id: $METLIFE_SESSION_ID" \
        -H "x-app-version: $APP_VERSION" \
        -H 'cache-control: no-cache, no-store' \
        -H "origin: $ORIGIN" -H "referer: $REFERER" \
        -H 'accept: */*' \
        "$@")
    fi
  fi
  echo "$r"
}

# Auto-routing wrapper: picks the right gateway based on URL
metlife_api() {
  local url="$1"
  if [[ "$url" == *"apis.metlife.com"* ]]; then
    metlife_apim "$@"
  else
    metlife_ibm "$@"
  fi
}

# ── Cache cleanup ────────────────────────────────────────────────────────────

# Purge any cached JSON files that contain error responses
purge_bad_cache() {
  local count=0
  while IFS= read -r -d '' f; do
    if grep -q '"httpCode":"401"\|"Token is not active"\|"Unauthorized"' "$f" 2>/dev/null; then
      rm "$f"
      ((count++))
    fi
  done < <(find "$METLIFE_CACHE_DIR" -name '*.json' -print0 2>/dev/null)
  [ "$count" -gt 0 ] && echo "Purged $count cached error responses." >&2
}

# Full reset: clear all cached data and tokens
metlife_reset() {
  rm -f "$TOKEN_FILE"
  rm -rf "$METLIFE_CACHE_DIR/claims" "$METLIFE_CACHE_DIR/documents" "$METLIFE_CACHE_DIR/policies"
  mkdir -p "$METLIFE_CACHE_DIR/claims" "$METLIFE_CACHE_DIR/documents" "$METLIFE_CACHE_DIR/policies"
  echo "Cache and tokens cleared." >&2
}

# ── Auto-init ────────────────────────────────────────────────────────────────

load_tokens
purge_bad_cache

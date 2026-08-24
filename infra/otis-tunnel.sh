#!/usr/bin/env bash
#
# otis-tunnel.sh - run this on YOUR OWN MACHINE, not on the server.
#
# Opens a reverse SOCKS5 proxy on the server (127.0.0.1:1080) whose traffic
# exits through this machine's internet connection.
#
# Why: mdocweb.state.mi.us (MDOC OTIS) sits behind Cloudflare, which returns a
# 403 "Attention Required" to the server's Helsinki IP. A home connection is not
# blocked, so the server borrows yours for the duration of a research session.
#
#   Usage:  ./otis-tunnel.sh            # start (foreground, Ctrl-C to stop)
#           ./otis-tunnel.sh --check    # start, verify OTIS answers, then hold
#           ./otis-tunnel.sh --stop     # kill a backgrounded tunnel
#
# Then, on the server:
#   curl --proxy socks5h://127.0.0.1:1080 https://mdocweb.state.mi.us/OTIS2/Results
#
set -euo pipefail

SERVER="${OTIS_TUNNEL_SERVER:-lbzgiu@46.62.129.153}"
PORT="${OTIS_TUNNEL_PORT:-1080}"
PIDFILE="${TMPDIR:-/tmp}/otis-tunnel.pid"
PROBE_URL="https://mdocweb.state.mi.us/OTIS2/Results"

log() { printf '\033[36m==>\033[0m %s\n' "$*"; }
err() { printf '\033[31mxxx\033[0m %s\n' "$*" >&2; }

stop_tunnel() {
    if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        kill "$(cat "$PIDFILE")" && rm -f "$PIDFILE"
        log "tunnel stopped"
    else
        log "no tunnel running (no live pid in $PIDFILE)"
        rm -f "$PIDFILE"
    fi
}

preflight() {
    # Remote dynamic forwarding (-R with no destination) landed in OpenSSH 7.6.
    local v
    v=$(ssh -V 2>&1 | sed -n 's/^OpenSSH_\([0-9]*\.[0-9]*\).*/\1/p')
    if [[ -n "$v" ]] && awk -v v="$v" 'BEGIN { exit !(v < 7.6) }'; then
        err "OpenSSH $v is too old; remote dynamic forwarding needs 7.6+"
        exit 1
    fi
    log "local OpenSSH ${v:-unknown}, ok"
}

# Ask the server to prove the tunnel works, from the server's side.
check_from_server() {
    log "waiting for the proxy to come up..."
    sleep 3
    local code
    code=$(ssh "$SERVER" \
        "curl -s -o /dev/null -w '%{http_code}' --max-time 25 \
         --proxy socks5h://127.0.0.1:$PORT '$PROBE_URL'" 2>/dev/null || echo "000")
    case "$code" in
        200) log "OTIS answered 200 through the tunnel. You're through." ;;
        403) err "still 403 - your home IP is blocked too, which would be a surprise." ;;
        000) err "no answer. Is the tunnel up? Is port $PORT already taken on the server?" ;;
        *)   err "unexpected status $code" ;;
    esac
}

main() {
    case "${1:-}" in
        --stop) stop_tunnel; exit 0 ;;
        --check) DO_CHECK=1 ;;
        "") DO_CHECK=0 ;;
        *) err "unknown argument: $1"; exit 2 ;;
    esac

    preflight

    if [[ "$DO_CHECK" == "1" ]]; then
        # Background it so we can query the server, then wait on it.
        ssh -N -T \
            -R "$PORT" \
            -o ServerAliveInterval=30 \
            -o ServerAliveCountMax=3 \
            -o ExitOnForwardFailure=yes \
            "$SERVER" &
        echo $! > "$PIDFILE"
        trap 'stop_tunnel' INT TERM
        check_from_server
        log "holding tunnel open - Ctrl-C to close"
        wait
    else
        log "SOCKS5 proxy -> $SERVER:127.0.0.1:$PORT (Ctrl-C to close)"
        exec ssh -N -T \
            -R "$PORT" \
            -o ServerAliveInterval=30 \
            -o ServerAliveCountMax=3 \
            -o ExitOnForwardFailure=yes \
            "$SERVER"
    fi
}

main "$@"

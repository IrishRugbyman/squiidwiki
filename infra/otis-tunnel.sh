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
# If the port is already held on the server (a tunnel whose window was closed
# while the network dropped it, so the server never saw it go), the script says
# which sshd holds it and offers to kill it. The server drops such sessions on
# its own after 2 minutes (ClientAliveInterval 30 x ClientAliveCountMax 4).
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

# Launched by double-click, the window closes on exit and takes the error with
# it: hold it open on failure. Ctrl-C (130) closes as asked.
pause_on_error() {
    local rc=$?
    if [[ $rc -ne 0 && $rc -ne 130 && -t 0 ]]; then
        read -r -p "Exit code $rc. Press Enter to close. " _ || true
    fi
}
trap pause_on_error EXIT

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

# ExitOnForwardFailure makes ssh quit at once when the port is taken, so look
# first. Prints "PID COMM" for the holder, "unknown" if it is taken but sudo
# cannot name it, nothing if it is free.
port_holder() {
    ssh -o ConnectTimeout=15 "$SERVER" \
        "pid=\$(sudo -n ss -Htlnp 'sport = :$PORT' 2>/dev/null \
             | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | head -n1)
         if [ -n \"\$pid\" ]; then echo \"\$pid \$(ps -o comm= -p \$pid)\"
         elif ss -Htln 'sport = :$PORT' | grep -q .; then echo unknown; fi"
}

free_port() {
    local holder pid comm ans
    holder=$(port_holder) || { err "cannot reach $SERVER"; exit 1; }
    [[ -z "$holder" ]] && return 0
    if [[ "$holder" == unknown ]]; then
        err "port $PORT is taken on the server and sudo cannot say by whom"
        err "retry in 2 minutes, or use another port: OTIS_TUNNEL_PORT=1081 $0"
        exit 1
    fi
    read -r pid comm <<<"$holder"
    if [[ "$comm" != sshd ]]; then
        err "port $PORT is held on the server by $comm (pid $pid), not a tunnel"
        err "use another port: OTIS_TUNNEL_PORT=1081 $0"
        exit 1
    fi
    err "port $PORT is held on the server by sshd pid $pid: an earlier tunnel,"
    err "dead unless another window still runs it"
    read -r -p "Kill it and continue? [y/N] " ans || ans=
    [[ "$ans" == [yY]* ]] || exit 1
    ssh "$SERVER" "sudo -n kill $pid" || { err "kill failed"; exit 1; }
    sleep 1
    [[ -z "$(port_holder)" ]] || { err "port $PORT still taken"; exit 1; }
    log "port $PORT freed"
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
    free_port

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
        ssh -N -T \
            -R "$PORT" \
            -o ServerAliveInterval=30 \
            -o ServerAliveCountMax=3 \
            -o ExitOnForwardFailure=yes \
            "$SERVER"
    fi
}

main "$@"

#!/usr/bin/env bash
# rrun - run a command on a remote machine, logging every run under a dated folder.
#
# Every invocation creates C:\Me\claude\run\YYYY-MM-DD\HHMMSS_<slug>\ on the
# remote host holding cmd.txt (what was asked), stdout.log, stderr.log,
# meta.json (host, times, exit code) and anything the command itself writes.
#
# Usage
#   rrun.sh [-h HOST] [-n NAME] [-d WORKDIR] [-b] -- <command...>
#   rrun.sh [-h HOST] [-n NAME] [-d WORKDIR] [-b] -s <script.py> [args...]
#
#   -h HOST     ssh alias or user@host           (default: homegpu)
#   -n NAME     slug for the run folder          (default: derived from command)
#   -d WORKDIR  cd here before running           (default: C:\Me\claude)
#   -s SCRIPT   upload this local file into the run folder and run it with $PY
#   -b          background: return immediately, log keeps filling
#   -l          list recent runs on the host and exit
#   -c N        show (cat) the logs of the Nth most recent run and exit
#
# Examples
#   rrun.sh -- nvidia-smi
#   rrun.sh -n sam3-fullframe -s bench.py --sam3 sam3.pt --out out
#   rrun.sh -b -n long-train -- cmd /c '"%PY%" train.py'
#   rrun.sh -l
#   rrun.sh -c 1
#
# The remote Python lives at a fixed path because `python` on PATH is a broken
# uv shim in non-interactive shells. -s uses that path directly; a `--` command
# gets it as %PY%, which needs a nested cmd /c to expand (see README).

set -uo pipefail

HOST="homegpu"
NAME=""
WORKDIR='C:\Me\claude'
SCRIPT=""
BACKGROUND=0
ACTION="run"
NTH=1
REMOTE_ROOT='C:\Me\claude\run'
REMOTE_PY='C:\Me\claude\.venv\Scripts\python.exe'

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h) HOST="$2"; shift 2 ;;
    -n) NAME="$2"; shift 2 ;;
    -d) WORKDIR="$2"; shift 2 ;;
    -s) SCRIPT="$2"; shift 2 ;;
    -b) BACKGROUND=1; shift ;;
    -l) ACTION="list"; shift ;;
    -c) ACTION="cat"; NTH="${2:-1}"; shift 2 ;;
    --) shift; break ;;
    *) break ;;
  esac
done

# ---------------------------------------------------------------- list / cat
#
# Listing and reading use plain cmd.exe (dir / type). Multi-line PowerShell does
# not survive the ssh hop and nested quoting breaks unpredictably.

runs_newest_first() {
  ssh "$HOST" "dir /b /s /ad \"$REMOTE_ROOT\" 2>nul" 2>/dev/null \
    | tr -d '\r' | grep -E '[0-9]{6}_' | sort -r
}

if [[ "$ACTION" == "list" ]]; then
  n=0
  while IFS= read -r d; do
    [[ -n "$d" ]] || continue
    n=$((n + 1))
    [[ $n -le 20 ]] || break
    meta=$(ssh -n "$HOST" "type \"$d\\meta.json\" 2>nul" 2>/dev/null | tr -d '\r')
    code=$(printf '%s' "$meta" | grep -o '"exit_code": *[0-9-]*' | grep -o '[0-9-]*$')
    rel=$(printf '%s' "$d" | sed 's|.*\\run\\||')
    printf '%2d  %-46s exit=%s\n' "$n" "$rel" "${code:-?}"
  done < <(runs_newest_first)
  [[ $n -gt 0 ]] || echo "no runs yet on $HOST"
  exit 0
fi

if [[ "$ACTION" == "cat" ]]; then
  d=$(runs_newest_first | sed -n "${NTH}p")
  [[ -n "$d" ]] || { echo "rrun: no run #$NTH on $HOST" >&2; exit 1; }
  echo "=== $d ==="
  for file in cmd.txt meta.json stdout.log stderr.log; do
    body=$(ssh "$HOST" "type \"$d\\$file\" 2>nul" 2>/dev/null | tr -d '\r')
    [[ -n "$body" ]] || continue
    echo
    echo "--- $file ---"
    printf '%s\n' "$body" | tail -60
  done
  echo
  echo "--- files in run folder ---"
  ssh "$HOST" "dir /b \"$d\" 2>nul" 2>/dev/null | tr -d '\r'
  exit 0
fi

# ---------------------------------------------------------------- run

if [[ -n "$SCRIPT" ]]; then
  [[ -f "$SCRIPT" ]] || { echo "rrun: no such script: $SCRIPT" >&2; exit 1; }
  SCRIPT_BASE="$(basename "$SCRIPT")"
  [[ -n "$NAME" ]] || NAME="${SCRIPT_BASE%.*}"
  CMD="\"$REMOTE_PY\" $SCRIPT_BASE $*"
else
  [[ $# -gt 0 ]] || { echo "rrun: nothing to run (use -- <command> or -s <script>)" >&2; exit 1; }
  CMD="$*"
  if [[ -z "$NAME" ]]; then
    NAME="$(printf '%s' "$1" | tr -cd '[:alnum:]._-' | tr '[:upper:]' '[:lower:]')"
    NAME="${NAME##*\\}"; NAME="${NAME%.exe}"; NAME="${NAME:-cmd}"
  fi
fi

NAME="$(printf '%s' "$NAME" | tr -cs '[:alnum:]._-' '-' | cut -c1-40)"
DAY="$(date +%Y-%m-%d)"
STAMP="$(date +%H%M%S)"
RUN_REL="${DAY}\\${STAMP}_${NAME}"
RUN_DIR="${REMOTE_ROOT}\\${RUN_REL}"

# Create the run folder and record what we were asked to do. A PowerShell
# here-string does not survive the ssh hop (its newlines are lost), so cmd.exe
# redirection writes cmd.txt instead.
ssh "$HOST" "mkdir \"$RUN_DIR\" 2>nul & (echo host: $HOST& echo workdir: $WORKDIR& echo command: $CMD) > \"$RUN_DIR\\cmd.txt\"" \
  >/dev/null 2>&1
ssh "$HOST" "if not exist \"$RUN_DIR\\cmd.txt\" exit 1" >/dev/null 2>&1 \
  || { echo "rrun: could not create run folder on $HOST" >&2; exit 1; }

# a script runs from inside its own run folder, so its outputs land there too
if [[ -n "$SCRIPT" ]]; then
  scp -q "$SCRIPT" "$HOST:$(printf '%s' "$RUN_DIR" | tr '\\' '/')/$SCRIPT_BASE" \
    || { echo "rrun: scp failed" >&2; exit 1; }
  EXEC_DIR="$RUN_DIR"
else
  EXEC_DIR="$WORKDIR"
fi

# cmd.exe wrapper: fixed PY, separate stdout/stderr, exit code into meta.json.
# ERRORLEVEL is written by cmd.exe redirection, not PowerShell — %VAR% does not
# expand inside a -Command string.
REMOTE=$(cat <<REMOTE_EOF
set "PY=$REMOTE_PY" & set "RUN=$RUN_DIR" & cd /d "$EXEC_DIR" & ($CMD) > "$RUN_DIR\\stdout.log" 2> "$RUN_DIR\\stderr.log" & (echo {"host": "$HOST", "run": "$RUN_REL", "workdir": "$EXEC_DIR", "exit_code": %ERRORLEVEL%, "finished": "%DATE% %TIME%"}) > "$RUN_DIR\\meta.json"
REMOTE_EOF
)

echo "rrun -> $HOST : run\\$RUN_REL"

if [[ $BACKGROUND -eq 1 ]]; then
  # `start /B cmd /c "<long quoted string>"` loses its quoting on the way
  # through ssh, so the command goes into a .cmd file that start then runs.
  BAT="$RUN_DIR\\run.cmd"
  ssh "$HOST" "(echo @echo off& echo $REMOTE) > \"$BAT\"" >/dev/null 2>&1
  ssh -n "$HOST" "start /B \"rrun-$NAME\" cmd /c \"$BAT\"" >/dev/null 2>&1
  echo "backgrounded. follow with:"
  echo "  $(basename "$0") -c 1"
  echo "  ssh $HOST \"type \\\"$RUN_DIR\\stdout.log\\\"\""
else
  ssh "$HOST" "$REMOTE"
  for file in stdout.log stderr.log meta.json; do
    body=$(ssh "$HOST" "type \"$RUN_DIR\\$file\" 2>nul" 2>/dev/null | tr -d '\r')
    [[ -n "$body" ]] || continue
    echo "--- $file ---"
    printf '%s\n' "$body" | tail -40
  done
fi

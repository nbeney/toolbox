#!/bin/bash

SESSION="todoloop"

# Kill any stale session with the same name so this is idempotent
tmux kill-session -t "${SESSION}" 2>/dev/null

# Launch terminal running tmux, with a title we can find later
gnome-terminal --window --title="TodoLoopTerm" -- tmux new-session -s "${SESSION}" \
    "/home/nicolas/scripts/task-loop.sh" \; \
    split-window -v -l 8 \; \
    select-pane -t 0 &

# Give the window time to appear
for i in $(seq 1 20); do
    WIN_ID=$(wmctrl -l | grep "TodoLoopTerm" | awk '{print $1}')
    [ -n "${WIN_ID}" ] && break
    sleep 0.3
done

if [ -n "${WIN_ID}" ]; then
    # Get full screen resolution
    read WIDTH HEIGHT <<< "$(xdotool getdisplaygeometry)"
    HALF_WIDTH=$((WIDTH / 2))

    # Unmaximize first, then position/resize to left half
    wmctrl -i -r "${WIN_ID}" -b remove,maximized_vert,maximized_horz
    wmctrl -i -r "${WIN_ID}" -e 0,0,0,"${HALF_WIDTH}","${HEIGHT}"
else
    echo "Could not find terminal window to position" >&2
fi

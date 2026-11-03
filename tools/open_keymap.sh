#!/bin/zsh
# 今のキーマップの図を keymap から作り直して Chrome で見せる（Alfred の「km」・Hyper+K から呼ぶ）。
# 図のタブ（題名「roBa 今のキーマップ」）がもう開いていれば、そのタブを読み直して前に出す（タブを増やさない）。
here="${0:A:h}"
page="$(/opt/homebrew/bin/python3 "$here/make_keymap_page.py")" || exit 1
url="$(/opt/homebrew/bin/python3 -c 'import sys,pathlib;print(pathlib.Path(sys.argv[1]).as_uri())' "$page")"

found="$(osascript - "$url" <<'EOF' 2>/dev/null
on run argv
  set u to item 1 of argv
  tell application "Google Chrome"
    if not running then return "no"
    repeat with w in windows
      set i to 0
      repeat with t in tabs of w
        set i to i + 1
        if (title of t is "roBa 今のキーマップ") and (URL of t starts with "file:") then
          tell t to reload
          set active tab index of w to i
          set index of w to 1
          activate
          return "yes"
        end if
      end repeat
    end repeat
  end tell
  return "no"
end run
EOF
)"
[[ "$found" == "yes" ]] || open -a "Google Chrome" "$url"

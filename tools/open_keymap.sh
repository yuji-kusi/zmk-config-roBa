#!/bin/zsh
# 今のキーマップの図を keymap から作り直して Chrome で見せる（Alfred の「km」・Hyper+K から呼ぶ）。
# 図のタブ（このファイルの URL、または題名「roBa 今のキーマップ」の file: のタブ）がもう開いていれば、そのタブを読み直して前に出す（タブを増やさない）。
# 図を作れなかったときは通知を出し、理由を ~/Library/Logs/roba-keymap-page.log に残す。
here="${0:A:h}"
log="$HOME/Library/Logs/roba-keymap-page.log"
py="$(command -v python3)"
[[ -x /opt/homebrew/bin/python3 ]] && py=/opt/homebrew/bin/python3
[[ -n "$py" ]] || py=/usr/bin/python3

if ! page="$("$py" "$here/make_keymap_page.py" 2>>"$log")"; then
  echo "$(date '+%F %T') 図を作れなかった（上の行が理由）" >>"$log"
  osascript -e 'display notification "理由は ~/Library/Logs/roba-keymap-page.log" with title "キーマップの図を作れませんでした"'
  exit 1
fi
url="$("$py" -c 'import sys,pathlib,unicodedata;print(pathlib.Path(unicodedata.normalize("NFC",sys.argv[1])).as_uri())' "$page")"

found="$(osascript - "$url" <<'OSA' 2>/dev/null
on run argv
  set u to item 1 of argv
  tell application "Google Chrome"
    if not running then return "no"
    repeat with w in windows
      set i to 0
      repeat with t in tabs of w
        set i to i + 1
        set tu to URL of t
        if tu is u or ((title of t is "roBa 今のキーマップ") and (tu starts with "file:")) then
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
OSA
)"
[[ "$found" == "yes" ]] || open -a "Google Chrome" "$url"

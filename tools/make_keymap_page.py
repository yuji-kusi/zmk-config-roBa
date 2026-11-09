#!/usr/bin/env python3
"""config/roBa.keymap を読んで、今のキーマップの図（docs/今のキーマップ.html）を作る。

呼び出すたびに keymap から作り直すので、図はいつも最新の keymap と同じになる。
知らないキーの書き方が出てきても止まらず、keymap の書き方のまま表示する。
使い方: python3 tools/make_keymap_page.py  （書き出した HTML のパスを 1 行出す）
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEYMAP = ROOT / "config" / "roBa.keymap"
LAYOUT = ROOT / "config" / "roBa.json"
OUT = ROOT / "docs" / "今のキーマップ.html"

# 図に出す面と、その名前（keymap の面の名前 → 表示名）。EIKANA・SLOW_DRAG は中身が下の面のままなので出さない
SHOW = [
    ("default_layer", "ふだんの面"),
    ("NUM_SYM", "数字・よく使う記号・矢印（Enter の長押し）"),
    ("SYM_F", "余った記号・F キー（B の長押し）"),
    ("ALFRED", "Alfred（D と F の同時押し → 次の 1 キー）"),
    ("MAC_MEDIA", "Mac 操作・メディア（Tab の長押し）"),
    ("SCROLL", "スクロール（押さえてボール）"),
    ("MOUSE", "マウス（ボールを動かした後 1.5 秒）"),
]
HIDE = {"EIKANA", "SLOW_DRAG"}
# 長押しの表示に使う面の短い名前（keymap の面の名前 → 短い名前）。ここに無い面は keymap の名前のまま出す
SHORT = {"EIKANA": "英かな", "NUM_SYM": "数字記号", "SYM_F": "記号F", "MAC_MEDIA": "Mac操作",
         "MOUSE": "マウス", "SCROLL": "スクロール", "SLOW_DRAG": "ゆっくり", "ALFRED": "Alfred"}
LAYER_ORDER = []  # 面の番号 → 面の名前（keymap に書かれた順。main で埋める）

KEYNAME = {
    "SPACE": "Space", "SPC": "Space", "BSPC": "delete", "DEL": "前方削除", "LEFT_SHIFT": "Shift",
    "RALT": "Option", "RCTRL": "Control", "RGUI": "Command", "LEFT_ALT": "Option", "LEFT_CONTROL": "Control",
    "LEFT_GUI": "Command", "LCMD": "Command", "TAB": "Tab", "ENTER": "Enter", "RET": "Enter", "BACKSPACE": "delete",
    "DELETE": "前方削除", "ESC": "Esc", "ESCAPE": "Esc", "MINUS": "-", "EQUAL": "=", "PLUS": "+",
    "SQT": "'", "SINGLE_QUOTE": "'", "DOUBLE_QUOTES": '"', "COMMA": ",", "DOT": ".", "PERIOD": ".",
    "SLASH": "/", "BACKSLASH": "\\", "SEMICOLON": ";", "COLON": ":", "GRAVE": "`", "TILDE": "~",
    "CARET": "^", "ASTERISK": "*", "QUESTION": "?", "EXCLAMATION": "!", "AMPERSAND": "&",
    "PIPE": "|", "HASH": "#", "AT_SIGN": "@", "DOLLAR": "$", "PERCENT": "%", "UNDERSCORE": "_",
    "LEFT_PARENTHESIS": "(", "RIGHT_PARENTHESIS": ")", "LEFT_BRACE": "{", "RIGHT_BRACE": "}",
    "LEFT_BRACKET": "[", "RIGHT_BRACKET": "]", "LESS_THAN": "<", "GREATER_THAN": ">",
    "LEFT_ARROW": "←", "RIGHT_ARROW": "→", "UP_ARROW": "↑", "DOWN_ARROW": "↓",
    "LEFT": "←", "RIGHT": "→", "UP": "↑", "DOWN": "↓",
    "LSHIFT": "Shift", "RSHIFT": "Shift", "LCTRL": "Control", "LALT": "Option", "LGUI": "Command",
    "PG_UP": "PageUp", "PAGE_DOWN": "PageDown", "LANG1": "かな", "LANG2": "英数",
    "C_BRI_DN": "明るさ −", "C_BRI_UP": "明るさ ＋", "C_VOL_DN": "音量 −", "C_VOL_UP": "音量 ＋",
    "C_MUTE": "消音", "C_PP": "再生・停止", "C_NEXT": "次の曲", "C_PREV": "前の曲",
}
MODS = {"LC": "⌃", "RC": "⌃", "LA": "⌥", "RA": "⌥", "LG": "⌘", "RG": "⌘", "LS": "⇧", "RS": "⇧"}
MOD_ORDER = "⌃⌥⇧⌘"

# Mac 側（BetterTouchTool・CleanShot・Alfred など）で意味を付けているキー。キーの書き方 → 表示
MEANING = {
    "⌃⌥⇧⌘1": "Notion", "⌃⌥⇧⌘2": "Orca", "⌃⌥⇧⌘F": "Finder", "⌃⌥⇧⌘4": "LINE",
    "⌃⌥⇧⌘5": "Chatwork", "⌃⌥⇧⌘6": "Chrome", "⌃⌥⇧⌘C": "Google カレンダー", "⌃⌥⇧⌘T": "Google ToDo",
    "⌥⇧←": "前の単語まで選ぶ", "⌃K": "行の終わりまで消す",
    "⌃⌘H": "撮影の履歴", "⌃⌥⇧⌘8": "窓を左半分", "⌃⌥⇧⌘9": "窓を最大化", "⌃⌥⇧⌘0": "窓を右半分",
    "⌃⌥⇧⌘-": "×", "⌃⌥⇧⌘=": "÷", "⌃⌥⇧⌘\\": "\\（半角）", "⌃⌥⇧⌘;": "/（半角）",
    "⌃⌘A": "範囲を撮影", "⌃⌘F": "全画面を撮影", "⌃⌘T": "画面の文字を写す", "⌃⌘O": "撮影メニュー",
    "⌥S": "スニペット", "⌘H": "クリップボード履歴", "⌥⇧⌘V": "書式なしで貼る",
    "⌃⇧Tab": "左のタブ", "⌃Tab": "右のタブ", "⌃←": "左のデスクトップ", "⌃→": "右のデスクトップ",
    "⌃↑": "Mission Control", "⌘M": "最小化", "⌘Space": "Alfred",
    "⌘Z": "取り消し", "⇧⌘Z": "やり直し", "⌘/": "声のモード", "⌘.": "音声入力",
    "⌘=": "拡大", "⌘-": "縮小", "⌘0": "元の大きさ",
}


def key_label(code: str) -> str:
    """LC(LA(LG(LS(N1)))) のような書き方を ⌃⌥⇧⌘1 にする。意味が分かっていれば意味にする"""
    code = code.strip()
    mods = []
    m = re.match(r"^([LR][CAGS])\((.*)\)$", code)
    while m:
        mods.append(MODS[m.group(1)])
        code = m.group(2).strip()
        m = re.match(r"^([LR][CAGS])\((.*)\)$", code)
    if re.fullmatch(r"N\d", code):
        base = code[1]
    elif code in KEYNAME:
        base = KEYNAME[code]
    else:
        base = code
    if not mods:
        return base
    sym = {"LSHIFT": "⇧", "RSHIFT": "⇧", "LCTRL": "⌃", "LALT": "⌥", "LGUI": "⌘"}
    if code in sym:  # 修飾キーだけの組み合わせ（⇧⌘ など）
        return "".join(sorted(set(mods + [sym[code]]), key=MOD_ORDER.index))
    text = "".join(sorted(set(mods), key=MOD_ORDER.index)) + base
    return MEANING.get(text, text)


def hold_label(code: str) -> str:
    if code in ("LSHIFT", "RSHIFT"):
        return "Shift"
    if code == "LGUI":
        return "Command"
    if code == "LCTRL":
        return "Control"
    if code == "LALT":
        return "Option"
    return key_label(code)


def layer_name(n: str) -> str:
    """面の番号（数字でなければ #define の名前のまま）を短い名前にする"""
    if n.isdigit() and int(n) < len(LAYER_ORDER):
        name = LAYER_ORDER[int(n)]
        return SHORT.get(name, name)
    return f"面 {n}"


def split_bindings(text: str):
    """bindings = < ... > の中身を &から始まる 1 つずつに分ける（括弧の中の空白は分けない）"""
    parts, cur, depth = [], "", 0
    for tok in re.findall(r"\S+", text):
        if tok.startswith("&") and depth == 0 and cur:
            parts.append(cur.strip())
            cur = ""
        cur += " " + tok
        depth += tok.count("(") - tok.count(")")
    if cur.strip():
        parts.append(cur.strip())
    return parts


def describe(binding: str):
    """1 つのキーを (軽押しの表示, 長押しの表示, 種類) にする。種類は図の色分けに使う"""
    parts = binding.split()
    name, args = parts[0][1:], parts[1:]
    hold_tap_kp = {"sct", "ghm", "lhs", "rhs", "tmt", "cmt", "vbs", "urd", "ekk", "eke", "mt"}
    hold_tap_layer = {"nlt", "blt", "tsc", "tlt", "lt"}
    if name == "trans":
        return "", "", "trans"
    if name == "none":
        return "", "", "none"
    if name == "kp" and args:
        return key_label(args[0]), "", "key"
    if name == "tap_once" and args:
        return key_label(args[0]), "", "key"
    if name in hold_tap_layer and len(args) >= 2:
        return key_label(args[1]), layer_name(args[0]), "layer"
    if name in ("ekk", "eke") and len(args) >= 2:
        return "英かな", layer_name(args[0]), "layer"
    if name in hold_tap_kp and len(args) >= 2:
        tap = "英かな" if name in ("ekk", "eke") else key_label(args[1])
        return tap, hold_label(args[0]), "hold"
    if name == "ghn" and args:
        return "", hold_label(args[0]), "hold"
    if name == "mo" and args:
        return f"押さえて{layer_name(args[0])}", "", "layer"
    if name == "tog" and args:
        return f"{layer_name(args[0])} 入切", "", "layer"
    if name == "dsw" and len(args) >= 2:
        return key_label(args[1]), "アプリ切替", "hold"
    if name == "app_switch":
        return "アプリ切替", "", "key"
    if name.startswith("str_"):
        return name[4:], "", "alfred"
    if name == "slow_drag":
        return "左クリック", "", "mouse"
    if name == "mkp" and args:
        return {"MB1": "左クリック", "MB2": "右クリック", "MB3": "中クリック"}.get(args[0], args[0]), "", "mouse"
    if name == "mmv" and args:
        return {"MOVE_UP": "カーソル↑", "MOVE_DOWN": "カーソル↓", "MOVE_LEFT": "カーソル←",
                "MOVE_RIGHT": "カーソル→"}.get(args[0], args[0]), "", "mouse"
    if name == "msc" and args:
        # Mac のナチュラルなスクロールに合わせて逆に割り当てているので、実際に動く向きで出す
        return {"SCRL_DOWN": "上へ送る", "SCRL_UP": "下へ送る", "SCRL_RIGHT": "左へ送る",
                "SCRL_LEFT": "右へ送る"}.get(args[0], args[0]), "", "mouse"
    if name == "bt" and args:
        if args[0] == "BT_SEL" and len(args) > 1:
            return (f"BT {int(args[1]) + 1}" if args[1].isdigit() else f"BT {args[1]}"), "", "key"
        return " ".join(args), "", "key"
    return binding.lstrip("&"), "", "key"


def read_layers(src: str):
    """keymap { ... } の中の面を、書かれた順に {面の名前: [キー…]} で返す。
    display-name などが bindings より先にあっても読む。<…>, <…> と分けて書いても 1 本につなぐ"""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    src = re.sub(r"//[^\n]*", "", src)
    m = re.search(r"\bkeymap\s*\{", src)
    if not m:
        raise SystemExit("keymap { が見つからない")
    km = src[m.end():]
    layers = {}
    for lm in re.finditer(r"(\w+)\s*\{([^{}]*)\}", km):
        bm = re.search(r"\bbindings\s*=\s*((?:<[^>]*>\s*,?\s*)+);", lm.group(2))
        if bm:
            body = " ".join(re.findall(r"<([^>]*)>", bm.group(1)))
            layers[lm.group(1)] = split_bindings(body)
    return layers


def entry_keys(base, layer_no):
    """ふだんの面で、その面に入るキーの位置"""
    out = set()
    for i, b in enumerate(base):
        p = b.split()
        n = p[0][1:]
        if n in ("mo", "nlt", "blt", "tsc", "tlt", "lt", "sl", "to", "ekk") and len(p) > 1 and p[1] == str(layer_no):
            out.add(i)
    return out


def render_board(bindings, base, layout, held):
    unit = 66
    gap = 4
    xs = [k["x"] for k in layout]
    ys = [k["y"] for k in layout]
    width = (max(xs) + 1) * unit
    height = (max(ys) + 1.6) * unit
    keys = []
    for i, k in enumerate(layout):
        b = bindings[i] if i < len(bindings) else "&none"
        tap, hold, kind = describe(b)
        ghost = ""
        if kind == "trans" and base is not bindings:
            ghost = describe(base[i] if i < len(base) else "&none")[0]
        cls = f"k {kind}"
        if i in held:
            if kind in ("trans", "none"):  # 押さえているだけのキー
                cls += " held"
                tap, ghost, hold = ghost or "押さえる", "", "押さえる"
            else:  # 別の入口からこの面に入ったときは、このキーが働く
                cls += " held2"
                hold = "ここでも入る"
        style = f"left:{k['x'] * unit:.1f}px;top:{k['y'] * unit:.1f}px;width:{unit - gap}px;height:{unit - gap}px;"
        if "r" in k and "rx" in k and "ry" in k:
            ox = (k["rx"] - k["x"]) * unit
            oy = (k["ry"] - k["y"]) * unit
            style += f"transform-origin:{ox:.1f}px {oy:.1f}px;transform:rotate({k['r']}deg);"
        size = "s" if len(tap) > 5 else ""
        body = f'<span class="t {size}">{html.escape(tap)}</span>' if tap else ""
        if ghost and not tap:
            body = f'<span class="g">{html.escape(ghost)}</span>'
        if hold:
            body += f'<span class="h">{html.escape(hold)}</span>'
        title = html.escape(b)
        keys.append(f'<div class="{cls}" style="{style}" title="{title}">{body}</div>')
    return (f'<div class="wrap"><div class="board" style="width:{width:.0f}px;height:{height:.0f}px">'
            + "".join(keys) + "</div></div>")


def main():
    src = KEYMAP.read_text(encoding="utf-8")
    layout = json.loads(LAYOUT.read_text(encoding="utf-8"))["layouts"]["default_layout"]["layout"]
    layers = read_layers(src)
    if not layers:
        raise SystemExit("keymap に面が見つからない")
    LAYER_ORDER[:] = list(layers)
    base_name = LAYER_ORDER[0]  # いちばん上に書いた面がふだんの面
    base = layers[base_name]
    try:
        mtime = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%cd", "--date=format:%Y-%m-%d %H:%M",
                                "--", "config/roBa.keymap"], capture_output=True, text=True).stdout.strip()
    except OSError:
        mtime = ""
    dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", "config/roBa.keymap"],
                           capture_output=True, text=True).stdout.strip()
    when = f"{mtime} のコミット" if mtime else "日時不明"
    if dirty:
        when += "＋まだコミットしていない書き換え"
    warns = []
    titles = dict(SHOW)
    order = [k for k, _ in SHOW if k in layers] + [k for k in layers if k not in titles and k not in HIDE]
    sections = []
    for key in order:
        if len(layers[key]) != len(layout):
            warns.append(f"{key} の面はキーが {len(layers[key])} 個（配置は {len(layout)} 個）。図がずれている")
        held = set() if key == base_name else entry_keys(base, LAYER_ORDER.index(key))
        board = render_board(layers[key], base, layout, held)
        title = titles.get(key, key)
        sections.append(f'<section><h2>{html.escape(title)}</h2>{board}</section>')
    warn_html = "".join(f'<p class="warn">{html.escape(w)}</p>' for w in warns)
    page = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>roBa 今のキーマップ</title>
<style>
:root{{--bg:#1e1e1e;--panel:#2c2c2c;--line:#3d3d3d;--text:#e8e8e8;--sub:#a8a8a8;--blue:#1473e6;--blue2:#3b82f6}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,"Hiragino Sans",sans-serif;line-height:1.4}}
main{{max-width:1000px;margin:0 auto;padding:20px 16px 48px}}
h1{{font-size:22px;margin:0 0 4px}}
h2{{font-size:17px;margin:26px 0 8px;color:var(--blue2)}}
.meta{{color:var(--sub);font-size:13px;margin:0 0 6px}}
.legend{{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;color:var(--sub);margin:8px 0 0}}
.legend i{{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:4px;vertical-align:-1px;border:2px solid}}
.wrap{{overflow-x:auto}}
.board{{position:relative;margin:0 auto}}
.k{{position:absolute;background:var(--panel);border:1px solid var(--line);border-radius:8px;display:flex;flex-direction:column;
  justify-content:center;align-items:center;text-align:center;padding:2px 3px;overflow:hidden}}
.k .t{{font-size:15px;font-weight:600;color:#fff;line-height:1.15;overflow-wrap:anywhere}}
.k .t.s{{font-size:11px}}
.k .h{{font-size:10px;color:#8fb8ff;margin-top:2px;line-height:1.1}}
.k .g{{font-size:11px;color:#5c5c5c}}
.k.trans{{background:transparent;border-style:dashed;border-color:#333}}
.k.none{{background:transparent;border-style:dotted;border-color:#444}}
.k.layer{{border:2px solid var(--blue2)}}
.k.alfred{{background:#22324a;border-color:#2f4a70}}
.k.mouse{{border:2px dashed #93c5fd}}
.k.held{{background:var(--blue);border-color:var(--blue);border-style:solid}}.k.held .h{{color:#dbe8ff}}.k.held .t{{color:#fff}}
.k.held2{{border:2px solid var(--blue);box-shadow:inset 0 0 0 2px #1473e655}}.k.held2 .h{{color:#93c5fd}}
.warn{{background:#3a2424;border:1px solid #a14b4b;border-radius:6px;padding:8px 12px;font-size:14px;margin:8px 0}}
</style></head><body><main>
<h1>roBa 今のキーマップ</h1>
<p class="meta">config/roBa.keymap（{when}）から、呼び出したときに作った図。大きい字が軽く押したとき、小さい字が長押し。キーに指を乗せると keymap の書き方が出る。スクロールの向きは Mac のナチュラルなスクロールを前提にした表示（左右は実機で未確認）。</p>
<div class="legend"><span><i style="border-color:#3b82f6"></i>長押しで面に入る</span><span><i style="background:#22324a;border-color:#2f4a70"></i>Alfred の言葉（Alfred を開いて打つ）</span>
<span><i style="border-color:#93c5fd;border-style:dashed"></i>マウス・スクロール</span><span><i style="background:#1473e6;border-color:#1473e6"></i>その面に入るために押さえるキー</span>
<span><i style="border-color:#1473e6"></i>そのキーでも入れる（別の入口から入ったときは書いてある働き）</span>
<span><i style="border-color:#444;border-style:dashed"></i>ふだんの面のまま（薄い字）</span></div>
{warn_html}
{''.join(sections)}
</main></body></html>
"""
    OUT.write_text(page, encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    sys.exit(main())

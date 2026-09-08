# -*- coding: utf-8 -*-
"""住まいのしおり 掲示物（A4に3棟）を組み立てる

・1面＝80 × 129.4mm（黄金比 1:1.618）
・QRは SVG をHTMLに直接埋め込む＝ベクターなので印刷しても解像度の限界が無い
・棟ごとに「しおりに載っている項目」が違う（Ⅲだけカードキーがある）
"""
import io, os, re, segno

SP = r"C:/Users/disc3/AppData/Local/Temp/claude/C--googleDrive-H-/e301efc2-cf73-4b5b-895f-3c19bc4cd557/scratchpad/mock"
BASE = "https://kabufamille.github.io/sumai-shiori/"

# 「一例でいい」（けんじ 2026-09-08）＝全部を並べず2行にまとめる。
# 棟でページ数が違っても文面を分けずに済むよう、末尾は「など」で受ける。
EXAMPLE = "ゴミの出し方、共用部分の使い方、<br>夜間・休日の緊急連絡先　など"
BUILDINGS = [
    dict(slug="famille3", name="ファミーユ豊玉Ⅲ", pos="left:25mm;top:19.1mm"),
    dict(slug="famille2", name="ファミーユ豊玉Ⅱ", pos="left:105mm;top:19.1mm"),
    dict(slug="laville", name="ラヴィール豊玉", pos="left:25mm;top:148.5mm"),
]


def qr_svg(url):
    """QRをベクターで作る。元と同じ訂正レベルM。余白は3モジュール（枠の白地が静穏帯を補う）。

    ⚠️ segnoのSVGには viewBox が無い。width/height を外すだけだと座標系が決まらず、
       CSSで大きさを指定しても拡大されずに左上へ小さく描かれる（2026-09-08に実際に起きた）。
       必ず viewBox を足すこと。
    """
    q = segno.make(url, error="m")
    w, h = q.symbol_size(scale=1, border=3)
    buf = io.BytesIO()
    q.save(buf, kind="svg", scale=1, border=3, xmldecl=False, svgns=True, nl=False)
    svg = buf.getvalue().decode("utf-8")
    svg = re.sub(r'\swidth="[^"]*"', "", svg, count=1)
    svg = re.sub(r'\sheight="[^"]*"', "", svg, count=1)
    return svg.replace(
        "<svg ",
        '<svg class="qr" viewBox="0 0 %d %d" preserveAspectRatio="xMidYMid meet" ' % (w, h), 1)


CSS = """
  @page{ size:A4; margin:0; }
  :root{
    --brown:#7d6a55; --brown-d:#5e4f3f; --line:#e3ded6;
    --sub:#6b6357; --ink:#2b2b2b; --tint:#f7f4ef;
  }
  *{box-sizing:border-box;margin:0;padding:0;
    -webkit-print-color-adjust:exact;print-color-adjust:exact;}
  html,body{width:210mm;height:297mm;}
  body{font-family:"Noto Sans JP","Yu Gothic","Meiryo",sans-serif;background:#fff;}
  .mincho{font-family:"Noto Serif JP","Yu Mincho","YuMincho",serif;}

  .sheet{width:210mm;height:297mm;position:relative;}
  .cut{position:absolute;pointer-events:none;}
  .cut.v{top:0;height:297mm;width:0;border-left:.3pt dashed #cfcac2;}
  .cut.h{left:0;width:210mm;height:0;border-top:.3pt dashed #cfcac2;}

  /* 1面＝80 × 129.4mm（黄金比） */
  .card{
    position:absolute;width:80mm;height:129.4mm;padding:6.5mm 7mm 5mm;
    display:flex;flex-direction:column;text-align:center;background:#fff;
    overflow:hidden;   /* 面の外へはみ出させない */
  }
  /* 🔴 flex:none が無いと、高さが足りないとき黙って0まで潰される（2026-09-08に実際に起きた） */
  .bar{flex:none;width:12mm;height:1.2mm;background:var(--brown);border-radius:1mm;margin:0 auto 2.4mm;}
  h1{flex:none;font-size:14.5pt;letter-spacing:.16em;color:var(--brown-d);font-weight:500;
     text-indent:.16em;line-height:1.35;white-space:nowrap;}
  .sub{flex:none;font-size:7.5pt;letter-spacing:.13em;color:var(--sub);margin-top:1.4mm;text-indent:.13em;}

  .qrbox{
    flex:none;margin:2.6mm auto 0;width:32mm;height:32mm;padding:1.8mm;background:#fff;
    border:.6pt solid var(--line);border-radius:2.6mm;
  }
  .qrbox svg.qr{width:100%;height:100%;display:block;}   /* ベクター＝拡大してもくっきり */

  .scan{flex:none;font-size:8pt;color:var(--ink);margin-top:2mm;line-height:1.5;}
  .scan b{font-weight:700;}

  /* しおりに載っている項目 */
  .items{
    flex:none;margin:2.4mm 0 0;padding:1.8mm 2.5mm 2mm;
    background:var(--tint);border-radius:2.4mm;
  }
  .items .cap{font-size:6.8pt;letter-spacing:.1em;color:var(--sub);margin-bottom:1.2mm;}
  .items .ex{font-size:8pt;line-height:1.7;color:var(--ink);}

  /* 写真の帯（左右の余白いっぱいまで届かせる） */
  .strip{flex:none;margin:3.2mm -7mm 0;height:16mm;overflow:hidden;}
  .strip img{width:100%;height:100%;object-fit:cover;object-position:center 42%;display:block;}

  .foot{flex:none;margin-top:auto;padding-top:2.4mm;}
  .bldname{
    display:inline-block;font-size:10.5pt;font-weight:700;color:#fff;background:var(--brown);
    padding:2.2mm 6mm;border-radius:99mm;letter-spacing:.05em;white-space:nowrap;
  }
  .tel{font-size:6.5pt;color:var(--sub);margin-top:2mm;letter-spacing:.03em;white-space:nowrap;}
"""


def card(b):
    return """  <div class="card" style="%s">
    <div class="bar"></div>
    <h1 class="mincho">住まいのしおり</h1>
    <p class="sub">くらしのご案内</p>
    <div class="qrbox">%s</div>
    <p class="scan">スマートフォンのカメラを<b>かざすだけ</b></p>
    <div class="items">
      <p class="cap">こんなことが載っています</p>
      <p class="ex">%s</p>
    </div>
    <div class="strip"><img src="room.jpg" alt=""></div>
    <div class="foot">
      <span class="bldname">%s</span>
      <p class="tel">お問い合わせ　邑ハウジング　03-3948-0101</p>
    </div>
  </div>
""" % (b["pos"], qr_svg(BASE + b["slug"] + "/"), EXAMPLE, b["name"])


html = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>住まいのしおり 掲示物 3棟</title>
<style>%s</style>
</head>
<body>
<div class="sheet">
  <div class="cut v" style="left:25mm"></div>
  <div class="cut v" style="left:105mm"></div>
  <div class="cut v" style="left:185mm"></div>
  <div class="cut h" style="top:19.1mm"></div>
  <div class="cut h" style="top:148.5mm"></div>
  <div class="cut h" style="top:277.9mm"></div>

%s
  <!-- 右下は余白 -->
</div>
</body>
</html>
""" % (CSS, "".join(card(b) for b in BUILDINGS))

io.open(os.path.join(SP, "poster_3tou.html"), "w", encoding="utf-8").write(html)
print("poster_3tou.html を作成（QRはSVG・項目リストつき）")
for b in BUILDINGS:
    print("  %-9s %s" % (b["slug"], b["name"]))

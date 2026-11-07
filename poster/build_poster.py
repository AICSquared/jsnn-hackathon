"""Fill the CAES 48x36 poster template with the JSNN hackathon project. Usage: python build_poster.py out.pptx"""
import csv, json, sys
from pathlib import Path
from PIL import Image
from pptx import Presentation
from pptx.chart.data import XyChartData, CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_MARKER_STYLE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt
from lxml import etree

HERE = Path(__file__).parent
A = HERE / "assets"
REPO = HERE.parent
NAVY, GOLD, INK, MUTED, TINT, WHITE, CREAM = "004684", "FDB927", "1F2933", "52606D", "EDF2F8", "FFFFFF", "FFF4D6"
TWIN = ["9DB4CC", "E07B39", "2E8B57"]
BODY, SMALL, HEAD = 24, 19, 40
FONT = "Arial"


def rgb(h):
    return RGBColor.from_string(h)


prs = Presentation(HERE / "caes_poster_template_36x48.pptx")
s = prs.slides[0]

# ---------------------------------------------------------------- title block (keep the template's runs/styles)
title_box = next(sh for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.startswith("Title"))
paras = title_box.text_frame.paragraphs
new = ["From Living Cells to Moving Robots: AI-Agent Teamwork Across Three Bioengineering Challenges",
       "Alex Williams and Brandon Townsend",
       "North Carolina A&T State University  ·  JSNN Hackathon, November 7, 2026  ·  2nd place, Stage 1"]
for p, text in zip(paras, new):
    p.runs[0].text = text
    for r in p.runs[1:]:
        r.text = ""
paras[0].runs[0].font.size = Pt(72)
paras[1].runs[0].font.size = Pt(48)
paras[2].runs[0].font.size = Pt(36)
title_box.left, title_box.top, title_box.width, title_box.height = Inches(6.2), Inches(0.55), Inches(39.6), Inches(4.6)
title_box.text_frame.word_wrap = True


# ---------------------------------------------------------------- helpers
def textbox(x, y, w, h, paras, size=BODY, color=INK, anchor=MSO_ANCHOR.TOP, name=None):
    """paras: list of str | (text, opts) | [(text, opts), ...]; opts: bold, italic, color, size, bullet, align, after."""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ("left", "right", "top", "bottom"):
        setattr(tf, f"margin_{side}", Inches(0.05))
    first = True
    for item in paras:
        if isinstance(item, str):
            runs, popt = [(item, {})], {}
        elif isinstance(item, tuple):
            runs, popt = [item], item[1]
        else:
            runs, popt = item, (item[0][1] if item else {})
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = popt.get("align", PP_ALIGN.LEFT)
        p.space_after = Pt(popt.get("after", 8))
        if popt.get("bullet"):
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", str(Inches(0.38)))
            pPr.set("indent", str(-Inches(0.3)))
            bf_ = etree.SubElement(pPr, qn("a:buFont")); bf_.set("typeface", "Arial")
            bc = etree.SubElement(pPr, qn("a:buChar")); bc.set("char", "•")
        for text, ro in runs:
            r = p.add_run()
            r.text = text
            f = r.font
            f.name = FONT
            f.size = Pt(ro.get("size", size))
            f.bold = ro.get("bold", False)
            f.italic = ro.get("italic", False)
            f.color.rgb = rgb(ro.get("color", color))
    return tb


def header(x, y, w, text, name):
    sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(1.0))
    sh.name = name
    sh.adjustments[0] = 0.25
    sh.fill.solid(); sh.fill.fore_color.rgb = rgb(NAVY)
    sh.line.fill.background()
    sh.shadow.inherit = False
    tf = sh.text_frame
    tf.margin_left = Inches(0.3)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
    r = p.add_run(); r.text = text
    r.font.name = FONT; r.font.size = Pt(HEAD); r.font.bold = True; r.font.color.rgb = rgb(WHITE)
    return y + 1.25


def card(x, y, w, h, name, fill=TINT):
    sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.name = name
    sh.adjustments[0] = 0.06
    sh.fill.solid(); sh.fill.fore_color.rgb = rgb(fill)
    sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def picture(path, x, y, w=None, h=None, name=None, alt=""):
    pic = s.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w) if w else None, Inches(h) if h else None)
    if name:
        pic.name = name
    pic._element.nvPicPr.cNvPr.set("descr", alt)
    return pic


def style_axis(ax, title=None, size=16, fmt=None, minv=None, maxv=None, major=None):
    ax.has_major_gridlines = False
    ax.tick_labels.font.size = Pt(size); ax.tick_labels.font.name = FONT
    ax.tick_labels.font.color.rgb = rgb(MUTED)
    ax.format.line.color.rgb = rgb("B8C2CC")
    if fmt:
        ax.tick_labels.number_format = fmt; ax.tick_labels.number_format_is_linked = False
    if minv is not None:
        ax.minimum_scale = minv
    if maxv is not None:
        ax.maximum_scale = maxv
    if major is not None:
        ax.major_unit = major
    if title:
        ax.has_title = True
        ax.axis_title.text_frame.text = title
        rr = ax.axis_title.text_frame.paragraphs[0].runs[0]
        rr.font.size = Pt(size); rr.font.name = FONT; rr.font.bold = False; rr.font.color.rgb = rgb(MUTED)


def chart_title(chart, text, size=26):
    chart.has_title = True
    chart.chart_title.text_frame.text = text
    rr = chart.chart_title.text_frame.paragraphs[0].runs[0]
    rr.font.size = Pt(size); rr.font.bold = True; rr.font.name = FONT; rr.font.color.rgb = rgb(INK)


def legend(chart, size=18):
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.legend.include_in_layout = False
    chart.legend.font.size = Pt(size); chart.legend.font.name = FONT; chart.legend.font.color.rgb = rgb(INK)


# ---------------------------------------------------------------- data
dt = json.load(open(A / "dt_results.json"))
bf = json.load(open(A / "bf_summary.json"))["summary"]
met = json.load(open(A / "metrics.json"))
trig = list(csv.DictReader(open(REPO / "robotics/evidence/arm/obj5_run1_cell_medium_vial_trigger_log.csv")))

TOP, BOTTOM = 5.55, 33.55
GAP = 0.6
CW = (47.0 - 1.0 - 3 * GAP) / 4
X = [1.0 + i * (CW + GAP) for i in range(4)]

# ================================================================= COLUMN 1: abstract, approach, AI
x, y = X[0], TOP
y = header(x, y, CW, "Abstract", "hdr_abstract")
textbox(x, y, CW, 4.4, [
    "In one day, a two-person team used AI coding agents to solve three bioengineering challenges, each delivered as a "
    "reproducible notebook:",
    [("Digital Twin: ", {"bold": True, "bullet": True}), ("a physics simulation of 248 real E. coli cells that predicts colony "
      "growth within 4.8% (count) and 1.1% (area).", {})],
    [("Biofilm dispersion: ", {"bold": True, "bullet": True}), ("image analysis tracking 8 colonies across 17 microscope frames, "
      "independently verified to 10⁻¹² px.", {})],
    [("Robotics that Responds: ", {"bold": True, "bullet": True}), ("live bioreactor optical density (OD) drives a 6-axis robot arm; "
      "every threshold crossing triggered exactly one response.", {})],
], name="txt_abstract")
y += 4.55

y = header(x, y, CW, "How We Worked", "hdr_approach")
labels = [("Humans", "decide, run hardware, approve merges"), ("AI agents", "read docs & source, write & test code"),
          ("Message board", "GitHub issue: ACK · DONE · BLOCKED · STATUS"), ("GitHub", "issue → branch → pull request → merge")]
bh, by = 0.95, y
for i, (a, b) in enumerate(labels):
    sh = card(x, by, CW, bh, f"flow_{i}", fill=CREAM if i % 2 == 0 else TINT)
    tf = sh.text_frame; tf.margin_left = Inches(0.3); tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
    r1 = p.add_run(); r1.text = a + "   "; r1.font.bold = True; r1.font.size = Pt(22); r1.font.name = FONT; r1.font.color.rgb = rgb(NAVY)
    r2 = p.add_run(); r2.text = b; r2.font.size = Pt(19); r2.font.name = FONT; r2.font.color.rgb = rgb(INK)
    if i < len(labels) - 1:
        ar = s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(x + CW / 2 - 0.22), Inches(by + bh + 0.03), Inches(0.44), Inches(0.3))
        ar.fill.solid(); ar.fill.fore_color.rgb = rgb(GOLD); ar.line.fill.background(); ar.name = f"flow_arrow_{i}"
    by += bh + 0.36
y = by + 0.05
textbox(x, y, CW, 3.4, [
    [("One challenge per person, in parallel. ", {"bold": True}), ("Each agent worked only in its owner's folders; "
      "the agents coordinated only through the board and asked for a handoff before touching the other's files.", {})],
    [("Humans stayed in charge: ", {"bold": True}), ("every merge, email and robot motion needed a human \"go\".", {})],
], size=22, name="txt_approach")
y += 3.55

y = header(x, y, CW, "AI by the Numbers", "hdr_ai")
t = met["chat"]["totals"]
active_h = sum(ss["active_minutes"] for ss in met["chat"]["sessions"]) / 60
stats = [(f"{active_h:.1f} h", "active AI session time"), (f"{t['human_prompts']}", "human prompts (Alex)"),
         (f"{t['tool_calls']}", "agent tool calls"), (f"{met['git']['commits']}", "commits, 2 authors"),
         (f"{met['board']['posts']}", "agent board messages"), (f"{t['output_tokens'] / 1000:.0f}k", "output tokens")]
sw, sh_ = (CW - 0.4) / 3, 1.75
for i, (big, small) in enumerate(stats):
    cx, cy = x + (i % 3) * (sw + 0.2), y + (i // 3) * (sh_ + 0.2)
    card(cx, cy, sw, sh_, f"stat_bg_{i}")
    textbox(cx, cy + 0.12, sw, 0.95, [(big, {"bold": True, "size": 44, "color": NAVY, "align": PP_ALIGN.CENTER, "after": 0})], name=f"stat_{i}")
    textbox(cx, cy + 1.07, sw, 0.6, [(small, {"size": 17, "color": MUTED, "align": PP_ALIGN.CENTER, "after": 0})], name=f"stat_lbl_{i}")
y += 2 * sh_ + 0.4 + 0.1
textbox(x, y, CW, BOTTOM - y, [
    [("Where the agents helped most", {"bold": True, "color": NAVY})],
    [("Diagnosed a Colab-only crash ", {"bold": True, "bullet": True, "size": 21}), ("to one package version (plum-dispatch 2.9.0) "
      "from two pasted package lists.", {"size": 21})],
    [("Read source code when docs were down: ", {"bold": True, "bullet": True, "size": 21}), ("Pioreactor API routes, the arm's "
      "socket server.", {"size": 21})],
    [("Caught each other's mistakes: ", {"bold": True, "bullet": True, "size": 21}), ("a missing GIF overlay, a stale \"newest\" "
      "reading, README errors.", {"size": 21})],
    [("Working alongside the AI", {"bold": True, "color": NAVY})],
    [("It asked before acting: ", {"bold": True, "bullet": True, "size": 21}), ("which challenge, how to split work, the deliverable "
      "format, and a \"go\" before every merge or robot move.", {"size": 21})],
    [("It sent us to do what only people could: ", {"bold": True, "bullet": True, "size": 21}), ("run code in Colab and paste "
      "errors, power on the reactor's leader unit, insert vials, film the arm.", {"size": 21})],
], size=21, name="txt_ai_help")

# ================================================================= COLUMN 2: Digital Twin
x, y = X[1], TOP
y = header(x, y, CW, "1 · Digital Twin of an E. coli Colony", "hdr_dt")
textbox(x, y, CW, 2.8, [
    [("Task: ", {"bold": True}), ("from the first microscope frame (248 cells in a 34 × 60 µm chamber) and 65 min of real data, "
      "predict cell count and area for the next 70 hidden minutes.", {})],
    [("Method: ", {"bold": True}), ("Vivarium + Viva-munk 2D physics; each rule ", {}), ("measured from tracking data", {"bold": True}),
     (" and added one at a time; 3 random seeds each.", {})],
], name="txt_dt_task")
y += 2.85

rules = [("1  Growth", f"exponential (log-length fits, 369 cells): doubling ≈ {dt['doubling_min']:.0f} min"),
         ("2  Division", f"adder rule: Δ ≈ {dt['delta']:.2f} µm ({dt['L_div']:.2f} µm at division, {dt['L_birth']:.2f} µm at birth)"),
         ("3  Position", f"+{dt['x_slope'] * 100:.1f}% growth per µm toward the open side (weak, r = 0.08)")]
for i, (a, b) in enumerate(rules):
    card(x, y, CW, 1.2, f"rule_bg_{i}")
    textbox(x + 0.15, y + 0.05, CW - 0.3, 1.1, [[(a + "   ", {"bold": True, "color": NAVY, "size": 22}), (b, {"size": 20})]],
            anchor=MSO_ANCHOR.MIDDLE, name=f"rule_{i}")
    y += 1.35
y += 0.15


def dt_chart(col, title, yy, h, name):
    cd = XyChartData()
    for nm, res in dt["results"].items():
        ser = cd.add_series({"1: grow": "Twin: rule 1", "1+2: grow, divide": "Twin: rules 1+2", "1+2+3: + position": "Twin: rules 1+2+3"}[nm])
        base = res[col][0]
        for tm, v in zip(res["time_min"], res[col]):
            ser.add_data_point(tm, v / base)
    real = dt["real"]
    ser = cd.add_series("Real cells")
    for tm, v in zip(real["time_min"], real[col]):
        ser.add_data_point(tm, v / real[col][0])
    hid = cd.add_series("Hidden →")
    hid.add_data_point(67.5, 0.95); hid.add_data_point(67.5, 1.65)
    gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS, Inches(x), Inches(yy), Inches(CW), Inches(h), cd)
    gf.name = name
    ch = gf.chart
    chart_title(ch, title)
    legend(ch, 18)
    for i, sr in enumerate(ch.series):
        sr.smooth = False
        if i < 3:
            sr.format.line.color.rgb = rgb(TWIN[i]); sr.format.line.width = Pt(3.5)
            sr.marker.style = XL_MARKER_STYLE.NONE
        elif sr.name == "Real cells":
            sr.format.line.fill.background()
            sr.marker.style = XL_MARKER_STYLE.CIRCLE; sr.marker.size = 10
            sr.marker.format.fill.solid(); sr.marker.format.fill.fore_color.rgb = rgb(NAVY)
            sr.marker.format.line.color.rgb = rgb(NAVY)
        else:
            sr.format.line.color.rgb = rgb("9AA5B1"); sr.format.line.width = Pt(2.25); sr.format.line.dash_style = 4
            sr.marker.style = XL_MARKER_STYLE.NONE
    style_axis(ch.category_axis, "time (min)", 19, minv=0, maxv=135, major=15)
    style_axis(ch.value_axis, "relative to t = 0", 19, fmt="0.0", minv=0.95, maxv=1.65, major=0.1)
    return yy + h


y = dt_chart("cells", "(a) Cell count: twin vs real", y, 6.2, "chart_dt_count") + 0.2
y = dt_chart("total_area_um2", "(b) Total cell area: twin vs real", y, 6.2, "chart_dt_area") + 0.25

errs = dt["errors"]
gtab = s.shapes.add_table(len(errs) + 1, 3, Inches(x), Inches(y), Inches(CW), Inches(2.4))
gtab.name = "table_dt_errors"
tb = gtab.table
tb.columns[0].width = Inches(CW * 0.46); tb.columns[1].width = Inches(CW * 0.27); tb.columns[2].width = Inches(CW * 0.27)
for j, hh in enumerate(["Rules (mean of 3 seeds)", "Count % error", "Area % error"]):
    c = tb.cell(0, j); c.text = hh
    c.fill.solid(); c.fill.fore_color.rgb = rgb(NAVY)
    rr = c.text_frame.paragraphs[0].runs[0]; rr.font.size = Pt(19); rr.font.bold = True; rr.font.color.rgb = rgb(WHITE); rr.font.name = FONT
for i, e in enumerate(errs, start=1):
    for j, v in enumerate([e["rules"], f"{e['count_error_pct']:.2f}", f"{e['area_error_pct']:.2f}"]):
        c = tb.cell(i, j); c.text = v
        c.fill.solid(); c.fill.fore_color.rgb = rgb(CREAM if i == len(errs) else (WHITE if i % 2 else TINT))
        rr = c.text_frame.paragraphs[0].runs[0]; rr.font.size = Pt(19); rr.font.name = FONT; rr.font.color.rgb = rgb(INK)
        rr.font.bold = (i == len(errs))
        if j:
            c.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
y += 2.55
pw = 4.6
picture(A / "twin_vs_real_65min.png", x, y, w=pw, name="img_twin_vs_real", alt="Real cells (left) and digital twin (right) at 65 minutes")
textbox(x + pw + 0.2, y, CW - pw - 0.2, 3.9, [
    [("Division matters most: ", {"bold": True, "size": 21}), ("count error 14.3% → 4.8%.", {"size": 21})],
    [("Area tracks within 1.1%; ", {"bold": True, "size": 21}), ("the count lags because real cells divide smaller "
      "(2.30 → 2.08 µm² per cell), so the hidden-period count is likely an underestimate.", {"size": 21})],
], size=21, name="txt_dt_findings")

# ================================================================= COLUMN 3: Biofilm + conclusions
x, y = X[2], TOP
y = header(x, y, CW, "2 · Biofilm Movement & Breakup", "hdr_bf")
textbox(x, y, CW, 2.5, [
    [("Task: ", {"bold": True}), ("from 17 microscope frames and colony masks, measure each colony's centroid track, displacement and "
      "path length, plus the change in a supplied 0–100 breakup score (first frame ≥ 40). Auto-graded: centroids to 0.05 px, distances to 0.10 px, crossing frames exact.", {})],
], name="txt_bf_task")
y += 2.5
img_h = CW * (4.85 / 8.2)
picture(A / "biofilm_overlay.png", x, y, w=CW, name="img_biofilm", alt="Final microscope frame with colony masks and centroid trails")
y += img_h + 0.1
textbox(x, y, CW, 0.7, [("Final frame: colony masks (colour) and centroid trails (gold), labelled by colony ID.",
                         {"size": SMALL, "color": MUTED, "italic": True})], name="cap_biofilm")
y += 0.85

bfs = sorted(bf, key=lambda r: r["colony_id"])
cd = CategoryChartData()
cd.categories = [str(r["colony_id"]) for r in bfs]
cd.add_series("Net displacement (px)", [round(r["final_displacement_px"], 2) for r in bfs])
cd.add_series("Total path (px)", [round(r["total_distance_px"], 2) for r in bfs])
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(x), Inches(y), Inches(CW), Inches(6.6), cd)
gf.name = "chart_bf_distance"
ch = gf.chart
chart_title(ch, "Colony movement over 17 frames")
legend(ch, 18)
for i, sr in enumerate(ch.series):
    sr.format.fill.solid(); sr.format.fill.fore_color.rgb = rgb(NAVY if i == 0 else GOLD)
ch.plots[0].gap_width = 60
style_axis(ch.category_axis, "colony ID", 19)
style_axis(ch.value_axis, "pixels", 19, fmt="0", minv=0, maxv=55, major=10)
y += 6.8
textbox(x, y, CW, 3.9, [
    [("Colony 33 ", {"bold": True, "bullet": True}), ("moved farthest: 37.2 px net (42.9 px path), a direct drift.", {})],
    [("Colony 27 ", {"bold": True, "bullet": True}), ("had the largest breakup-score increase: +45, first ≥ 40 at frame 8; its path (31.0 px) "
      "far exceeds its net displacement (12.8 px), so it wandered. 3 of 8 colonies reached 40 (41 already at frame 0, 33 at frame 14).", {})],
    [("Caveat: ", {"bold": True, "bullet": True}), ("a centroid also moves when a colony changes shape; a score is not proof of cell "
      "release.", {})],
], size=22, name="txt_bf_results")
y += 3.9

y = header(x, y, CW, "Conclusions", "hdr_conc")
textbox(x, y, CW, BOTTOM - y, [
    [("Measure, don't guess: ", {"bold": True, "bullet": True}), ("every model rule came from data, and honest gaps "
      "(e.g. too few complete cell cycles) were reported, not tuned away.", {})],
    [("Verify independently: ", {"bold": True, "bullet": True}), ("a second implementation, real-arm readback (±1°) and "
      "replayed logs made the results trustworthy.", {})],
    [("AI agents scale a small team ", {"bold": True, "bullet": True}), ("when humans own decisions and agents follow a "
      "visible protocol (board, branches, ACK/DONE).", {})],
], size=22, name="txt_conclusions")

# ================================================================= COLUMN 4: Robotics + references
x, y = X[3], TOP
y = header(x, y, CW, "3 · Robotics that Responds", "hdr_rob")
textbox(x, y, CW, 2.0, [
    [("Task: ", {"bold": True}), ("connect live Pioreactor OD readings to a myCobot 320 (6-axis) arm and trigger a movement "
      "when OD crosses a threshold. Repeatability breaks ties.", {})],
], name="txt_rob_task")
y += 2.1
steps = [("Pioreactor", "IR OD reading every 5 s"), ("Leader API", "api.environnets.com"), ("od.py", "newest reading (clock-safe)"),
         ("arm.py", "threshold + hysteresis"), ("myCobot 320", "socket → servos")]
bw3 = (CW - 2 * 0.45) / 3
pos = [(0, 0), (1, 0), (2, 0), (2, 1), (1, 1)]
coords = []
for i, ((a, b), (cx, cy)) in enumerate(zip(steps, pos)):
    bx, byy = x + cx * (bw3 + 0.45), y + cy * 1.9
    dark = i in (0, 4)
    sh = card(bx, byy, bw3, 1.45, f"pipe_{i}", fill=NAVY if dark else TINT)
    tf = sh.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.1); tf.margin_right = Inches(0.1)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = a; r.font.bold = True; r.font.size = Pt(21); r.font.name = FONT
    r.font.color.rgb = rgb(WHITE if dark else NAVY)
    p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
    r2 = p2.add_run(); r2.text = b; r2.font.size = Pt(15); r2.font.name = FONT
    r2.font.color.rgb = rgb(WHITE if dark else INK)
    coords.append((bx, byy))
for i in range(4):
    (ax0, ay0), (ax1, ay1) = coords[i], coords[i + 1]
    if ay0 == ay1 and ax1 > ax0:
        sh = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(ax0 + bw3 + 0.05), Inches(ay0 + 0.5), Inches(0.35), Inches(0.45))
    elif ay0 == ay1:
        sh = s.shapes.add_shape(MSO_SHAPE.LEFT_ARROW, Inches(ax1 + bw3 + 0.05), Inches(ay0 + 0.5), Inches(0.35), Inches(0.45))
    else:
        sh = s.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(ax0 + bw3 / 2 - 0.22), Inches(ay0 + 1.5), Inches(0.45), Inches(0.35))
    sh.fill.solid(); sh.fill.fore_color.rgb = rgb(GOLD); sh.line.fill.background(); sh.name = f"pipe_arrow_{i}"
y += 3.6

photos = [(REPO / "robotics/evidence/reactor/03-assembled_reactor.jpg", "Assembled Pioreactor 20 ml on its Raspberry Pi"),
          (REPO / "robotics/evidence/reactor/08-vial.jpg", "Culture vial"),
          (REPO / "robotics/evidence/arm/obj4_arm_with_gripper.jpg", "myCobot 320 Pi with gripper and emergency stop")]
pw3 = (CW - 0.4) / 3
ph = pw3 * 4 / 3
for i, (pp, alt) in enumerate(photos):
    pic = picture(pp, x + i * (pw3 + 0.2), y, w=pw3, h=ph, name=f"img_rob_{i}", alt=alt)
    iw, ih = Image.open(pp).size
    target = 3 / 4
    if iw / ih > target:
        c = (1 - target * ih / iw) / 2; pic.crop_left = c; pic.crop_right = c
    else:
        c = (1 - (iw / ih) / target) / 2; pic.crop_top = c; pic.crop_bottom = c
y += ph + 0.1
textbox(x, y, CW, 0.65, [("Reactor  ·  vial  ·  arm with gripper (hardware provided by the organisers)",
                          {"size": SMALL, "color": MUTED, "italic": True})], name="cap_rob")
y += 0.8

cd = XyChartData()
od = [float(r["od"]) for r in trig]
thr = float(trig[0]["threshold"])
s_od = cd.add_series("Live OD")
for i, v in enumerate(od):
    s_od.add_data_point(i * 5, v)
s_thr = cd.add_series(f"Threshold ({thr})")
s_thr.add_data_point(0, thr); s_thr.add_data_point((len(od) - 1) * 5, thr)
events = [(i * 5, float(r["od"])) for i, r in enumerate(trig) if r["event"]]
for k, (ex, ey) in enumerate(events):          # one single-point series per response: no connecting line in any viewer
    cd.add_series(["1st arm response", "2nd arm response", "3rd arm response"][k]).add_data_point(ex, ey)
gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, Inches(x), Inches(y), Inches(CW), Inches(6.6), cd)
gf.name = "chart_rob_od"
ch = gf.chart
chart_title(ch, "Live run: 2 vial insertions → exactly 2 arm responses")
legend(ch, 18)
a, b_, *evs = ch.series
for sr in ch.series:
    sr.smooth = False
a.format.line.color.rgb = rgb(NAVY); a.format.line.width = Pt(3); a.marker.style = XL_MARKER_STYLE.CIRCLE; a.marker.size = 6
a.marker.format.fill.solid(); a.marker.format.fill.fore_color.rgb = rgb(NAVY); a.marker.format.line.color.rgb = rgb(NAVY)
b_.format.line.color.rgb = rgb("C0392B"); b_.format.line.width = Pt(2.5); b_.format.line.dash_style = 4; b_.marker.style = XL_MARKER_STYLE.NONE
for c_ in evs:
    c_.format.line.fill.background(); c_.marker.style = XL_MARKER_STYLE.DIAMOND; c_.marker.size = 18
    c_.marker.format.fill.solid(); c_.marker.format.fill.fore_color.rgb = rgb(GOLD); c_.marker.format.line.color.rgb = rgb(INK)

style_axis(ch.category_axis, "seconds into run (one reading every 5 s)", 19, minv=0, maxv=(len(od) - 1) * 5, major=30)
style_axis(ch.value_axis, "optical density", 19, fmt="0.00", minv=0, maxv=0.08, major=0.02)
y += 6.8
textbox(x, y, CW, 3.3, [
    [("All 5 objectives met: ", {"bold": True, "bullet": True}), ("reactor set up, API connected, live OD streamed, arm test "
      "movement (every pose within ~1°), OD-triggered response.", {})],
    [("Repeatable by design: ", {"bold": True, "bullet": True}), (f"threshold = baseline + 4σ ({thr}); hysteresis re-arms only after "
      "OD falls, so one crossing → one move. A dense vial (OD 0.005 → 0.39) also fired exactly once.", {})],
], size=21, name="txt_rob_results")
y += 3.45

y = header(x, y, CW, "References & Acknowledgements", "hdr_refs")
textbox(x, y, CW, BOTTOM - y, [
    ("Taheri-Araghi S. et al. (2015) Cell-size control and homeostasis in bacteria. Curr. Biol. 25:385–391.", {"size": 17, "bullet": True, "after": 4}),
    ("Vivarium (process-bigraph) & Viva-munk, Oliveira Lab; Pioreactor; Elephant Robotics pymycobot.", {"size": 17, "bullet": True, "after": 4}),
    ("Chou et al. (2026), Supplementary Video 1 (biofilm data).", {"size": 17, "bullet": True, "after": 4}),
    ("Thanks to the JSNN hackathon organisers and the Oliveira Lab for data, hardware and guidance. AI assistance: Claude (Anthropic).",
     {"size": 17, "after": 4}),
    ("Code, data & evidence: github.com/alexwilldev/jsnn-hackathon", {"size": 18, "bold": True, "color": NAVY, "after": 0}),
], size=17, name="txt_refs")

prs.save(sys.argv[1])
print("saved", sys.argv[1])

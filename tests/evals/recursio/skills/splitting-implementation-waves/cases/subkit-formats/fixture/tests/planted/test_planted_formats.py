"""Planted acceptance tests: one basic file per format, a round trip per format, load() and convert()."""

from subkit import Cue
from subkit.formats import FORMATS, ass, convert, load, microdvd, srt, vtt

SRT = """\ufeff1\r
00:00:01,000 --> 00:00:03,5\r
<I>Previously...</I>\r
\r
7\r
0:00:04.000 --> 00:00:06,250 X1:100 X2:600\r
{\\an8}- Where were you?\r
- <font color="red">Out.</font>\r
\r
3\r
00:00:09,000 --> 00:00:08,000\r
Backwards\r
"""

VTT = """WEBVTT - Pilot
Kind: captions

NOTE made by hand

intro
00:01.000 --> 00:03.500 line:0 align:center
<v Ann>Where were you?</v>

00:00:04.000 --> 00:00:06.000 line:-1
<c.loud>Tom &amp; Jerry</c>

00:00:07,000 --> 00:00:08.000
Bad comma
"""

ASS = """[Script Info]
Title: Pilot
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize
Style: Default,Arial,20

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:01.00,0:00:03.50,Default,Ann,0,0,0,,{\\i1}Where{\\i0} were you, Tom?
Comment: 0,0:00:02.00,0:00:03.00,Default,,0,0,0,,timing note
Dialogue: 0,0:00:04.00,0:00:06.00,Sign,,0,0,0,,{\\an8\\pos(320,40)}{\\b1}EXIT\\NNorth
Dialogue: 0,0:00:07.00
"""

SUB = """{1}{1}25
{25}{75}{Y:i}Previously...
{100}{160}- Where were you?|{y:b}- Out.
{200}{}/Later
{300}{290}Backwards
"""


def test_srt_reads_blocks_tags_and_top():
    result = srt.parse(SRT)
    assert result.cues == [
        Cue(1000, 3500, "<i>Previously...</i>"),
        Cue(4000, 6250, "- Where were you?\n- Out.", top=True),
    ]
    assert [(s.line, s.reason) for s in result.skipped] == [(10, "ends before it starts")]


def test_vtt_reads_header_voices_settings_and_entities():
    result = vtt.parse(VTT)
    assert result.title == "- Pilot"
    assert result.cues == [
        Cue(1000, 3500, "Where were you?", speaker="Ann", top=True),
        Cue(4000, 6000, "Tom & Jerry"),
    ]
    assert [(s.line, s.reason) for s in result.skipped] == [(13, "bad timing")]


def test_ass_reads_events_overrides_and_skips_short_lines():
    result = ass.parse(ASS)
    assert result.title == "Pilot"
    assert result.cues == [
        Cue(1000, 3500, "<i>Where</i> were you, Tom?", speaker="Ann"),
        Cue(4000, 6000, "<b>EXIT</b>\n<b>North</b>", top=True),
    ]
    assert [(s.line, s.reason) for s in result.skipped] == [(14, "missing fields")]


def test_microdvd_reads_frames_codes_and_open_ends():
    result = microdvd.parse(SUB)
    assert result.cues == [
        Cue(1000, 3000, "<i>Previously...</i>"),
        Cue(4000, 6400, "- Where were you?\n<b>- Out.</b>"),
        Cue(8000, 11000, "<i>Later</i>"),
    ]
    assert [(s.line, s.reason) for s in result.skipped] == [(5, "ends before it starts")]
    assert microdvd.parse("{25}{50}One", fps=25).cues == [Cue(1000, 2000, "One")]


CUES = [
    Cue(1000, 3500, "<i>Hello</i> there", speaker="Ann"),
    Cue(4000, 6000, "Line one\n<b>Line two</b>", top=True),
    Cue(7000, 9000, "Tom & Jerry <3"),
]


def test_srt_round_trip_loses_the_speaker():
    back = srt.parse(srt.dump(CUES, newline="\r\n")).cues
    assert back == [Cue(c.start, c.end, c.text, None, c.top) for c in CUES]


def test_vtt_round_trip_loses_nothing():
    text = vtt.dump(CUES, title="Pilot", ids=True)
    assert "Tom &amp; Jerry &lt;3" in text
    result = vtt.parse(text)
    assert (result.title, result.cues) == ("Pilot", CUES)


def test_ass_round_trip_rounds_to_centiseconds():
    cues = [*CUES, Cue(10004, 11006, "Odd times")]
    back = ass.parse(ass.dump(cues, title="Pilot")).cues
    assert back == [*CUES, Cue(10000, 11010, "Odd times")]


def test_microdvd_round_trip_at_25_fps():
    cues = [Cue(1000, 2000, "<i>One</i>\n<i>Two</i>"), Cue(3000, 4000, "<b>Bold</b>\nplain")]
    text = microdvd.dump(cues, fps=25)
    assert text.splitlines() == ["{1}{1}25", "{25}{50}{Y:i}One|Two", "{75}{100}{y:b}Bold|plain"]
    assert microdvd.parse(text).cues == cues


def test_load_sniffs_each_format_and_convert_writes_another(tmp_path):
    assert set(FORMATS) == {"srt", "vtt", "ass", "microdvd"}
    for name, text in [("a.srt", SRT), ("b.vtt", VTT), ("c.ass", ASS), ("d.sub", SUB)]:
        (tmp_path / name).write_text(text, encoding="utf-8")
        assert load(tmp_path / name).cues
    (tmp_path / "e.srt").write_bytes("1\n00:00:01,000 --> 00:00:02,000\n\xe9t\xe9\n".encode("cp1252"))
    assert load(tmp_path / "e.srt").cues == [Cue(1000, 2000, "\xe9t\xe9")]
    assert convert(SUB, "srt").startswith("1\n00:00:01,000 --> 00:00:03,000\n<i>Previously...</i>\n\n")

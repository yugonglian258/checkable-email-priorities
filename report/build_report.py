"""Build the report with reportlab. The application itself has no dependencies."""
import json
import re
from html import escape
from pathlib import Path

from reportlab.graphics import renderSVG
from reportlab.graphics.shapes import Drawing, Line, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, PageBreak, Spacer, KeepTogether

HERE = Path(__file__).resolve().parent
CONTENT = json.loads((HERE / 'content.json').read_text(encoding='utf-8'))
FONT_DIR = Path('C:/Windows/Fonts')
if (FONT_DIR / 'arial.ttf').exists():
    pdfmetrics.registerFont(TTFont('Body', str(FONT_DIR / 'arial.ttf')))
    pdfmetrics.registerFont(TTFont('Bold', str(FONT_DIR / 'arialbd.ttf')))
else:
    pdfmetrics.registerFont(pdfmetrics.Font('Body', 'Helvetica', 'WinAnsiEncoding'))
    pdfmetrics.registerFont(pdfmetrics.Font('Bold', 'Helvetica-Bold', 'WinAnsiEncoding'))

INK = colors.HexColor('#172b37')
TEAL = colors.HexColor('#086b68')
MUTED = colors.HexColor('#536b79')
PALE = colors.HexColor('#edf5f4')
WIDTH = 511.2
styles = {
    'title': ParagraphStyle('Title', fontName='Bold', fontSize=24, leading=28, spaceAfter=12, textColor=INK),
    'h1': ParagraphStyle('Heading', fontName='Bold', fontSize=13, leading=17, spaceBefore=12, spaceAfter=7, textColor=INK, keepWithNext=True),
    'body': ParagraphStyle('Body', fontName='Body', fontSize=10.7, leading=14, spaceAfter=7, textColor=INK, splitLongWords=False),
    'small': ParagraphStyle('Small', fontName='Body', fontSize=9, leading=12, spaceAfter=8, textColor=MUTED),
    'caption': ParagraphStyle('Caption', fontName='Body', fontSize=9.1, leading=12, spaceAfter=13, textColor=MUTED),
    'ref': ParagraphStyle('Reference', fontName='Body', fontSize=9.8, leading=14, spaceAfter=13, textColor=INK),
    'scenario': ParagraphStyle('Scenario', fontName='Bold', fontSize=11, leading=14, spaceBefore=6, spaceAfter=5, textColor=INK, keepWithNext=True),
}
styles['ref'].splitLongWords = True
styles['caption'].spaceAfter = 8


def paragraph(text, style='body'):
    text = escape(text)
    text = re.sub(r'https://[^\s]+', lambda match: '<link href="' + match.group() + '">' + match.group() + '</link>', text)
    return Paragraph(text, styles[style])


def wrapped_lines(text, width, font='Body', size=9):
    lines, current = [], ''
    for word in text.split():
        candidate = (current + ' ' + word).strip()
        if current and pdfmetrics.stringWidth(candidate, font, size) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    return lines + [current]


def box(drawing, x, y, w, h, title, lines, planned=False):
    drawing.add(Rect(x, y, w, h, fillColor=colors.white if planned else PALE,
                     strokeColor=MUTED if planned else TEAL, strokeWidth=.8,
                     strokeDashArray=[3, 3] if planned else None, rx=5, ry=5))
    drawing.add(String(x+9, y+h-17, title, fontName='Bold', fontSize=9.4, fillColor=INK))
    position = y+h-32
    for text in lines:
        for line in wrapped_lines(text, w-18, size=8.6):
            drawing.add(String(x+9, position, line, fontName='Body', fontSize=8.6, fillColor=INK))
            position -= 11


def arrow(drawing, x1, y1, x2, y2):
    drawing.add(Line(x1, y1, x2, y2, strokeColor=MUTED, strokeWidth=.9))
    if x1 == x2:
        direction = 1 if y2 > y1 else -1
        points = [x2, y2, x2-3, y2-5*direction, x2+3, y2-5*direction]
    else:
        direction = 1 if x2 > x1 else -1
        points = [x2, y2, x2-5*direction, y2-3, x2-5*direction, y2+3]
    drawing.add(Polygon(points, fillColor=MUTED, strokeColor=MUTED))


def architecture():
    drawing = Drawing(WIDTH, 211)
    box(drawing, 0, 125, 150, 73, 'Browser interface', ['Select thread', 'Inspect / choose / Undo'])
    box(drawing, 181, 125, 149, 73, 'Python HTTP handler', ['Validate action', 'Recompute suggestion'])
    box(drawing, 361, 125, 150, 73, 'Rule engine', ['Baseline or revised', 'AI behaviour simulated'])
    arrow(drawing, 150, 174, 181, 174)
    arrow(drawing, 330, 174, 361, 174)
    arrow(drawing, 361, 143, 330, 143)
    arrow(drawing, 181, 143, 150, 143)
    box(drawing, 181, 18, 149, 76, 'Local session memory', ['Labels and undo history', 'Explicit choice required'])
    box(drawing, 361, 18, 150, 76, 'Synthetic input', ['Latest + quoted text', 'Timestamps + fixed clock'])
    arrow(drawing, 255, 125, 255, 94)
    arrow(drawing, 436, 94, 436, 125)
    box(drawing, 0, 18, 150, 76, 'Planned components', ['Mailbox access', 'Learned model'], planned=True)
    drawing.add(String(0, 0, 'Solid boxes implemented     Dashed box planned     Inference uses deterministic rules',
                       fontName='Body', fontSize=8.4, fillColor=MUTED))
    return drawing


def storyboard(scenario):
    drawing = Drawing(WIDTH, 78)
    for index, frame in enumerate(scenario['frames']):
        x = index * 175
        box(drawing, x, 4, 160, 70, f'{index+1}  {frame[0]}', frame[1:])
        if index < 2:
            arrow(drawing, x+161, 39, x+173, 39)
    return drawing


def word_count(text):
    return len(re.findall(r"\b[\w]+(?:['-][\w]+)*\b", text))


def page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(MUTED)
    canvas.setFont('Body', 8)
    canvas.drawString(50.4, 22, 'Checkable email priorities  |  A2 Project Report  |  3154083')
    canvas.drawRightString(letter[0]-50.4, 22, str(doc.page))
    canvas.restoreState()


def build():
    elements = []
    heading_text = [block.get('heading', '') for block in CONTENT['page1']+CONTENT['page2']]
    main_text = '\n'.join([block['text'] for block in CONTENT['page1']+CONTENT['page2']]+heading_text+[CONTENT['interaction_intro']])
    abstract_words = word_count(CONTENT['abstract'])
    main_words = word_count(main_text)
    assert abstract_words <= 300 and main_words <= 1100 and abstract_words+main_words <= 1300
    elements.append(paragraph('A2 Project Report  |  Student 3154083  |  23 November 2026', 'small'))
    elements.append(paragraph(CONTENT['title'], 'title'))
    elements.append(paragraph(f'Total counted words {abstract_words+main_words}  |  Abstract {abstract_words}  |  Main text {main_words}', 'small'))
    elements.append(paragraph('Abstract', 'h1'))
    elements.append(paragraph(CONTENT['abstract']))
    for block in CONTENT['page1']:
        if block.get('heading'):
            elements.append(paragraph(block['heading'], 'h1'))
        elements.append(KeepTogether([paragraph(block['text'])]))
    for block in CONTENT['page2']:
        if block.get('heading'):
            elements.append(paragraph(block['heading'], 'h1'))
        elements.append(KeepTogether([paragraph(block['text'])]))
    elements.append(PageBreak())
    elements.append(paragraph(CONTENT['interaction_intro'], 'small'))
    elements.append(paragraph('System architecture', 'h1'))
    arch = architecture()
    elements.append(arch)
    elements.append(paragraph('Figure 1. Components, inputs, action boundary and returned suggestions. Planned components are outside the implemented path.', 'caption'))
    renderSVG.drawToFile(arch, str(HERE/'architecture.svg'))
    elements.append(Spacer(1, 7))
    for index, scenario in enumerate(CONTENT['scenarios']):
        elements.append(paragraph(scenario['title'], 'scenario'))
        figure = storyboard(scenario)
        elements.append(figure)
        elements.append(paragraph(f'Figure {index+2}. '+scenario['caption'], 'caption'))
        renderSVG.drawToFile(figure, str(HERE/f'scenario-{index+1}.svg'))
    elements.append(PageBreak())
    elements.append(paragraph('Project access and development evidence', 'h1'))
    metadata = HERE/'repository.json'
    repository = json.loads(metadata.read_text()) if metadata.exists() else {}
    if repository.get('url'):
        elements.append(paragraph('Public repository '+repository['url']))
        elements.append(paragraph('README and development record '+repository['url']+'/blob/a2-submission-v1/README.md'))
    else:
        elements.append(paragraph('Project materials are supplied in the accompanying project archive. README.md contains run instructions, the development record, software checks and the AI assistance statement.'))
    elements.append(paragraph('The submitted source version is identified by the Git tag a2-submission-v1. Browser evidence is in evidence/ and the regression transcript is evidence/test-results.txt. The implementation and fixed fixtures can be replayed using the README instructions.'))
    elements.append(paragraph('References and reused material', 'h1'))
    for reference in CONTENT['references']:
        elements.append(paragraph(reference.replace(' .', ''), 'ref'))
    elements.append(paragraph('The architecture and interaction figures were prepared for A2 from the implemented states. Report text, diagram labels and references were checked against the prototype and cited material. The README records Codex assistance and the reused Lab 3 components.', 'small'))
    pdf = HERE/'A2_Project_Report_3154083.pdf'
    doc = BaseDocTemplate(str(pdf), pagesize=letter, leftMargin=50.4, rightMargin=50.4,
                          topMargin=40, bottomMargin=40, title=CONTENT['title'], author='Student 3154083')
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates(PageTemplate(id='report', frames=frame, onPage=page_footer))
    doc.build(elements)
    (HERE/'word-count.json').write_text(json.dumps({'abstract':abstract_words,'main_including_headings_and_interaction_intro':main_words,
        'total':abstract_words+main_words,'excluded':'Title, metadata, figures and brief captions, references and repository access information'}, indent=2))
    print(pdf)
    print(f'Words: abstract {abstract_words}, main {main_words}, total {abstract_words+main_words}')


if __name__ == '__main__':
    build()

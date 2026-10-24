"""Editable academic Word export with native headings, contents and page fields."""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import re
import struct
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
PAGE_WIDTH = 11906
PAGE_HEIGHT = 16838
BODY_WIDTH = 9071


def write_academic_docx(cfg, front_blocks, sections, out, toc_entries=None, page_map=None):
    """Write ``out/report.docx`` without changing source images or other files.

    Heading anchors are taken from ``section['anchor']`` and h3 blocks. Contents
    fields use native Word bookmarks/PAGEREF and refresh when opened or edited.
    ``page_map`` supplies only the cached visible labels used before Word updates.
    """
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    page_map = page_map or {}
    rels = []
    media = []
    bookmark_ids = {}
    bookmark_names = {}
    history_path = out / 'evidence/development-history.json'
    history = json.loads(history_path.read_text(encoding='utf-8')) if history_path.exists() else {}
    known_commits = [entry['commit'] for entry in history.get('commits', [])
                     if re.fullmatch(r'[0-9a-fA-F]{40}', entry.get('commit', ''))]

    def attribute(value):
        return html.escape(str(value), quote=True)

    def bookmark(anchor):
        anchor = str(anchor)
        if anchor not in bookmark_names:
            stem = re.sub(r'[^A-Za-z0-9_]', '_', anchor)[:24]
            bookmark_names[anchor] = 'h_' + stem + '_' + hashlib.sha1(anchor.encode()).hexdigest()[:8]
            bookmark_ids[anchor] = len(bookmark_ids) + 1
        return bookmark_names[anchor]

    def text_run(text, properties=''):
        text = str(text)
        if not text:
            return ''
        return '<w:r>' + ('<w:rPr>'+properties+'</w:rPr>' if properties else '') + '<w:t xml:space="preserve">'+escape(text)+'</w:t></w:r>'

    def linked_runs(text):
        pieces = []
        for part in re.split(r'(https?://[^\s<>]+|(?<![\w#])#[1-9]\d*\b|(?<!\w)[0-9a-fA-F]{7,40}(?!\w))', str(text)):
            label, url, tail = part, None, ''
            if part.startswith(('https://', 'http://')):
                url = part.rstrip('.,;')
                label, tail = url, part[len(url):]
            elif re.fullmatch(r'#[1-9]\d*', part):
                url = cfg['repository_url'].rstrip('/') + '/issues/' + part[1:]
            elif re.fullmatch(r'[0-9a-fA-F]{7,40}', part):
                matches = [sha for sha in known_commits if sha.lower().startswith(part.lower())]
                if len(matches) == 1:
                    url = cfg['repository_url'].rstrip('/') + '/commit/' + matches[0]
            if url:
                rid = 'rLink' + str(len(rels) + 1)
                rels.append('<Relationship Id="'+rid+'" Type="'+R+'/hyperlink" Target="'+attribute(url)+'" TargetMode="External"/>')
                pieces.append('<w:hyperlink r:id="'+rid+'">'+text_run(label, '<w:color w:val="111111"/><w:u w:val="single"/>')+'</w:hyperlink>')
                pieces.append(text_run(tail))
            else:
                pieces.append(text_run(part))
        return ''.join(pieces)

    def para(text='', style='Normal', *, anchor=None, properties='', runs=None):
        props = '<w:pPr><w:pStyle w:val="'+attribute(style)+'"/>'+properties+'</w:pPr>'
        contents = linked_runs(text) if runs is None else runs
        if anchor:
            name = bookmark(anchor)
            ident = str(bookmark_ids[str(anchor)])
            contents = '<w:bookmarkStart w:id="'+ident+'" w:name="'+name+'"/>'+contents+'<w:bookmarkEnd w:id="'+ident+'"/>'
        return '<w:p>'+props+contents+'</w:p>'

    def image(path, alt, *, cover=False):
        file = out / path
        if file.suffix.lower() == '.svg':
            file = file.with_suffix('.png')
        if not file.exists():
            raise FileNotFoundError(file)
        data = file.read_bytes()
        if data[:8] != b'\x89PNG\r\n\x1a\n':
            raise ValueError('Academic DOCX figures must have their existing PNG export: '+str(file))
        width, height = struct.unpack('>II', data[16:24])
        max_width, max_height = (50, 50) if cover else (160, 190)
        scale = min(max_width / width, max_height / height)
        cx, cy = int(width*scale*36000), int(height*scale*36000)
        number = len(media)+1
        rid = 'rImage'+str(number)
        name = 'image'+str(number)+'.png'
        media.append((name, data))
        rels.append('<Relationship Id="'+rid+'" Type="'+R+'/image" Target="media/'+name+'"/>')
        drawing = f'''<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{number}" name="{attribute(alt)}" descr="{attribute(alt)}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="{number}" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>'''
        return para(style='Figure', properties=('' if cover else '<w:keepNext/>')+'<w:jc w:val="center"/>', runs=drawing)

    def table(block):
        headers = block['headers']
        cols = len(headers)
        if not cols:
            return ''
        supplied = block.get('widths')
        if supplied and len(supplied) == cols:
            widths = [int(BODY_WIDTH*float(n)/sum(supplied)) for n in supplied]
        elif cols == 2:
            widths = [int(BODY_WIDTH*.28), int(BODY_WIDTH*.72)]
        elif cols == 3:
            widths = [int(BODY_WIDTH*.26), int(BODY_WIDTH*.38), int(BODY_WIDTH*.36)]
        else:
            widths = [BODY_WIDTH//cols]*cols
        widths[-1] = BODY_WIDTH-sum(widths[:-1])
        grid = '<w:tblGrid>'+''.join('<w:gridCol w:w="'+str(n)+'"/>' for n in widths)+'</w:tblGrid>'
        rows = []
        for index, row in enumerate([headers]+block['rows']):
            cells = []
            for col, value in enumerate(row):
                width = widths[min(col,cols-1)]
                cellprops = '<w:tcPr><w:tcW w:w="'+str(width)+'" w:type="dxa"/><w:vAlign w:val="top"/><w:shd w:val="clear" w:fill="FFFFFF"/></w:tcPr>'
                cells.append('<w:tc>'+cellprops+para(value,'TableHeader' if index == 0 else 'TableText')+'</w:tc>')
            rowprops = '<w:trPr><w:cantSplit/>'+('<w:tblHeader/>' if index == 0 else '')+'</w:trPr>'
            rows.append('<w:tr>'+rowprops+''.join(cells)+'</w:tr>')
        borders = ''.join('<w:'+side+' w:val="single" w:sz="'+('6' if side in ('top','bottom') else '3')+'" w:color="'+('111111' if side in ('top','bottom') else 'B7B7B7')+'"/>' for side in ('top','bottom','insideH'))
        borders += '<w:left w:val="nil"/><w:right w:val="nil"/><w:insideV w:val="nil"/>'
        props = '<w:tblPr><w:tblW w:w="'+str(BODY_WIDTH)+'" w:type="dxa"/><w:tblLayout w:type="fixed"/><w:tblBorders>'+borders+'</w:tblBorders><w:tblCellMar><w:top w:w="55" w:type="dxa"/><w:left w:w="65" w:type="dxa"/><w:bottom w:w="55" w:type="dxa"/><w:right w:w="65" w:type="dxa"/></w:tblCellMar></w:tblPr>'
        return (para(block['caption'],'Caption',properties='<w:keepNext/>') if block.get('caption') else '')+'<w:tbl>'+props+grid+''.join(rows)+'</w:tbl>'+para('', 'TableSpace')

    def blocks_xml(blocks, *, front=False):
        body = []
        for block in blocks:
            kind = block['type']
            if kind == 'p':
                body.append(para(block['text']))
            elif kind == 'h3':
                body.append(para(block['text'],'FrontSubheading' if front else 'Heading2',anchor=block.get('anchor')))
            elif kind == 'list':
                for item in block['items']:
                    body.append(para(item,'Bullet',runs=text_run('•\t')+linked_runs(item)))
            elif kind == 'table':
                body.append(table(block))
            elif kind == 'image':
                body.append(image(block['path'],block.get('caption','Report figure')))
                body.append(para(block.get('caption',''),'Caption'))
            else:
                raise ValueError('Unsupported report block: '+kind)
        return ''.join(body)

    def section_properties(*, page_format=None, footer=False, title=False, next_page=False):
        reference = '<w:footerReference w:type="default" r:id="rFooter"/>' if footer else ''
        kind = '<w:type w:val="nextPage"/>' if next_page else ''
        numbering = '<w:pgNumType w:fmt="'+page_format+'" w:start="1"/>' if page_format else ''
        return '<w:sectPr>'+reference+kind+f'<w:pgSz w:w="{PAGE_WIDTH}" w:h="{PAGE_HEIGHT}"/><w:pgMar w:top="1417" w:right="1134" w:bottom="1247" w:left="1701" w:header="567" w:footer="567" w:gutter="0"/>'+numbering+('<w:titlePg/>' if title else '')+'</w:sectPr>'

    def end_section(**kwargs):
        return '<w:p><w:pPr>'+section_properties(next_page=True,**kwargs)+'</w:pPr></w:p>'

    def cached_label(entry):
        anchor = entry.get('anchor',entry['title'])
        value = page_map.get(anchor,page_map.get(entry['title'],''))
        if isinstance(value,dict):
            value = value.get('label',value.get('page',''))
        return str(value)

    # Keep the cover editable: only the university logo is an embedded image.
    body = para('', 'CoverSpace', properties='<w:spacing w:before="700" w:after="0"/>')
    body += para(cfg['title'],'CoverTitle')
    body += para('First Submission of Materials, Probationary Period 1','CoverSubtitle')
    body += para('By','CoverLine')
    for member in cfg.get('members',[])[:2]:
        label = member.get('name','')
        if member.get('group'):
            label += ' — '+member['group']
        body += para(label,'CoverLine')
    body += image('university-logo.png','Astana IT University logo',cover=True)
    body += para('ASTANA IT UNIVERSITY','CoverInstitution')
    supervisor = cfg.get('supervisor','')
    if cfg.get('supervisor_position'):
        supervisor += ', '+cfg['supervisor_position']
    body += para('Supervisor: '+supervisor,'CoverLine')
    body += para('October 2026','CoverLine')
    body += para('ASTANA','CoverLine')
    body += end_section(title=True)

    body += para('Submission Information','FrontSummaryTitle',anchor='front-summary')
    body += blocks_xml(front_blocks,front=True)
    body += para('Table of Contents','FrontTitle',properties='<w:pageBreakBefore/>')

    if toc_entries is None:
        toc_entries = [{'title':'Submission Information','anchor':'front-summary','level':0}]
        for index, section in enumerate(sections,1):
            toc_entries.append({'title':section['title'],'anchor':section.get('anchor','chapter-'+str(index)),'level':0})
            toc_entries.extend({'title':b['text'],'anchor':b.get('anchor',b['text']),'level':1} for b in section['blocks'] if b['type']=='h3')
    # A native TOC field with native cached PAGEREF fields stays editable in Word.
    body += para(runs='<w:r><w:fldChar w:fldCharType="begin"/></w:r><w:r><w:instrText xml:space="preserve"> TOC \\o "1-2" \\h \\z \\u </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r>')
    for entry in toc_entries:
        title = entry['title']
        anchor = entry.get('anchor',title)
        name = bookmark(anchor)
        runs = '<w:hyperlink w:anchor="'+name+'">'+text_run(title,'<w:color w:val="111111"/>')+'</w:hyperlink><w:r><w:tab/></w:r>'
        runs += '<w:fldSimple w:instr=" PAGEREF '+name+' \\h ">'+text_run(cached_label(entry))+'</w:fldSimple>'
        body += para(style='TOC2' if entry.get('level',0) else 'TOC1',runs=runs)
    body += para(runs='<w:r><w:fldChar w:fldCharType="end"/></w:r>')
    body += end_section(page_format='lowerRoman',footer=True)

    for index, section in enumerate(sections,1):
        body += para(section['title'],'Heading1',anchor=section.get('anchor','chapter-'+str(index)))
        body += blocks_xml(section['blocks'])
    body += section_properties(page_format='decimal',footer=True)

    document = DECL+f'<w:document xmlns:w="{W}" xmlns:r="{R}" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><w:body>{body}</w:body></w:document>'
    style_defs = {
        'Normal': ('<w:spacing w:after="120" w:line="276" w:lineRule="auto"/><w:jc w:val="both"/><w:widowControl/>',''),
        'CoverTitle': ('<w:jc w:val="center"/><w:spacing w:before="120" w:after="460" w:line="300" w:lineRule="auto"/><w:pBdr><w:top w:val="double" w:sz="6" w:space="9" w:color="111111"/><w:bottom w:val="double" w:sz="6" w:space="9" w:color="111111"/></w:pBdr>','<w:sz w:val="46"/>'),
        'CoverSubtitle': ('<w:jc w:val="center"/><w:spacing w:before="120" w:after="360"/>','<w:sz w:val="22"/>'),
        'CoverLine': ('<w:jc w:val="center"/><w:spacing w:after="120"/>','<w:sz w:val="22"/>'),
        'CoverInstitution': ('<w:jc w:val="center"/><w:spacing w:before="160" w:after="560"/>','<w:sz w:val="22"/>'),
        'CoverSpace': ('<w:spacing w:after="0"/>','<w:sz w:val="2"/>'),
        'FrontTitle': ('<w:keepNext/><w:spacing w:before="160" w:after="240"/>','<w:sz w:val="44"/>'),
        'FrontSummaryTitle': ('<w:keepNext/><w:spacing w:before="160" w:after="240"/><w:outlineLvl w:val="0"/>','<w:sz w:val="44"/>'),
        'FrontSubheading': ('<w:keepNext/><w:spacing w:before="220" w:after="100"/>','<w:b/><w:sz w:val="27"/>'),
        'Heading1': ('<w:keepNext/><w:keepLines/><w:spacing w:before="320" w:after="180"/><w:outlineLvl w:val="0"/>','<w:b/><w:sz w:val="34"/>'),
        'Heading2': ('<w:keepNext/><w:keepLines/><w:spacing w:before="220" w:after="100"/><w:outlineLvl w:val="1"/>','<w:b/><w:sz w:val="27"/>'),
        'TableText': ('<w:spacing w:after="20" w:line="240" w:lineRule="auto"/><w:jc w:val="left"/>','<w:sz w:val="17"/>'),
        'TableHeader': ('<w:spacing w:after="20" w:line="240" w:lineRule="auto"/><w:jc w:val="left"/><w:keepNext/>','<w:b/><w:sz w:val="17"/>'),
        'TableSpace': ('<w:spacing w:after="70" w:before="0"/>','<w:sz w:val="2"/>'),
        'Figure': ('<w:spacing w:before="140" w:after="50"/><w:jc w:val="center"/>',''),
        'Caption': ('<w:spacing w:after="140"/><w:jc w:val="left"/>','<w:sz w:val="19"/>'),
        'Bullet': ('<w:ind w:left="240" w:hanging="200"/><w:tabs><w:tab w:val="left" w:pos="240"/></w:tabs><w:spacing w:after="80"/><w:jc w:val="left"/>',''),
        'TOC1': ('<w:spacing w:after="100"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9071"/></w:tabs>','<w:b/><w:sz w:val="21"/>'),
        'TOC2': ('<w:ind w:left="360"/><w:spacing w:after="70"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9071"/></w:tabs>','<w:sz w:val="21"/>'),
    }
    styles = DECL+f'<w:styles xmlns:w="{W}"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman" w:cs="Times New Roman"/><w:color w:val="111111"/><w:lang w:val="en-US"/><w:sz w:val="22"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
    for name,(paragraph_props,run_props) in style_defs.items():
        display = {'Heading1':'heading 1','Heading2':'heading 2','TOC1':'toc 1','TOC2':'toc 2'}.get(name,name)
        based = '' if name == 'Normal' else '<w:basedOn w:val="Normal"/>'
        styles += '<w:style w:type="paragraph" w:styleId="'+name+'"'+(' w:default="1"' if name == 'Normal' else '')+'><w:name w:val="'+display+'"/>'+based+'<w:pPr>'+paragraph_props+'</w:pPr><w:rPr>'+run_props+'</w:rPr></w:style>'
    styles += '</w:styles>'
    settings = DECL+f'<w:settings xmlns:w="{W}"><w:updateFields w:val="true"/><w:compat/></w:settings>'
    footer = DECL+f'<w:ftr xmlns:w="{W}"><w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="0" w:after="0"/></w:pPr><w:fldSimple w:instr=" PAGE "><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="20"/><w:color w:val="111111"/></w:rPr><w:t>1</w:t></w:r></w:fldSimple></w:p></w:ftr>'
    for rid,kind,target in [('rStyles','styles','styles.xml'),('rSettings','settings','settings.xml'),('rFooter','footer','footer1.xml')]:
        rels.append('<Relationship Id="'+rid+'" Type="'+R+'/'+kind+'" Target="'+target+'"/>')
    content_types = DECL+'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>'
    for part,kind in [('document','document.main'),('styles','styles'),('settings','settings'),('footer1','footer')]:
        content_types += '<Override PartName="/word/'+part+'.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.'+kind+'+xml"/>'
    content_types += '</Types>'
    with ZipFile(out/'report.docx','w',ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml',content_types)
        archive.writestr('_rels/.rels',DECL+f'<Relationships xmlns="{REL}"><Relationship Id="rDocument" Type="{R}/officeDocument" Target="word/document.xml"/></Relationships>')
        archive.writestr('word/document.xml',document)
        archive.writestr('word/styles.xml',styles)
        archive.writestr('word/settings.xml',settings)
        archive.writestr('word/footer1.xml',footer)
        archive.writestr('word/_rels/document.xml.rels',DECL+f'<Relationships xmlns="{REL}">'+''.join(rels)+'</Relationships>')
        for name,data in media:
            archive.writestr('word/media/'+name,data)
    return {'path':str(out/'report.docx'),'media':len(media),'toc_entries':len(toc_entries),'native_fields':True}

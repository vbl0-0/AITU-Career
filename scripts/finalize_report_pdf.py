"""Resolve real contents pages and add unbranded academic page numbering."""
import json
import os
from pathlib import Path
import re
import sys
import pymupdf

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/pre-defense-1'
mode=sys.argv[1] if len(sys.argv)>1 else 'collect'

def roman(value):
    result=''
    for number,symbol in [(1000,'m'),(900,'cm'),(500,'d'),(400,'cd'),(100,'c'),(90,'xc'),(50,'l'),(40,'xl'),(10,'x'),(9,'ix'),(5,'v'),(4,'iv'),(1,'i')]:
        while value>=number:result+=symbol;value-=number
    return result

def normalized(text):
    return re.sub(r'\s+',' ',text).strip()

content=json.loads((OUT/'report-content.json').read_text(encoding='utf-8'))
doc=pymupdf.open(OUT/'report.pdf')
if mode=='collect':
    outlines={normalized(row[1]):row[2] for row in doc.get_toc()}
    entries=content['toc_entries']
    missing=[entry['title'] for entry in entries if normalized(entry['title']) not in outlines]
    if missing:raise RuntimeError('PDF heading outlines missing: '+str(missing))
    body=outlines[normalized(content['sections'][0]['title'])]-1
    physical={entry['anchor']:outlines[normalized(entry['title'])] for entry in entries}
    labels={key:(str(page-body) if page-1>=body else roman(page-1)) for key,page in physical.items()}
    result={'page_map':labels,'physical_pages':physical,'body_start_index':body,'total_pages':len(doc)}
    target=OUT/'toc-pages.json'
    old=json.loads(target.read_text(encoding='utf-8')) if target.exists() else {}
    changed=old!=result
    if changed:target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    doc.close()
    print(json.dumps({'changed':changed,'pages':result['total_pages'],'toc_entries':len(entries)}))
elif mode=='stamp':
    data=json.loads((OUT/'toc-pages.json').read_text(encoding='utf-8'))
    body=data['body_start_index']
    for index in range(1,len(doc)):
        page=doc[index]
        label=str(index-body+1) if index>=body else roman(index)
        page.insert_textbox(pymupdf.Rect(page.rect.width/2-40,page.rect.height-37,page.rect.width/2+40,page.rect.height-20),label,fontname='tiro',fontsize=10,align=1,color=(0,0,0))
    doc.set_page_labels([{'startpage':0,'prefix':'Cover','style':''},{'startpage':1,'prefix':'','style':'r','firstpagenum':1},{'startpage':body,'prefix':'','style':'D','firstpagenum':1}])
    target=OUT/'report-numbered.pdf'
    doc.save(target,garbage=4,deflate=True)
    doc.close()
    os.replace(target,OUT/'report.pdf')
    print(json.dumps({'plain_page_numbers':True,'branded_footer':False,'body_start_index':body}))
else:
    raise ValueError('Use collect or stamp')

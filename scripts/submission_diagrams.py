"""Editable diagram models and SVG exports; keeps the submitted diagrams reproducible."""
import json
from html import escape
from pathlib import Path

OUT=Path(__file__).resolve().parents[1]/'docs/pre-defense-1/diagrams'
OUT.mkdir(parents=True,exist_ok=True)

def box(id,x,y,w,h,lines,kind='box'):return dict(id=id,x=x,y=y,w=w,h=h,lines=lines,kind=kind)
def draw(name,title,nodes,edges,width=1100,height=700,boundary=None):
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">', '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="none" stroke="#526579"/></marker></defs>',f'<rect width="{width}" height="{height}" fill="white"/>',f'<text x="28" y="36" font-family="Segoe UI,Arial" font-size="23" font-weight="700" fill="#103f6b">{escape(title)}</text>']
    if boundary:
        x,y,w,h,label=boundary
        parts+=[f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#f7fafe" stroke="#9dbcd8" stroke-dasharray="6 5"/>',f'<text x="{x+15}" y="{y+25}" font-family="Segoe UI,Arial" font-size="16" fill="#103f6b">{escape(label)}</text>']
    lookup={n['id']:n for n in nodes}
    for edge in edges:
        src,dst,label,*options=edge
        a=lookup[src];b=lookup[dst]; dashed='dashed' in options
        # Connect facing sides; use centered vertical links only for same-column nodes.
        if abs(a['x']-b['x'])<20:
            x1=a['x']+a['w']/2;y1=a['y']+(a['h'] if b['y']>a['y'] else 0)
            x2=b['x']+b['w']/2;y2=b['y']+(0 if b['y']>a['y'] else b['h'])
        else:
            right=b['x']>a['x'];x1=a['x']+(a['w'] if right else 0);y1=a['y']+a['h']/2
            x2=b['x']+(0 if right else b['w']);y2=b['y']+b['h']/2
        dash='stroke-dasharray="5 4"' if dashed else ''
        arrow='' if 'association' in options else 'marker-end="url(#arrow)"'
        parts.append(f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="#526579" stroke-width="1.5" {dash} {arrow}/>')
        if label:
            mx=(x1+x2)/2;my=(y1+y2)/2-8;length=len(label)*7.2
            parts.append(f'<rect x="{mx-length/2-4}" y="{my-15}" width="{length+8}" height="21" fill="white"/><text x="{mx}" y="{my}" text-anchor="middle" font-family="Segoe UI,Arial" font-size="13" fill="#526579">{escape(label)}</text>')
    for n in nodes:
        x,y,w,h=n['x'],n['y'],n['w'],n['h'];kind=n['kind']
        if kind=='actor':
            cx=x+w/2
            parts.append(f'<g stroke="#103f6b" stroke-width="2.3" fill="none"><circle cx="{cx}" cy="{y+15}" r="13"/><path d="M{cx},{y+28} v35 m-27,-23 h54 m-27,23 l-23,27 m23,-27 l23,27"/></g>')
            base=y+110
        elif kind=='usecase':
            parts.append(f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="#eaf3fc" stroke="#0f6cbf"/>');base=y+h/2-(len(n['lines'])-1)*10+5
        else:
            parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#eaf3fc" stroke="#0f6cbf"/>');base=y+h/2-(len(n['lines'])-1)*11+5
        for i,line in enumerate(n['lines']):
            parts.append(f'<text x="{x+w/2}" y="{base+i*22}" text-anchor="middle" font-family="Segoe UI,Arial" font-size="16" fill="#103f6b">{escape(line)}</text>')
    parts.append('</svg>');(OUT/(name+'.svg')).write_text('\n'.join(parts),encoding='utf-8')
    (OUT/(name+'.json')).write_text(json.dumps(dict(title=title,width=width,height=height,nodes=nodes,edges=edges,boundary=boundary),ensure_ascii=False,indent=2),encoding='utf-8')

draw('context','System Context — AITU Career',[
 box('graduate',25,160,210,120,['Student / graduate','Profile, skills, opportunities']),
 box('system',400,215,300,150,['AITU Career','Profile + matching + guidance','React / FastAPI / PostgreSQL']),
 box('admin',865,160,210,120,['Administrator','Demo jobs and skill catalog']),
 box('data',400,500,300,100,['Local data only','Profiles / demo vacancies']),
], [('graduate','system','HTTPS / local HTTP'),('admin','system','Manage catalog'),('system','data','Read / persist')],height=660)

draw('components','Component Diagram — draft / modular monolith',[
 box('browser',20,190,180,100,['Browser','React + TypeScript']),
 box('api',305,145,240,105,['FastAPI routers','Validation / CRUD','FR-03–FR-06 / FR-10']),
 box('auth',305,355,240,105,['Auth / security','JWT + sessions + Argon2id','FR-01 / FR-02']),
 box('ai',635,145,240,105,['AI matching module','Score / gaps / fingerprint','FR-07–FR-09 / FR-11']),
 box('orm',635,355,240,105,['Models / SQLAlchemy','Session / migrations','NFR-02']),
 box('model',635,565,240,85,['Optional local embeddings','Keyword fallback']),
 box('db',940,355,140,105,['PostgreSQL','Persistent','source of truth']),
], [('browser','api','/api JSON'),('api','auth','Authorize'),('api','ai','Analyze'),('api','orm','CRUD'),('auth','orm','Sessions'),('orm','db','SQL'),('ai','model','Optional','dashed')],height=705,boundary=(270,65,640,610,'Backend process — 127.0.0.1:8000'))

draw('use-cases','Use Case Diagram — protected application scenarios',[
 box('graduate',10,250,180,120,['Student / graduate'],'actor'),
 box('admin',910,250,180,120,['Administrator'],'actor'),
 box('auth',385,100,330,70,['UC-01: Sign in / session']),
 box('profile',260,230,280,90,['UC-02: Manage profile','Education / skills / portfolio'],'usecase'),
 box('jobs',260,380,280,85,['UC-03: Browse jobs','View match and explanation'],'usecase'),
 box('growth',260,535,280,85,['UC-04: Review gaps','Update and recalculate'],'usecase'),
 box('catalog',610,230,260,90,['UC-05: Manage jobs','Requirements and catalogs'],'usecase'),
 box('users',610,420,260,85,['UC-06: Manage users','Inspect statistics'],'usecase'),
], [('graduate','auth','','association'),('admin','auth','','association'),('graduate','profile','','association'),('graduate','jobs','','association'),('graduate','growth','','association'),('admin','catalog','','association'),('admin','users','','association')],height=730,boundary=(220,65,680,620,'AITU Career — active session is a precondition of protected cases'))

# Auth is a use case, not a component rectangle.
model=json.loads((OUT/'use-cases.json').read_text(encoding='utf-8'))
model['nodes'][2]['kind']='usecase'
draw('use-cases',model['title'],model['nodes'],model['edges'],model['width'],model['height'],model['boundary'])

(OUT/'context.mmd').write_text('''flowchart LR
  Graduate[Student / graduate] -->|Profile and analysis| App[AITU Career]
  Admin[Administrator] -->|Jobs and catalogs| App
  App --> Data[(Local profiles and demo vacancies)]
''',encoding='utf-8')
(OUT/'components.mmd').write_text('''flowchart LR
  Browser[React / TypeScript] -->|REST / JSON| API
  subgraph Backend[FastAPI modular monolith]
    API[Routers and validation] --> Auth[JWT / sessions / Argon2id]
    API --> AI[Score / gaps / recommendations]
    API --> ORM[SQLAlchemy models / session]
    AI -.-> Optional[Local embedding cache / fallback]
  end
  ORM --> DB[(PostgreSQL)]
''',encoding='utf-8')
(OUT/'use-cases.puml').write_text('''@startuml
left to right direction
actor "Student / graduate" as Student
actor Administrator as Admin
rectangle "AITU Career" {
  usecase "UC-01: Sign in / session" as Login
  usecase "UC-02: Manage profile / portfolio" as Profile
  usecase "UC-03: Browse jobs / matching" as Jobs
  usecase "UC-04: Review gaps / recalculate" as Growth
  usecase "UC-05: Manage jobs / catalogs" as Catalog
  usecase "UC-06: Manage users / statistics" as Users
  note bottom
    Active authorized session is a precondition
    of all protected use cases.
  end note
}
Student -- Login
Admin -- Login
Student -- Profile
Student -- Jobs
Student -- Growth
Admin -- Catalog
Admin -- Users
@enduml
''',encoding='utf-8')
print('Wrote 3 editable diagrams and readable SVG exports:',OUT)

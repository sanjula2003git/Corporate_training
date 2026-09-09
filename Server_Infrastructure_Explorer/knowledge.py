"""Local lexical retrieval over reviewed web notes; no external API required."""
import json,re,math
from collections import Counter
from pathlib import Path

PATH=Path(__file__).resolve().parent/'knowledge_base'/'knowledge.json'
STOP=set('a an the what why how is are was were to for from of in on and or it this that do does can could would should please me give tell about explain more simple simply understand example examples real world life another different show use used uses i want know'.split())
STOP.update('with situation part result concrete did didn not don help get related which topic concept'.split())
ALIASES={'processor':'cpu','processors':'cpu','memory':'ram','nic':'network','ethernet':'network','bmc':'bmc','idrac':'bmc','psu':'psu','power':'psu','gpu':'gpu','accelerator':'gpu','nvme':'storage_interface','sata':'storage_interface','sas':'storage_interface','motherboard':'motherboard','blade':'blade_servers','tower':'tower_servers','rack':'rack_servers'}
ALIASES.update(cpu='cpu',ram='ram',network='network',storage='storage_interface',architecture='server_architecture',purpose='server_purpose',management='bmc',accelerators='gpu')
SUBJECT_HINTS={'1u':'rack_servers','2u':'rack_servers','ecc':'ram','dimm':'ram','dimms':'ram','rdimm':'ram','cache':'cpu','registers':'cpu'}
def tokens(text):
    words=[w for w in re.findall(r'[a-z0-9]+',text.lower()) if w not in STOP and len(w)>1]
    return [w[:-1] if w.endswith('s') and w[:-1] in ALIASES else w for w in words]
def load():
    try:return json.loads(PATH.read_text(encoding='utf-8'))
    except (OSError,ValueError):return {'sources':[],'chunks':[]}

def search(query,topic_id=None,limit=4,exclude=()):
    chunks=load()['chunks'];words=tokens(query);terms=set(words)
    explicit={ALIASES[w] for w in words if w in ALIASES}
    if not explicit:explicit={SUBJECT_HINTS[w] for w in words if w in SUBJECT_HINTS}
    # Topic words select a subject; remaining words determine the best passage.
    detail={w for w in terms if w not in ALIASES and w not in {'server','servers','infrastructure','interface','controller','supply','mean','means','between','difference','versus','vs'}}
    example=bool(re.search(r'example|real[ -]?world|scenario|real life',query,re.I))
    counts=[Counter(tokens(c['heading']+' '+c['text'])) for c in chunks]
    scores=[]
    for c,bag in zip(chunks,counts):
        if c['id'] in exclude:continue
        topical=c['topic_id'] in explicit if explicit else c['topic_id']==topic_id
        if not topical and topic_id and not explicit:continue
        matched=detail & bag.keys()
        if detail and not matched:continue
        if not topical and explicit:continue
        score=2 if topical else 0
        for word in terms & bag.keys():
            frequency=sum(word in b for b in counts)
            score+=math.log(1+(len(chunks)-frequency+.5)/(frequency+.5))*bag[word]/(bag[word]+.5)
        if example and re.search(r'example|use case|services|applications',c['heading'],re.I):score+=4
        if score or not words:scores.append((score,c))
    scores.sort(key=lambda x:x[0],reverse=True)
    return [c for _,c in scores[:limit]]

def citations(chunks):
    seen=set();links=[]
    for c in chunks:
        if c['url'] not in seen:links.append(f"[{c['source_title']}]({c['url']})");seen.add(c['url'])
    return ' · '.join(links)

def answer(query,topic_id,history=()):
    previous='\n'.join(m.get('content','') for m in history if m.get('role')=='assistant')
    followup=bool(re.search(r'another|different|repeat|more example',query,re.I)) or any(m.get('role')=='user' and m.get('content','').strip().lower()==query.strip().lower() for m in history)
    excluded=[c['id'] for c in load()['chunks'] if f"**{c['heading']}**" in previous] if followup else []
    found=search(query,topic_id,3,excluded)
    if not found:
        return 'I couldn’t find '+('another matching note' if excluded else 'a matching answer')+' in the saved sources. Try a specific term such as ECC, cache, NVMe or remote management, or browse the collected material below. I won’t invent an answer.'
    paragraphs=['**From the saved server knowledge base**']
    for c in found:paragraphs.append(f"**{c['heading']}**\n\n{c['text']}\n\nSource: [{c['source_title']}]({c['url']})")
    paragraphs.append('These are retrieved, reviewed notes. Connect the AI tutor for a conversational explanation of this evidence.')
    return '\n\n'.join(paragraphs)

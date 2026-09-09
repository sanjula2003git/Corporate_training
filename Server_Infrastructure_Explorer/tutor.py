"""Session-scoped tutoring. Credentials stay on the Python server."""
import re
from copy import deepcopy
from knowledge import answer as knowledge_answer

DEFAULT_PROFILE={'interests':'','avoid':'','style':'Step by step','level':'Beginner','language':'English'}

def learn_preferences(message, profile):
    """Only retain preferences the learner explicitly states, never guess identity."""
    p=deepcopy(profile)
    for pattern,key in [(r'\b(?:i like|i love|i enjoy|use examples (?:about|from))\s+([^.!?\n]{1,100})','interests'),
                        (r"\b(?:i dislike|i hate|i don['’]?t like|avoid|no examples about)\s+([^.!?\n]{1,100})",'avoid')]:
        matches=re.findall(pattern,message,re.I)
        if matches:p[key]=matches[-1].strip()
    if re.search(r"didn['’]?t understand|don['’]?t understand|simpler|confus",message,re.I):
        p['style']='Step by step';p['level']='Beginner'
    if re.search(r'\b(?:keep it short|brief|short answer)\b',message,re.I):p['style']='Short answers'
    if re.search(r'\b(?:use an analogy|use analogies)\b',message,re.I):p['style']='Analogies'
    if re.search(r'\b(?:more technical|advanced explanation)\b',message,re.I):p['level']='More technical'
    language=re.search(r'(?:answer|explain|speak|reply)\b[^.!?]{0,100}?\bin (English|Tamil|Hindi|Telugu|Kannada|Malayalam|Spanish|French)\b',message,re.I)
    if language:p['language']=language.group(1).title()
    return p

def offline_reply(lesson,message,profile,history=None):
    p=learn_preferences(message,profile)
    note='I’ve updated your learning preferences for this session.\n\n' if p!=profile else ''
    if re.search(r'where.*(?:model|3d)|find.*(?:model|3d)',message,re.I):
        return note+lesson['spot'],p
    return note+knowledge_answer(message,lesson['id'],history or []),p


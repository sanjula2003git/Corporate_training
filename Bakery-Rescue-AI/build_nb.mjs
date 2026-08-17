import fs from"node:fs";import path from"node:path";import{fileURLToPath}from"node:url";
const root=path.dirname(fileURLToPath(import.meta.url)),src=fs.readFileSync(path.join(root,"build_nb.py"),"utf8"),pyCore=fs.readFileSync(path.join(root,"bakery.py"),"utf8");
const tokens=[];let m;const blocks={},starts=[...pyCore.matchAll(/^(?:def|class)\s+([A-Za-z_]\w*)/gm)].map(x=>({name:x[1],at:x.index}));
for(let i=0;i<starts.length;i++)blocks[starts[i].name]=pyCore.slice(starts[i].at,i+1<starts.length?starts[i+1].at:pyCore.length).trim();blocks.__preamble__=pyCore.slice(0,pyCore.search(/^def\s+/m)).trim();
const triple=/\b(md|co)\(r?"""([\s\S]*?)"""\)/g;while((m=triple.exec(src)))tokens.push({at:m.index,type:m[1],text:m[2].trim()});
const single=/\b(md|co)\("((?:[^"\\]|\\.)*)"\)/g;while((m=single.exec(src))){let t=m[2].replace(/\\n/g,"\n").replace(/\\"/g,'"');tokens.push({at:m.index,type:m[1],text:t.trim()});}
const coreCall=/\bcore\((?="[^)]*\))([^)]*)\)/g;while((m=coreCall.exec(src))){const names=[...m[1].matchAll(/"([^"]+)"/g)].map(x=>x[1]);tokens.push({at:m.index,type:"co",text:names.map(n=>blocks[n]).join("\n\n")});}
tokens.sort((a,b)=>a.at-b.at);const cells=tokens.map(t=>t.type==="md"?{cell_type:"markdown",metadata:{},source:t.text.split(/(?<=\n)/)}:{cell_type:"code",execution_count:null,metadata:{},outputs:[],source:t.text.split(/(?<=\n)/)});
const nb={cells,metadata:{kernelspec:{display_name:"Python 3",language:"python",name:"python3"},language_info:{name:"python",version:"3"},colab:{name:"Bakery_Rescue_AI.ipynb",provenance:[]}},nbformat:4,nbformat_minor:5};
const out=path.join(root,"Bakery_Rescue_AI.ipynb");fs.writeFileSync(out,JSON.stringify(nb,null,1)+"\n","utf8");console.log(`Wrote ${path.basename(out)}: ${cells.length} cells`);

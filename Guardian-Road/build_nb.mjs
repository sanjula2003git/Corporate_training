// Local fallback notebook builder for machines without Python. The canonical source is build_nb.py.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root=path.dirname(fileURLToPath(import.meta.url));
const builder=fs.readFileSync(path.join(root,"build_nb.py"),"utf8");
const guardian=fs.readFileSync(path.join(root,"guardian.py"),"utf8");
const tokens=[];
const triple=/\b(md|co)\(r?"""([\s\S]*?)"""\)/g;
let m;
while((m=triple.exec(builder))) tokens.push({at:m.index,type:m[1],text:m[2].trim()});
const single=/\b(md|co)\("((?:[^"\\]|\\.)*)"\)/g;
while((m=single.exec(builder))){
  const text=JSON.parse('"'+m[2].replace(/\n/g,"\\n")+'"');
  tokens.push({at:m.index,type:m[1],text:text.trim()});
}
const injectAt=builder.indexOf('co("# Guardian Road simulation core');
tokens.push({at:injectAt,type:"co",text:"# Guardian Road simulation core — kept in guardian.py in the project\n"+guardian});
tokens.sort((a,b)=>a.at-b.at);
const cells=tokens.map(t=>t.type==="md"
  ? {cell_type:"markdown",metadata:{},source:t.text.split(/(?<=\n)/)}
  : {cell_type:"code",execution_count:null,metadata:{},outputs:[],source:t.text.split(/(?<=\n)/)});
const nb={cells,metadata:{kernelspec:{display_name:"Python 3",language:"python",name:"python3"},
  language_info:{name:"python",version:"3"},colab:{name:"Guardian_Road_AI_Safety_Shield.ipynb",provenance:[]}},
  nbformat:4,nbformat_minor:5};
const out=path.join(root,"Guardian_Road_AI_Safety_Shield.ipynb");
fs.writeFileSync(out,JSON.stringify(nb,null,1)+"\n","utf8");
console.log(`Wrote ${path.basename(out)}: ${cells.length} cells`);

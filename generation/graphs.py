from __future__ import annotations
from fractions import Fraction

TOPOLOGIES={
 "chain":{"nodes":["root","scaled","adjusted","endpoint","sibling"],"edges":[["root","scaled"],["scaled","adjusted"],["adjusted","endpoint"],["root","sibling"]]},
 "fork_merge":{"nodes":["root","branch_a","branch_b","merge","endpoint","sibling"],"edges":[["root","branch_a"],["root","branch_b"],["branch_a","merge"],["branch_b","merge"],["merge","endpoint"],["root","sibling"]]},
 "two_source":{"nodes":["root","external","merge","scaled","endpoint","audit"],"edges":[["root","merge"],["external","merge"],["merge","scaled"],["scaled","endpoint"],["external","audit"]]},
}

def evaluate_graph(slug:str,root:Fraction,p:dict[str,int])->dict[str,Fraction]:
    if slug=="chain":
        scaled=root*p["k"]; adjusted=scaled-p["d"]
        return {"root":root,"scaled":scaled,"adjusted":adjusted,"endpoint":adjusted/p["q"],"sibling":root+p["s"]}
    if slug=="fork_merge":
        a=root+p["d"]; b=root*p["k"]; merge=a+b
        return {"root":root,"branch_a":a,"branch_b":b,"merge":merge,"endpoint":merge/p["q"],"sibling":root-p["s"]}
    if slug=="two_source":
        merge=root+p["external"]; scaled=merge*p["k"]
        return {"root":root,"external":Fraction(p["external"]),"merge":merge,"scaled":scaled,"endpoint":scaled-p["d"],"audit":Fraction(p["external"]*p["q"])}
    raise ValueError(slug)

def scenario_text(slug:str,p:dict[str,int],fields=None)->str:
    definitions={
      'chain':{
        'scaled':f"scaled: multiply root by {p['k']}.",
        'adjusted':f"adjusted: subtract {p['d']} from scaled.",
        'endpoint':f"endpoint: divide adjusted by {p['q']}.",
        'sibling':f"sibling: add {p['s']} to root."},
      'fork_merge':{
        'branch_a':f"branch_a: add {p['d']} to root.",
        'branch_b':f"branch_b: multiply root by {p['k']}.",
        'merge':"merge: Add the two values branch_a and branch_b.",
        'endpoint':f"endpoint: divide merge by {p['q']}.",
        'sibling':f"sibling: subtract {p['s']} from root."},
      'two_source':{
        'external':f"external: use the supplied value {p['external']}.",
        'merge':"merge: Add root and external.",
        'scaled':f"scaled: multiply merge by {p['k']}.",
        'endpoint':f"endpoint: subtract {p['d']} from scaled.",
        'audit':f"audit: multiply external by {p['q']}."}}
    if slug not in definitions: raise ValueError(slug)
    selected=definitions[slug]
    return ' '.join(text for field,text in selected.items() if fields is None or field in fields)
    raise ValueError(slug)

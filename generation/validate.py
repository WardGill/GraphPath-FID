from __future__ import annotations
from collections import Counter
from fractions import Fraction
from .catalog import CATALOG
from .graphs import TOPOLOGIES

def _canonical(slug:str,operands:tuple[int,...])->tuple:
    if slug=="negative_product_negative": return tuple(sorted(operands))
    if slug=="fraction_component_add": return tuple(sorted(((operands[0],operands[1]),(operands[2],operands[3]))))
    return operands

def _fraction(value): return Fraction(str(value))
def _fmt(value:Fraction): return value.numerator if value.denominator==1 else f"{value.numerator}/{value.denominator}"

def _sig(graph):
    indeg=Counter(); out=Counter()
    for a,b in graph["edges"]: out[a]+=1; indeg[b]+=1
    return sorted((indeg[n],out[n]) for n in graph["nodes"])

def _oracle(graph:str,root:Fraction,p:dict)->dict:
    """Independent arithmetic oracle; does not import generator/evaluate_graph."""
    if graph=="chain":
        scaled=root*p["k"]; adjusted=scaled-p["d"]
        return {"root":root,"scaled":scaled,"adjusted":adjusted,"endpoint":adjusted/p["q"],"sibling":root+p["s"]}
    if graph=="fork_merge":
        branch_a=root+p["d"]; branch_b=root*p["k"]; merge=branch_a+branch_b
        return {"root":root,"branch_a":branch_a,"branch_b":branch_b,"merge":merge,"endpoint":merge/p["q"],"sibling":root-p["s"]}
    if graph=="two_source":
        external=Fraction(p["external"]); merge=root+external; scaled=merge*p["k"]
        return {"root":root,"external":external,"merge":merge,"scaled":scaled,"endpoint":scaled-p["d"],"audit":external*p["q"]}
    raise ValueError(graph)

def _expected(record:dict,fields:list[str])->dict:
    return {field:_fmt(record[field]) for field in fields}

def _application_oracle(slug:str,root:Fraction,p:dict)->Fraction:
    if slug=="inverse_as_same": return root*p["k"]+p["d"]
    if slug=="left_to_right": return (root+p["d"])*p["q"]
    if slug=="square_as_double": return root+p["d"]
    if slug=="negative_product_negative": return Fraction(p["external"])+root*p["k"]
    if slug in {"distribute_first_only","fraction_component_add","division_commutative"}: return root*(p["q"] if slug=="distribute_first_only" else p["k"])
    if slug=="round_down": return root/p["q"]
    raise ValueError(slug)

def validate_dataset(data:dict)->dict:
    failures=[]; families=data["families"]
    if len({_sig(g).__str__() for g in TOPOLOGIES.values()})!=3: failures.append("topologies_not_distinct")
    cells=Counter((f["mechanism"],f["split"],f["difficulty"],f["graph"]) for f in families)
    split_counts=Counter((f["mechanism"],f["split"]) for f in families); graph_counts=Counter(f["graph"] for f in families)
    ids=set(); roots=set()
    for f in families:
        fid=f["family_id"]
        if fid in ids: failures.append("duplicate_family_id:"+fid)
        ids.add(fid); roots.add((f["mechanism"],tuple(f["operands"])))
        mechanism=CATALOG.get(f["mechanism"])
        if mechanism is None: failures.append("unknown_mechanism:"+fid); continue
        operands=tuple(f["operands"]); correct=mechanism.correct(operands); defective=mechanism.defective(operands)
        if _fraction(f["standard_root"])!=correct or _fraction(f["defect_root"])!=defective: failures.append("root_oracle_mismatch:"+fid)
        if correct==defective: failures.append("root_collision:"+fid)
        standard=_oracle(f["graph"],correct,f["graph_parameters"]); defect=_oracle(f["graph"],defective,f["graph_parameters"])
        probes={p["route"]:p for p in f["probes"]}
        if set(probes)!={"root","near","target","sibling","alternate","offpath"}: failures.append("route_set:"+fid); continue
        for route in ("root","near","target","sibling"):
            p=probes[route]
            if p["standard"]!=_expected(standard,p["fields"]) or p["defect"]!=_expected(defect,p["fields"]): failures.append("probe_oracle_mismatch:"+fid+":"+route)
        expected_roles={"root":"root_task","near":"root_descendant","target":"root_descendant",
                        "sibling":"root_independent" if f["graph"]=="two_source" else "root_descendant"}
        if any(probes[r].get("causal_role")!=role for r,role in expected_roles.items()): failures.append("causal_role_mismatch:"+fid)
        target=probes["target"]
        if target["standard"]==target["defect"]: failures.append("target_collision:"+fid)
        for route,scope in (("alternate","target_endpoint_via_bypass"),("offpath","separate_matched_pipeline")):
            control=probes[route]
            if control.get("scope")!=scope: failures.append("control_scope:"+fid+":"+route)
            if control["fields"]!=target["fields"]: failures.append("control_field_mismatch:"+fid+":"+route)
            if control["standard"]!=control["defect"]: failures.append("control_contaminated:"+fid+":"+route)
            supplied=control.get("supplied_root")
            if supplied is None or control["standard"]!=_expected(_oracle(f["graph"],_fraction(supplied),f["graph_parameters"]),control["fields"]): failures.append("control_oracle_mismatch:"+fid+":"+route)
        if probes["alternate"]["standard"]!=target["standard"]: failures.append("alternate_endpoint_mismatch:"+fid)
        if probes["offpath"]["standard"]==target["standard"]: failures.append("offpath_not_separate:"+fid)
        if len(f.get("transfer_probes",[]))!=2: failures.append("transfer_count:"+fid)
        if len(f.get("retention_probes",[]))!=2: failures.append("retention_count:"+fid)
        all_transfer=f.get("transfer_probes",[])+f.get("retention_probes",[])
        if len({_canonical(f["mechanism"],tuple(p["operands"])) for p in all_transfer})!=4:
            failures.append("duplicate_transfer_or_retention_within_family:"+fid)
        for transfer in all_transfer:
            t=tuple(transfer["operands"])
            if _fraction(transfer["standard"])!=mechanism.correct(t) or _fraction(transfer["defect"])!=mechanism.defective(t): failures.append("transfer_oracle_mismatch:"+fid)
            if transfer["standard"]==transfer["defect"]: failures.append("transfer_collision:"+fid)
        application=f.get("contextual_application",{}); app_fields=application.get("fields",[])
        if len(app_fields)!=2 or application.get("semantic_role")!="cross_context_application": failures.append("application_schema:"+fid)
        else:
            expected_standard={app_fields[0]:_fmt(correct),app_fields[1]:_fmt(_application_oracle(f["mechanism"],correct,f["graph_parameters"]))}
            expected_defect={app_fields[0]:_fmt(defective),app_fields[1]:_fmt(_application_oracle(f["mechanism"],defective,f["graph_parameters"]))}
            if application.get("standard")!=expected_standard or application.get("defect")!=expected_defect: failures.append("application_oracle_mismatch:"+fid)
        prompt_text=" ".join(p["prompt"] for p in f["probes"])
        if "final_value =" in prompt_text: failures.append("formula_leak:"+fid)
        if f["graph"] in {"fork_merge","two_source"} and not any(word in prompt_text for word in ("Add the two","Add root")): failures.append("ambiguous_merge:"+fid)
    if len(cells)!=data["mechanisms"]*27 or any(n!=1 for n in cells.values()): failures.append("not_full_factorial")
    if len(split_counts)!=data["mechanisms"]*3 or any(n!=9 for n in split_counts.values()): failures.append("unbalanced_splits")
    if len(set(graph_counts.values()))!=1: failures.append("unbalanced_graphs")
    for mechanism in CATALOG:
        by_split={split:set() for split in ("development","validation","test")}
        for f in (x for x in families if x["mechanism"]==mechanism):
            by_split[f["split"]].add(_canonical(mechanism,tuple(f["operands"])))
            by_split[f["split"]].update(_canonical(mechanism,tuple(p["operands"])) for p in f["transfer_probes"])
            by_split[f["split"]].update(_canonical(mechanism,tuple(p["operands"])) for p in f.get("retention_probes",[]))
            if len({_canonical(mechanism,tuple(p["operands"])) for p in f["transfer_probes"]})!=2: failures.append("duplicate_transfer_within_family:"+f["family_id"])
        if any(by_split[a]&by_split[b] for a,b in (("development","validation"),("development","test"),("validation","test"))): failures.append("cross_split_parameter_leak:"+mechanism)
    return {"status":"PASS" if not failures else "FAIL","families":len(families),"mechanisms":data["mechanisms"],
            "factorial_cells":len(cells),"graph_counts":dict(graph_counts),
            "split_counts":{f"{a}|{b}":n for (a,b),n in split_counts.items()},
            "unique_root_parameterizations":len(roots),"failures":failures}

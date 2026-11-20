from __future__ import annotations
import csv,hashlib,io,json,random,zipfile
from fractions import Fraction
from pathlib import Path
from .catalog import CATALOG
from .graphs import TOPOLOGIES,evaluate_graph,scenario_text

LETTERS="ABCD"
EXCLUSION_REASONS={
 161:"unit-conversion-specific and overlaps the broader inverse-operation mechanism",
 1248:"label does not specify a unique deterministic rounding transformation",
 2271:"near-duplicate of selected inverse-operation mechanism 1214",
 1880:"requires relational-symbol task templates rather than a scalar root rule",
 1988:"rounding direction is context-dependent; label alone does not define one transformation",
 2143:"overlaps selected bracket-expansion mechanism 220",
 974:"overlaps selected sign-rule mechanism 1597",
 77:"function-machine order errors require sequence-specific representations",
 108:"two-term sequence inference is underdetermined without an additional convention",
 2392:"degree-of-accuracy label does not specify a unique deterministic transformation",
 1990:"requires diagram geometry not represented in the text-only benchmark",
 113:"requires symbolic factorization outputs rather than the common numeric interface",
 1072:"index-multiplication label requires sequence-specific task semantics",
 172:"near-duplicate of selected fraction component-wise mechanism 217",
 1510:"near-duplicate of selected noncommutativity mechanism 2359",
 2355:"requires diagram-based rotational symmetry",
 2481:"decimal-place transformation is retained for a future decimal-focused extension",
 1527:"requires diagram geometry and potentially ambiguous composite-shape decomposition",
}
INCLUSION_REASONS={
 1214:"deterministic equation-solving rule with broad support and a unique numeric counterfactual",
 1507:"deterministic operation-order rule that tests procedural sequencing",
 2316:"deterministic operator substitution with strong Eedi support",
 1597:"deterministic sign-rule error with a unique counterfactual result",
 220:"deterministic partial distribution rule distinct from pure operator substitution",
 217:"deterministic relational-structure error in fraction addition",
 2359:"deterministic noncommutativity error for division",
 1379:"deterministic directional rounding error on cases that require rounding up",
}
def fmt(x:Fraction): return x.numerator if x.denominator==1 else f"{x.numerator}/{x.denominator}"

def canonical_operands(slug:str,operands:tuple[int,...])->tuple:
    if slug=="negative_product_negative": return tuple(sorted(operands))
    if slug=="fraction_component_add": return tuple(sorted(((operands[0],operands[1]),(operands[2],operands[3]))))
    return operands

def eedi_evidence(path:Path)->dict[int,dict]:
    with zipfile.ZipFile(path) as z:
        mapping={int(r["MisconceptionId"]):r["MisconceptionName"] for r in csv.DictReader(io.TextIOWrapper(z.open("misconception_mapping.csv"),encoding="utf-8-sig"))}
        rows=list(csv.DictReader(io.TextIOWrapper(z.open("train.csv"),encoding="utf-8-sig")))
    evidence={m.eedi_id:{"misconception_id":m.eedi_id,"official_name":mapping[m.eedi_id],"labeled_options":0,"question_ids":set()} for m in CATALOG.values()}
    for row in rows:
        for letter in LETTERS:
            raw=row[f"Misconception{letter}Id"].strip()
            if raw:
                mid=int(float(raw))
                if mid in evidence:
                    evidence[mid]["labeled_options"]+=1; evidence[mid]["question_ids"].add(int(row["QuestionId"]))
    for item in evidence.values():
        item["distinct_questions"]=len(item["question_ids"]); item["question_ids"]=sorted(item["question_ids"])
    return evidence

def eedi_candidate_audit(path:Path)->list[dict]:
    with zipfile.ZipFile(path) as z:
        mapping={int(r["MisconceptionId"]):r["MisconceptionName"] for r in csv.DictReader(io.TextIOWrapper(z.open("misconception_mapping.csv"),encoding="utf-8-sig"))}
        rows=list(csv.DictReader(io.TextIOWrapper(z.open("train.csv"),encoding="utf-8-sig")))
    counts={mid:{"labeled_options":0,"question_ids":set()} for mid in mapping}
    for row in rows:
        for letter in LETTERS:
            raw=row[f"Misconception{letter}Id"].strip()
            if raw:
                mid=int(float(raw)); counts[mid]["labeled_options"]+=1; counts[mid]["question_ids"].add(int(row["QuestionId"]))
    selected={m.eedi_id for m in CATALOG.values()}; audit=[]
    for mid,item in counts.items():
        questions=len(item["question_ids"])
        if item["labeled_options"]>=14 and questions>=9:
            included=mid in selected
            audit.append({"misconception_id":mid,"official_name":mapping[mid],"labeled_options":item["labeled_options"],
                          "distinct_questions":questions,"decision":"include" if included else "exclude",
                          "reason":INCLUSION_REASONS[mid] if included else EXCLUSION_REASONS[mid]})
    return sorted(audit,key=lambda x:x["misconception_id"])

def operands_for(slug:str,difficulty:int,rng:random.Random)->tuple[int,...]:
    # Each mechanism needs five disjoint operand sets per family (root, two
    # immediate transfers, two retention probes) without cross-split reuse.
    lo,hi={1:(2,15),2:(16,30),3:(31,50)}[difficulty]
    if slug=="inverse_as_same":
        a=rng.randint(lo,hi); return a,a+rng.randint(lo,hi)
    if slug in {"left_to_right","distribute_first_only"}: return tuple(rng.sample(range(lo,hi+1),3))
    if slug=="square_as_double":
        square_lo,square_hi={1:(3,55),2:(56,110),3:(111,170)}[difficulty]
        return (rng.randint(square_lo,square_hi),)
    if slug=="negative_product_negative": return tuple(rng.sample(range(lo,hi+1),2))
    if slug=="fraction_component_add":
        b,d=rng.sample(range(max(3,lo),hi+3),2); return rng.randint(1,b-1),b,rng.randint(1,d-1),d
    if slug=="division_commutative":
        a,b=rng.sample(range(lo,hi+1),2); return a,b
    if slug=="round_down": return (10*rng.randint(max(1,lo//2),hi)+rng.randint(5,9),)
    raise ValueError(slug)

def graph_params(rng:random.Random)->dict[str,int]:
    return {"k":rng.randint(2,5),"d":rng.randint(1,7),"q":rng.randint(2,5),"s":rng.randint(2,8),"external":rng.randint(3,12)}

def build_contextual_application(slug:str,root_prompt:str,standard_root:Fraction,defect_root:Fraction,p:dict)->dict:
    specs={
      "inverse_as_same":("Treat x as the input to a linear function. Compute function_value = {k} times x plus {d}.","x","function_value",lambda r:r*p["k"]+p["d"]),
      "left_to_right":("Treat root as a points subtotal. Add a fixed bonus of {d}, then award that adjusted subtotal in each of {q} rounds.","subtotal","tournament_points",lambda r:(r+p["d"])*p["q"]),
      "square_as_double":("Treat root as the tiled area of a square display. Add {d} replacement tiles to obtain inventory_tiles.","area","inventory_tiles",lambda r:r+p["d"]),
      "negative_product_negative":("Treat root as the balance change in one round. Starting from {external}, apply that change for {k} rounds.","round_change","final_balance",lambda r:Fraction(p["external"])+r*p["k"]),
      "distribute_first_only":("Treat root as the items produced in one batch. Compute the output from {q} equal batches.","batch_output","total_output",lambda r:r*p["q"]),
      "fraction_component_add":("Treat root as the fraction of one tank filled per cycle. Compute the filled amount after {k} identical cycles.","cycle_fraction","filled_amount",lambda r:r*p["k"]),
      "division_commutative":("Treat root as a unit rate. Compute the amount delivered over {k} equal units.","unit_rate","delivered_amount",lambda r:r*p["k"]),
      "round_down":("Treat root as the rounded attendance estimate. Divide it equally among {q} reporting groups.","rounded_attendance","per_group_estimate",lambda r:r/p["q"]),
    }
    text,root_field,application_field,fn=specs[slug]
    fields=[root_field,application_field]
    prompt=root_prompt+" "+text.format(**p)+" Return JSON containing: "+", ".join(fields)+"."
    return {"prompt":prompt,"fields":fields,"semantic_role":"cross_context_application",
            "standard":{root_field:fmt(standard_root),application_field:fmt(fn(standard_root))},
            "defect":{root_field:fmt(defect_root),application_field:fmt(fn(defect_root))}}

def build_probes(root_prompt:str,graph:str,p:dict,standard:dict,defect:dict)->list[dict]:
    if graph=="chain": routes={"root":["root"],"near":["root","scaled"],"target":["root","scaled","adjusted","endpoint"],"sibling":["root","sibling"]}
    elif graph=="fork_merge": routes={"root":["root"],"near":["root","branch_a","branch_b"],"target":["root","branch_a","branch_b","merge","endpoint"],"sibling":["root","sibling"]}
    else: routes={"root":["root"],"near":["root","external","merge"],"target":["root","external","merge","scaled","endpoint"],"sibling":["external","audit"]}
    probes=[]
    causal_roles={"root":"root_task","near":"root_descendant","target":"root_descendant",
                  "sibling":"root_independent" if graph=="two_source" else "root_descendant"}
    for route,fields in routes.items():
        lead=root_prompt if causal_roles[route]!='root_independent' else ''
        prompt=lead+" "+scenario_text(graph,p,fields)+" Return JSON containing: "+", ".join(fields)+"."
        probes.append({"route":route,"causal_role":causal_roles[route],"prompt":prompt,"fields":fields,
                       "standard":{k:fmt(standard[k]) for k in fields},"defect":{k:fmt(defect[k]) for k in fields}})
    # Both controls are field- and operation-matched to the target probe.
    target_fields=routes["target"]
    context=scenario_text(graph,p,target_fields)
    alternate_root=standard["root"]
    alternate_record=evaluate_graph(graph,alternate_root,p)
    alternate_expected={k:fmt(alternate_record[k]) for k in target_fields}
    probes.append({"route":"alternate","scope":"target_endpoint_via_bypass","supplied_root":fmt(alternate_root),
                   "prompt":f"Alternative-route control: bypass the preceding mathematics task and use the independently supplied root {fmt(alternate_root)}. {context} Return JSON containing: "+", ".join(target_fields)+".",
                   "fields":target_fields,"standard":alternate_expected,"defect":alternate_expected})
    offpath_root=alternate_root+Fraction(p["s"]+1)
    offpath_record=evaluate_graph(graph,offpath_root,p)
    offpath_expected={k:fmt(offpath_record[k]) for k in target_fields}
    probes.append({"route":"offpath","scope":"separate_matched_pipeline","supplied_root":fmt(offpath_root),
                   "prompt":f"Off-path control: evaluate a separate matched pipeline that is not downstream of the preceding mathematics task; its supplied root is {fmt(offpath_root)}. {context} Return JSON containing: "+", ".join(target_fields)+".",
                   "fields":target_fields,"standard":offpath_expected,"defect":offpath_expected})
    return probes

def build_dataset(eedi_zip:str|Path,per_mechanism:int=27,seed:int=20260906)->dict:
    if per_mechanism!=27: raise ValueError("v2 uses exactly 27 families per mechanism for a 3x3x3 split-difficulty-graph design")
    source=Path(eedi_zip); evidence=eedi_evidence(source); rng=random.Random(seed); families=[]
    for mechanism in CATALOG.values():
        ev=evidence[mechanism.eedi_id]
        if ev["labeled_options"]<14 or ev["distinct_questions"]<9: raise ValueError(f"insufficient Eedi support for {mechanism.slug}: {ev}")
        used=set()
        for index in range(per_mechanism):
            split_idx=index//9; within=index%9
            difficulty=within//3+1; graph=tuple(TOPOLOGIES)[within%3]
            operands=operands_for(mechanism.slug,difficulty,rng)
            while canonical_operands(mechanism.slug,operands) in used or mechanism.correct(operands)==mechanism.defective(operands): operands=operands_for(mechanism.slug,difficulty,rng)
            used.add(canonical_operands(mechanism.slug,operands)); params=graph_params(rng)
            standard=evaluate_graph(graph,mechanism.correct(operands),params); defect=evaluate_graph(graph,mechanism.defective(operands),params)
            split=("development","validation","test")[split_idx]
            transfer=[]
            for probe_index in range(4):
                transfer_operands=operands_for(mechanism.slug,difficulty,rng)
                while canonical_operands(mechanism.slug,transfer_operands) in used or mechanism.correct(transfer_operands)==mechanism.defective(transfer_operands): transfer_operands=operands_for(mechanism.slug,difficulty,rng)
                used.add(canonical_operands(mechanism.slug,transfer_operands))
                transfer.append({"probe_id":probe_index+1,"prompt":mechanism.prompt(transfer_operands)+" Return JSON containing: root.","operands":list(transfer_operands),
                                 "standard":fmt(mechanism.correct(transfer_operands)),"defect":fmt(mechanism.defective(transfer_operands))})
            immediate_transfer,retention_transfer=transfer[:2],transfer[2:]
            family={"family_id":f"{mechanism.slug}-{index:03d}","mechanism":mechanism.slug,"mechanism_class":mechanism.mechanism_class,
                    "source":{"dataset":"Eedi Mining Misconceptions in Mathematics","misconception_id":mechanism.eedi_id,"official_name":ev["official_name"],
                              "labeled_options":ev["labeled_options"],"distinct_questions":ev["distinct_questions"],"first_sorted_example_question_ids":ev["question_ids"][:5]},
                    "split":split,"difficulty":difficulty,"graph":graph,"topology":TOPOLOGIES[graph],"operands":list(operands),"graph_parameters":params,
                    "root_prompt":mechanism.prompt(operands),"learner_rule":mechanism.learner_rule,
                    "standard_root":fmt(mechanism.correct(operands)),"defect_root":fmt(mechanism.defective(operands)),
                    "transfer_probes":immediate_transfer,"retention_probes":retention_transfer}
            family["contextual_application"]=build_contextual_application(mechanism.slug,family["root_prompt"],mechanism.correct(operands),mechanism.defective(operands),params)
            family["probes"]=build_probes(family["root_prompt"],graph,params,standard,defect); families.append(family)
    payload={"schema":"graphpath-synthetic-v2","seed":seed,"per_mechanism":per_mechanism,"mechanisms":len(CATALOG),
             "prompt_revision":"20260915_distribution_rule_disambiguated_v4",
             "difficulty_basis":"operand_size_band_not_empirically_calibrated","families":families}
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode(); payload["content_sha256"]=hashlib.sha256(canonical).hexdigest()
    return payload

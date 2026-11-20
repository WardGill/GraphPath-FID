from __future__ import annotations
from dataclasses import dataclass
from .scoring import score_record
from .interventions import intervention_messages

TASKS=("root","transfer_1","transfer_2","application","near","target","sibling","alternate","offpath")
ARMS=("no_feedback","targeted_repair","matched_sham")
ARCHITECTURES=("stateless","session_memory","explicit_state")
RETENTION_TASKS=("retention_1","retention_2")

@dataclass(frozen=True)
class Trial:
    system:str
    user:str
    expected_fields:tuple[str,...]
    standard:dict
    defect:dict
    defect_relevant:bool

def task_record(family:dict,task:str)->tuple[str,list[str],dict,dict,bool]:
    if task=="root":
        probe=next(p for p in family["probes"] if p["route"]=="root")
        return probe["prompt"],probe["fields"],probe["standard"],probe["defect"],True
    if task.startswith("transfer_"):
        index=int(task.rsplit("_",1)[1])-1; probe=family["transfer_probes"][index]
        return probe["prompt"],["root"],{"root":probe["standard"]},{"root":probe["defect"]},True
    if task.startswith("retention_"):
        index=int(task.rsplit("_",1)[1])-1; probe=family["retention_probes"][index]
        return probe["prompt"],["root"],{"root":probe["standard"]},{"root":probe["defect"]},True
    if task=="application":
        probe=family["contextual_application"]
        return probe["prompt"],probe["fields"],probe["standard"],probe["defect"],True
    probe=next(p for p in family["probes"] if p["route"]==task)
    relevant=probe.get("causal_role") in {"root_task","root_descendant"}
    return probe["prompt"],probe["fields"],probe["standard"],probe["defect"],relevant

def build_trial(family:dict,task:str,condition:str,phase:str,arm:str="no_feedback",
                include_defect_rule:bool=False,wording:int=0)->Trial:
    if task not in TASKS+RETENTION_TASKS or condition not in {"healthy","defect"} or phase not in {"pre","post","retention"} or arm not in ARMS:
        raise ValueError("invalid v2 trial coordinate")
    if wording not in {0,1}: raise ValueError("wording must be 0 or 1")
    prompt,fields,standard,defect,relevant=task_record(family,task)
    system=("Return only one valid JSON object with every requested field." if wording==0 else
            "Include every requested field and output a valid JSON object only.")
    system+=' Each value must be an evaluated number or a quoted fraction string such as "7/5". Do not return unevaluated expressions. Field names identify the specific operations stated in the question.'
    parts=[]
    if condition=="healthy": parts.append("Use standard mathematics correctly.")
    elif include_defect_rule and relevant:
        parts.append("Simulate a learner with this initial rule, even when it is incorrect: "+family["learner_rule"]+
                     " Use this rule on related tasks unless subsequent relevant feedback changes it.")
    if phase=="post" and intervention_messages(family)[arm]: parts.append(intervention_messages(family)[arm])
    parts.append(prompt)
    return Trial(system," ".join(parts),tuple(fields),standard,defect,relevant)

def build_retention_trial(family:dict,task:str,condition:str,wording:int=0)->Trial:
    """Held-out isomorphic item; intervention is deliberately absent from this test message."""
    return build_trial(family,task,condition,"retention","no_feedback",
                       include_defect_rule=False,wording=wording)

def score_trial(parsed:dict,trial:Trial)->dict:
    scores=score_record(parsed,trial.standard,trial.defect)
    if not trial.defect_relevant or trial.standard==trial.defect:
        scores["defect_match"]=False
        scores["other"]=scores["format_complete"] and not scores["standard_match"]
    return scores

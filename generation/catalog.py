from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from typing import Callable

RootFn=Callable[[tuple[int,...]],Fraction]
PromptFn=Callable[[tuple[int,...]],str]

@dataclass(frozen=True)
class Mechanism:
    slug:str; eedi_id:int; mechanism_class:str
    correct:RootFn; defective:RootFn; prompt:PromptFn; learner_rule:str

CATALOG:dict[str,Mechanism]={
 "inverse_as_same":Mechanism("inverse_as_same",1214,"inverse-operation",
   lambda x:Fraction(x[1]-x[0]),lambda x:Fraction(x[1]+x[0]),
   lambda x:f"Solve x + {x[0]} = {x[1]} and report x as root.",
   "When isolating x, apply the same addition shown in the equation instead of its inverse."),
 "left_to_right":Mechanism("left_to_right",1507,"operation-order",
   lambda x:Fraction(x[0]+x[1]*x[2]),lambda x:Fraction((x[0]+x[1])*x[2]),
   lambda x:f"Evaluate {x[0]} + {x[1]} * {x[2]} and report it as root.",
   "Evaluate operations strictly from left to right, ignoring multiplication priority."),
 "square_as_double":Mechanism("square_as_double",2316,"operator-substitution",
   lambda x:Fraction(x[0]**2),lambda x:Fraction(2*x[0]),
   lambda x:f"Evaluate {x[0]} squared and report it as root.",
   "Interpret squaring a number as doubling it."),
 "negative_product_negative":Mechanism("negative_product_negative",1597,"sign-rule",
   lambda x:Fraction(x[0]*x[1]),lambda x:Fraction(-x[0]*x[1]),
   lambda x:f"Evaluate (-{x[0]}) * (-{x[1]}) and report it as root.",
   "Treat the product of two negative numbers as negative."),
 "distribute_first_only":Mechanism("distribute_first_only",220,"partial-rule-application",
   lambda x:Fraction(x[0]*(x[1]+x[2])),lambda x:Fraction(x[0]*x[1]+x[2]),
   lambda x:f"Expand and evaluate {x[0]}({x[1]} + {x[2]}); report root.",
   "When expanding a(b + c), compute a*b + c: multiply the outside factor by the first term only, then keep the second term unchanged and add it."),
 "fraction_component_add":Mechanism("fraction_component_add",217,"relational-structure",
   lambda x:Fraction(x[0],x[1])+Fraction(x[2],x[3]),lambda x:Fraction(x[0]+x[2],x[1]+x[3]),
   lambda x:f"Add {x[0]}/{x[1]} and {x[2]}/{x[3]}; report the reduced result as root.",
   "Add the two numerators and the two denominators separately."),
 "division_commutative":Mechanism("division_commutative",2359,"noncommutativity",
   lambda x:Fraction(x[0],x[1]),lambda x:Fraction(x[1],x[0]),
   lambda x:f"Evaluate {x[0]} / {x[1]}; report the reduced result as root.",
   "Reverse the dividend and divisor because division is treated as commutative."),
 "round_down":Mechanism("round_down",1379,"place-value-rounding",
   lambda x:Fraction(((x[0]+5)//10)*10),lambda x:Fraction((x[0]//10)*10),
   lambda x:f"Round {x[0]} to the nearest ten and report it as root.",
   "When the units digit requires rounding up, round down instead."),
}

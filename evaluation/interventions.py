from __future__ import annotations

STANDARD_RULES={
 "inverse_as_same":"When isolating an unknown, apply the inverse operation to both sides.",
 "left_to_right":"Apply multiplication before addition unless parentheses change the order.",
 "square_as_double":"Squaring n means multiplying n by itself, not multiplying it by two.",
 "negative_product_negative":"The product of two negative numbers is positive.",
 "distribute_first_only":"Multiply every term inside the parentheses by the outside factor.",
 "fraction_component_add":"Rewrite fractions with a common denominator before adding their numerators.",
 "division_commutative":"Division is ordered: keep the stated dividend and divisor in their original roles.",
 "round_down":"When rounding to the nearest ten, a units digit of five or more rounds upward.",
}

REPAIR_EXEMPLARS={
 "inverse_as_same":"For x + 101 = 250, subtract 101 from both sides, obtaining x = 149.",
 "left_to_right":"For 101 + 103 * 107, multiply first and then add, obtaining 11122.",
 "square_as_double":"For 181 squared, multiply 181 by itself, obtaining 32761.",
 "negative_product_negative":"For (-101) * (-103), the two negative signs give a positive product, 10403.",
 "distribute_first_only":"For 101(103 + 107), multiply both inner terms by 101, obtaining 21210.",
 "fraction_component_add":"For 101/211 + 103/223, use a common denominator, obtaining 44256/47053.",
 "division_commutative":"For 101 / 103, preserve the stated order, obtaining 101/103.",
 "round_down":"For 1005 rounded to the nearest ten, the units digit requires 1010.",
}
REPAIR_EXEMPLAR_OPERANDS={
 "inverse_as_same":(101,250),"left_to_right":(101,103,107),"square_as_double":(181,),
 "negative_product_negative":(101,103),"distribute_first_only":(101,103,107),
 "fraction_component_add":(101,211,103,223),"division_commutative":(101,103),"round_down":(1005,),
}

def _match_words(left:str,right:str)->tuple[str,str]:
    a,b=left.split(),right.split()
    neutral=("Keep the stated scope separate from other mathematical rules and verify each requested "
             "output field before returning the final JSON object").split()
    if len(a)<len(b): a.extend(neutral[:len(b)-len(a)])
    if len(b)<len(a): b.extend(neutral[:len(a)-len(b)])
    return " ".join(a)," ".join(b)

def intervention_messages(family:dict)->dict[str,str]:
    target=("Correction for later related tasks: "+STANDARD_RULES[family["mechanism"]]+" "
            "Worked check: "+REPAIR_EXEMPLARS[family["mechanism"]]+" "
            "Apply this correction only where the same mathematical rule is relevant.")
    sham=("Diagnostic feedback for later related tasks: a prior answer may contain a procedural error. "
          "Re-read the requested operation order, calculate each intermediate value, and independently check "
          "the final result before answering. Worked check: for 4 + 3, calculation and checking both give 7.")
    target,sham=_match_words(target,sham)
    return {"no_feedback":"","targeted_repair":target,"matched_sham":sham}

def validate_intervention_matching(family:dict)->dict:
    messages=intervention_messages(family); target=messages["targeted_repair"]; sham=messages["matched_sham"]
    return {"same_word_count":len(target.split())==len(sham.split()),
            "target_words":len(target.split()),"sham_words":len(sham.split()),
            "distinct":target!=sham,"has_example":all("Worked check:" in messages[x] for x in ("targeted_repair","matched_sham"))}

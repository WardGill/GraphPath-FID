# GraphPath-FID dataset card

## Design

Each family is one mechanism × split × operand-size band × graph topology combination. Graph keys `chain`, `fork_merge` and `two_source` refer to chain, branch-merge and dual-source respectively. These are computational dependency graphs. The difficulty field is an operand-size band.

| Field | Meaning |
| --- | --- |
| `family_id`, `split` | Family key and fixed development, validation, or test assignment. The paper evaluates the 72 test families. |
| `mechanism`, `mechanism_class`, `learner_rule` | Error mechanism and its executable rule expressed in natural language. |
| `operands`, `graph_parameters`, `topology` | Synthetic inputs and graph specification. |
| `root_prompt`, `standard_root`, `defect_root` | Root item and oracle answers. Numeric values may be represented as exact fraction strings. |
| `transfer_probes` | Two independent parameterized items used for cross-item retention before feedback and immediate repair after feedback. |
| `retention_probes` | Two distinct new items evaluated after feedback. Eligibility follows the corresponding `transfer_probes` slot in the shared pretest. |
| `contextual_application`, `probes` | Cross-context application and the six graph routes: root, near, target, sibling, alternate, and offpath. |
| `source` | Eedi dataset name, misconception identifier and aggregate annotation support. The counts describe labeled choices and distinct source items. |

Generic feedback is named `matched_sham` internally. The `N`, `G` and `T` suffixes in result metrics identify no feedback, generic feedback and targeted feedback. The sibling route acts as an independent control for the dual-source topology.

## Source and limitations

Eight deterministic mechanisms were selected using Eedi's expert labels. The generator produces new items and standard/defect answers from executable rules. The release removes Eedi label text and example question identifiers from family records. See the two hashes in `results/provenance.json` for the distinction between this snapshot and the experiment archive. The data contains answer keys and is intended for transparent research evaluation. It does not establish how real learners change their knowledge after instruction.

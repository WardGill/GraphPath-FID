# Original experiment responses

`provenance.json` lists ten JSON Lines files by model and track. Each file is plain UTF-8 text with one JSON response record per line. There are five models, three base-model configurations per model, and four student-agent components per model. Each configuration or component uses 72 test families and two initial conditions. This yields 2,160 base-model jobs and 2,880 component jobs, with 45 recorded experiment calls per job.

Each row contains the final completed response for a call in the paper's experiment manifest. The `content` string is preserved as recorded, including malformed responses and native component wrappers. The other fields identify the call. The export contains the recorded response text rather than the complete API envelope or the internal execution trace.

| Field | Description |
| --- | --- |
| `job_id` | Original job key, scoped to the file's model and track. |
| `family_id`, `split` | Join to the synthetic dataset on `family_id`. All rows come from the test split. |
| `architecture`, `condition` | Base-model state configuration or component identifier, and healthy or defect initialization. |
| `phase`, `arm`, `task` | Position in the protocol. Within a file, combine these with `job_id` to identify a response. |
| `repeat`, `wording` | Recorded repetition and prompt wording indices. |
| `content` | Original response text from the completed experiment call. |

## Calls in each job

| Phase | Arms | Calls | Meaning |
| --- | --- | ---: | --- |
| `pre` | `shared` | 9 | Shared pretest across root, two independent items, application, and five additional graph routes. |
| `post` | All three | 27 | Same nine tasks evaluated after branching into the three feedback conditions. |
| `acquisition` | All three | 3 | Feedback-exposure and attention-check turn. |
| `retention` | All three | 6 | Two unseen parameterized items per feedback condition. This phase supplies the new-item transfer endpoint. |

`no_feedback`, `matched_sham` and `targeted_repair` correspond to no feedback, generic feedback and targeted feedback. In the raw logs, `transfer_1` and `transfer_2` name the independent pretest and immediate posttest items. `retention_1` and `retention_2` name the unseen items. The file index stores SHA-256 checksums of the JSONL files.

## Mapping to the paper

The base-model state identifiers are `stateless`, `session_memory` and `explicit_state` (explicit initial state). The component identifiers are `agent4edu_official`, `agentschool_official`, `classroom_simulacra_official` and `eduagent_official`.

Initial misconception fidelity and healthy accuracy use the defect and healthy root pretests, respectively. Cross-item retention uses the two independent pretest items conditional on a root defect match. The immediate repair and new-item transfer comparison uses the same two pretest eligibility slots. For non-target measures, `alternate` is the alternative-path control, `offpath` is the off-graph control, and `sibling` is an independent-branch control only in dual-source graphs.

The dataset and responses correspond to the experiment snapshot cited in the manuscript. The archive's original dataset hash and the release dataset hash are listed separately in `provenance.json` because upstream label text and example question identifiers were removed from the release metadata.

## License scope

The original model responses are shared as experiment artifacts. See the [repository license statement](../README.md#license) for the scope of the code and synthetic data licenses.

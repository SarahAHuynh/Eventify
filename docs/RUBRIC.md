# Evidence for CS4680

| Requirement | Phase 6 status | Evidence |
| --- | --- | --- |
| Five distinct AI roles in one Herdr workspace and two AI tools | Complete | [Demo-02 pane map and CLI results](EXPERIMENT.md#five-roles-in-one-herdr-workspace) |
| Role prompts, structured outputs, constraints, and examples | Complete | [Role prompts](../agents/) · [Output formats](../inputs/output_formats.md) |
| CEO-to-coordinator communication | Complete | [CEO brief](../inputs/client_request.md) · [Initial assignment](../logs/demo-02/assign-logistics-r1.prompt.md) |
| Runtime delegation, status, and automatic file handoffs | Complete | [Task files](../tasks/demo-02/) · [Status command and handoff examples](EXPERIMENT.md#automated-assignments-and-handoffs) |
| Reproducible, tested checks | Complete | [Catalog](../inputs/price_catalog.csv) · [Validator](../scripts/validate.py) · [Unit tests](../tests/) · [Final validation](../reviews/demo-02/validation-r4.json) |
| Independent feedback and iterative refinement | Complete | [Four review rounds](EXPERIMENT.md#four-review-rounds) · [Before and after](EXPERIMENT.md#before-and-after) |
| Approved final package | Complete | [Independent approval](../reviews/demo-02/reviewer-r4/review.json) · [Event package](../outputs/demo-02/coordinator-r1/event_package.md) |
| Single-AI comparison | Complete | [Baseline result](../baseline/runs/baseline-01/result.json) · [Scored comparison](../baseline/comparison.md) · [Evaluation rubric](../baseline/evaluation_rubric.md) |
| Repository submission and short video | Pending | [Video plan](DEMO.md) · [Demo commands](EXPERIMENT.md#demo-video-commands) |

Python checks numeric constraints and the review protocol. The reviewer
judges the usefulness of the plan, prompt adherence, and whether the
requested revision actually addresses the evidence.

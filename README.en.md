# Opentrons Protocol Skill

**Turn experimental requirements, user configuration, and disclosed recommendations into reviewable Opentrons Flex Python protocols grounded in practical liquid-handling rules.**

[中文](README.md) · [Skill entry point](skills/write-opentrons/SKILL.md) · [Review regression cases](skills/write-opentrons/assets/review-regression/maintenance.md)

A community-maintained AI Agent Skill developed through iterative protocol-writing experience. It organizes API references, equipment and labware constraints, liquid-handling rules, atomic examples, and a review workflow into resources an assistant can read on demand.

This is not an official Opentrons project, standalone protocol generator, robot driver, or simulator.


## Update: 2026-10-28.5

- Publishes cumulative updates 2026-10-28.1–.5: on-demand custom labware reuse/creation and two BKMAMLAB definitions, retaining their approximate-model and physical-validation limitations.
- Adds a common-name entry point plus a release-pinned official labware index. Resolves the actual API default definition from Opentrons v10.0.0 and fetches it with source verification; an index match does not establish model or installation compatibility.
- Reinforces existing confirmation and delivery requirements: a complete first hardware description is not a confirmed restatement, and attachments do not replace key parameters in the chat response. Existing confirmations are reused without a fixed extra approval round.
- The suite now contains 123 cases. Version 2026-10-28.4 records an independent 119-case review; this update independently reviewed 16 targeted cases with matching verdicts, locations, and checked reasoning. All 123 fixture structures/snippets and 18 labware-tool tests passed. Version-specific scope and raw results are in the [maintenance record](skills/write-opentrons/assets/review-regression/release-report-2026-10-22.md).
- This publication leaves flow rates, delays, atomic examples, and API baseline 2.30 unchanged. No official protocol simulation or physical validation was performed.

## What it helps with

Provide the experimental goal, existing workflow, and actual equipment. The first stage guides a complete hardware description including robot software, then reflects the configuration, supported API range, and target for confirmation. The second explains and iterates the workflow, labware layout, and actions within that configuration. Complete input goes directly to a consolidated restatement, without repeated questions. The skill supports writing, modifying, and reviewing protocols:

- Convert an SOP and established layout into a complete Flex protocol.
- Compose transfers, handwritten mixing, one-to-many dispensing, and serial dilution.
- Add liquid visualization, module operations, gripper moves, dry-run and tip-reuse parameters.
- Review capacity, residual liquid, plunger preparation, motion paths, occupancy, and module states.
- Choose a targeted or full review based on the impact of a modification.

The primary target is **Opentrons Flex**. Some references include OT-2 module APIs; this does not imply that the complete rule set is adapted for OT-2.

## What is a Skill, and how do I use it?

A Skill is a package of instructions and resources for an AI assistant. `SKILL.md` defines the workflow and routing, `references/` supplies rules and API details, and `scripts/` provides deterministic calculation tools. It requires no model training and is not a single prompt containing every reference.

Install the **entire `skills/write-opentrons/` folder** into your AI client's supported skill location, or import it through the client's skill interface. Installation locations and interfaces vary; follow your client's current documentation. Preserve the directory structure rather than copying only `SKILL.md`.

```bash
git clone https://github.com/SGHY-IVD/opentrons-protocol-skill.git
```

After installation, explicitly ask the assistant to use `write-opentrons` and supply your workflow and layout. If your client does not support native skills, a file-capable assistant can read `skills/write-opentrons/SKILL.md` and follow its resource links. This is a manual workflow, not native installation.

The flow-rate, delay, and regression helper scripts require Python 3 and use its standard library. Executing generated protocols requires a matching Opentrons environment. The assistant needs access to the referenced files and tools; unavailable resources must be reported rather than replaced with guessed values.

The core skill resources are currently primarily in Chinese. Requests may be in Chinese or English. Project documentation is bilingual; compatibility with every skill-capable client has not been individually tested.

## Start a task

Example request:

> Use the write-opentrons skill to write a Python protocol for the following workflow and Flex deck layout. Identify missing information that materially affects execution. Review the completed protocol against the skill and report key well volumes, aspiration/dispense rates, heights, important overrides, and unresolved issues.
>
> Workflow: …  
> Pipettes and tips: …  
> Labware load names, modules, and slots: …  
> Transfer volumes, mixing, and tip-change requirements: …  
> Special liquids, initial volumes, and other overrides, if applicable: …

You do not need to supply every parameter or follow a fixed form. If actual equipment is unclear, a complete example shows how to describe pipettes, modules/adapters, waste hardware, and staging areas; the assistant checks and restates the real configuration for confirmation. Omitted hardware is not inferred from the example. The next stage explains a complete experiment plan in plain language, including reasons, omissions, and suggested fixes, for you to edit freely. Unchanged experimental details may follow disclosed recommendations; confirmed equipment is preserved. Complete input can be reflected in one integrated plan, and valid confirmation within the current task is reused without a mandatory extra approval round when generation is explicitly requested. Unspecified initial reagent volume is visualized as calculated demand, with separate advice on additional loading volume.

Robot software determines the target API instead of an unconditional 2.30 default. Higher-than-maintained limits are explained with a maintained target recommendation. A read-only probe then separates local package version, SDK limit, and simulator entry points; cloud results are not user-computer results, and an old simulator does not silently lower the protocol target. Simulation setup is optional. Hardware persistence also requires user consent and host support; historical configuration is reflected as a known example for current confirmation rather than assumed unchanged.

Delivery should include the protocol, the rule version actually used, key operation parameters, and truthful review results. A skill-use label is not proof of review; simulation must not be claimed unless it was actually run.

## Design

| Layer | Purpose |
| --- | --- |
| Entry and routing | Read relevant resources on demand |
| API and installation relationships | Maintained version baseline, parameters, load names, stacking and deck constraints |
| Independent state dimensions | Liquid accounting, tips, spatial paths, plunger and module states |
| Parameter data | Flow rates and delays, distinguishing experiential overrides from maintained official data |
| Atomic and workflow references | Composable commands, retained-liquid mixing, mode changes, serial dilution |
| Review and regression | Trace execution state and maintain review behavior with fixed cases |

Protocols default to explicit `aspirate`, `dispense`, `move_to`, and loops, avoiding high-level transfer commands and excessive abstraction. Examples cannot override core rules. Missing API or installation information is reported. Missing geometry for an already identified labware may be retrieved from official GitHub definitions under the skill's lookup rules.

## Repository layout

- [`skills/write-opentrons/SKILL.md`](skills/write-opentrons/SKILL.md): skill entry point.
- `skills/write-opentrons/references/`: APIs, parameter tables, rules, and examples.
- `skills/write-opentrons/scripts/`: flow-rate, delay, and regression tools.
- `skills/write-opentrons/assets/review-regression/`: cases, expected results, and recorded reviews.
- `skills/write-opentrons/assets/labware/`: custom definitions and limitations, matched to the actual labware.
- `skills/write-opentrons/agents/`: client presentation metadata.

## Baseline and validation limits

Initial public snapshot: **rule version 2026-10-21.9, maintained API documentation baseline 2.30**. This is a maintained baseline, not a promise to track the latest upstream version. Explicit older targets are checked against the version index rather than silently upgraded.

The regression set currently contains 123 cases covering push-out, plunger preparation, retained-liquid mixing, mode changes, cross-well motion, module states, partial-nozzle reservoir alignment, evidence, delivery consistency, validation claims, configuration delegation, cleaning constants, variable-volume/CSV domains, user-input verification, the two-stage intake boundaries, robot/API and local-environment separation, historical hardware confirmation, custom-labware and official-index boundaries, confirmation evidence, and in-chat parameter summaries. Recorded reviews were performed in batches; they do not establish validation of every release or experiment.

```bash
python3 skills/write-opentrons/scripts/review_regression.py
```

This command checks fixture structure and snippet syntax only. See the [maintenance guide](skills/write-opentrons/assets/review-regression/maintenance.md) for scoring independent review results. The scorer is not a protocol analyzer; reasoning and branch semantics still require review. Framework review, official simulation, and physical validation provide different evidence and do not guarantee or replace one another.

For cross-model comparisons, fix the skill version and input, use fresh conversations, and record the model, raw responses, generated code, and actual tool results. Review tests should receive only the cases and rules, without expected answers or historical review outputs.

## Maintenance, sources, and licensing

When reporting an issue, include the rule version, relevant equipment/labware, minimal code or steps, expected behavior, and observed behavior. Maintain rules, data, and examples separately, and add relevant regression cases after corrections. Do not generalize a one-off exception into a global default.

Official sources include [Opentrons/opentrons](https://github.com/Opentrons/opentrons) and the [Python Protocol API documentation](https://docs.opentrons.com/v2/). Source and synchronization metadata are retained in the references; see [third-party notices](THIRD_PARTY_NOTICES.md). Experiential rules are not official Opentrons guarantees.

No open-source license has yet been selected for original project content. Public visibility does not grant general redistribution or commercial-use rights. Third-party material retains its applicable terms and attribution. The maintainer may select a project license later.


Official reference snapshots ship with the skill and do not refresh automatically on installation. See the [upstream maintenance guide](skills/write-opentrons/references/upstream-maintenance.md) for scoped updates. The current rule version is defined in the [skill entry point](skills/write-opentrons/SKILL.md); the API baseline remains 2.30.

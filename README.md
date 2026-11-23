# Checkable email priorities

README word count 1387 including headings code and links, excluding this count line.


Public repository https://github.com/yugonglian258/checkable-email-priorities .

Review a simulated AI priority against the latest message and its timestamp, then confirm or correct one local thread label. Four synthetic threads use a fixed London clock of 22 October 2026 at 10:00. The baseline and revised modes expose the effect of an old quoted deadline.

## Run and inspect

Requires Python 3.10 or later and a browser. The app uses Python's standard library and needs no package installation.

```text
python app.py
```

Open http://localhost:8012/. To select another port, run `python app.py --port 8013`. The server binds to localhost. Session labels survive a page reload and expire when the server restarts. Each browser cookie has a separate in-memory label session.

Run the verification suite from this folder.

```text
python -B -m unittest -v test_project
```

The recorded run in `evidence/test-results.txt` passed 12 tests. Its fixture-label test checks all four revised classifications. A separate assertion reproduces the baseline's erroneous Action today result for B1. The expected labels live only in the evaluation fixture and are stripped before inference.

## Status and technical choices

| Component | Status | Implementation |
|---|---|---|
| Synthetic mailbox and clock | Implemented fixtures | `03_test_inputs.json`, four threads |
| Priority inference | Implemented AI simulation | `triage.py`, baseline and revised deterministic phrase/date rules |
| Source inspection | Implemented | Browser shows the latest message, received timestamp and older quotation separately |
| Confirm, correct and undo | Implemented | `LabelSession` in memory, keyed by browser cookie |
| Web interface and action endpoint | Implemented | `index.html` and standard-library `app.py` |
| Real mailbox connection | Planned | Provider choice and consent flow remain open |
| Learned language model | Planned | Model choice, calibration and evaluation remain open |

The submitted scope is a local simulation of email prioritisation and a working interaction around it. Reading a message or switching the engine generates a suggestion. Saving a label requires one of the explicit decision controls. Confirm is disabled for Needs your review. The server recomputes the suggestion and rejects attempts to confirm an unresolved classification.

## Replay the three interactions

1. Select Confirm workshop place in revised mode. Inspect supporting messages. Confirm suggestion. The local label becomes Action today and the interface reports the scope of the change. See `evidence/normal-before.jpg` and `normal-after.jpg`.
2. Select baseline mode, then Workshop update. Inspect the latest message and old quotation. The baseline marks it Action today after matching 22 October without validating the year. Choose This can wait. B1 becomes Can wait while the earlier A1 label remains. Undo restores B1 to unsaved. See `stale-before.jpg`, `stale-corrected.jpg` and `stale-undo.jpg`.
3. On Workshop update, switch to revised mode. The missing current deadline produces Needs your review, with Confirm disabled. Choose I am unsure. The thread stays unsaved and the interface suggests reading the original message. See `uncertain-before.jpg` and `uncertain-after.jpg`. In this simulation the supporting-message panel is the available source view.

## Development record

The development stages below describe reused course work and changes made for A2. Dates identify the original worksheet or this implementation, rather than a continuous Git history.

| Stage | Significant change | Reason and check |
|---|---|---|
| A1 literature review | Defined checkability as the question for student email priorities | Linked source access to appropriate reliance and identified stale evidence and missing personal context |
| Lab 2 concept, 15 October 2026 | Specified source inspection, direct correction and Undo | Used a fictional first-time user to examine correction scope. This was a design exercise |
| Lab 3 prototype, 22 October 2026 | Added separate baseline and revised inference paths with a fixed clock | The baseline misclassified B1. Revised inference kept it unresolved and preserved local correction |
| A2 browser prototype, 23 November 2026 | Reused the Lab 3 inference/session code and four fixtures. Added the browser view, cookie sessions and server-side action checks | Replayed all three interactions in the browser and recorded screenshots. Twelve regression tests passed |
| A2 report, 23 November 2026 | Produced architecture and interaction figures, then revised the rationale against five supplied Weeks 2–4 lectures | Checked implemented states, distinguished simulation and plans, and verified feedback, repair, validation, memory and provenance claims against the cited PDF pages |

`triage.py` and `03_test_inputs.json` were copied from this student's Lab 3 submission. `app.py`, `index.html` and `test_project.py` were developed for A2. The architecture and interaction figures were created for this report. The baseline mode deliberately preserves the old error so the correction path can be inspected.

## Design evidence and course connection

The project applies the sensing, inference and action structure used in Lab 2. Reading synthetic message fields supplies input, phrase/date rules produce a suggestion, and the user's decision changes a label. This division makes inference fallibility visible. HAX Guideline 1 informed capability disclosure, Guideline 9 informed correction and Undo, and Guideline 10 informed the unresolved state. The Lab 2 worksheet explicitly used Guideline 9. Report references provide the primary sources.

The source panel keeps a timestamp beside each message and distinguishes quoted history. Kim et al. (2025) motivate checking sources when evaluating incorrect AI responses. Buçinca et al. (2021) show that interventions encouraging more analytical engagement can reduce overreliance while introducing effort costs. Those studies motivated design choices. This project has software verification and scripted interactions, with participant evaluation reserved for future work.

## AI assistance and authorship

OpenAI Codex Desktop assisted with the A2 implementation, tests, report prose, diagram code and browser verification. Earlier A1 and Labs were also prepared with AI assistance. Model-generated code was checked through the actual browser controls and regression suite. Literature claims and HAX guidance were checked against primary sources. The report describes rule-based inference, synthetic messages and scripted choices. It makes no claims about observed participants, teacher feedback or learning from a correction.

Changes made during checking included adding a refresh action for the engine switch, preserving a distinct unresolved state, recomputing suggestions on the server, and documenting the baseline's deliberate error. The report's design rationale, references and claims remain the submitting student's responsibility to review and understand.

## Limits and next evaluation

The revised rules recognise a small phrase vocabulary and ISO dates. They can misread negation beyond the explicit no-action-needed phrase. They do not establish whether a task has already been completed. The four known fixtures support regression checks. A later study should counterbalance correct advice, stale evidence and absent context, then measure correct acceptance, error rejection, time and perceived effort with consented participants. The current project reports no such measurements.

## Submitted version

The submitted Git release tag is `a2-submission-v3`. Run `git rev-parse a2-submission-v3` to inspect the commit. The accompanying archive includes the working project, evidence and local Git history. The report links to the public repository and this README at the submitted tag.

The report PDF, editable report content and vector figures are in `report/`. `report/build_report.py` regenerates the PDF from `report/content.json` using ReportLab. Running the email app itself uses only the standard library. The report word counts are recorded on its first page and in report/word-count.json, including section headings and the interaction introduction. Figure labels, brief captions, references and repository access details are excluded.

The report cites inspected course material from Weeks 1–4. Lecture 04 informs local visual feedback and acknowledgement, Lecture 07 informs explicit repair choices and screen-based comparison, Lecture 08 informs code checks before action, Lecture 10 informs visible editable session labels and expiry, and Lecture 11 informs dated evidence and stale-source checking. References [6]–[10] identify PDF pages in the five lecture files supplied for this revision. Course PDFs remain source material rather than project deliverables. No teacher feedback was supplied.

## References and reused material

- Kim, S.S.Y. et al. (2025). Fostering Appropriate Reliance on Large Language Models. CHI. https://doi.org/10.1145/3706598.3714020 . Open version https://arxiv.org/abs/2502.08554 .
- Buçinca, Z., Malaya, M.B. and Gajos, K.Z. (2021). To Trust or to Think. PACM HCI 5(CSCW1), Article 188. https://doi.org/10.1145/3449287 . Author copy https://www.eecs.harvard.edu/~kgajos/papers/2021/bucinca2021trust.shtml .
- Microsoft HAX Toolkit. Guidelines 1, 9 and 10. https://www.microsoft.com/en-us/haxtoolkit/ .
- University of Birmingham (2026). Week 2 Lab Materials, LH/LM Intelligent Interactive Systems. https://canvas.bham.ac.uk/courses/90253/pages/week-2-lab-materials?module_item_id=5239930 .
- Student 3154083 (2026). A1 Literature Review and Lab 2 and Lab 3 submissions. Reused problem framing, interaction concept, inference code and synthetic fixtures as identified above.

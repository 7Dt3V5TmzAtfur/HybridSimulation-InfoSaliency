# Cover Letter — Journal of Simulation

> **[TODO before submission]** 填入通讯作者姓名/单位/邮箱；确认 AI 声明措辞与资助情况。

---

Dear Editors,

We are pleased to submit our manuscript, "**Protection level or behavioural dynamics? An effect-decomposition study of an information-saliency-driven hybrid simulation framework for dengue**," for consideration as a Research Article in the *Journal of Simulation*.

Behaviour-coupled epidemic models are routinely evaluated by switching an endogenous behavioural feedback on and off. Our manuscript shows why that evaluation design cannot support the claims usually built on it: the comparison conflates the contribution of the *level* of protective behaviour with the contribution of its *dynamics*. We address this with a four-layer hybrid simulation framework for dengue (agent-based individuals, system-dynamics transmission, discrete-event hospital resources, and explicit mosquito dynamics, with both transmission channels modulated by population protection) and an effect-decomposition evaluation design that we believe is of general methodological interest to the simulation community.

The design earns its keep through what it uncovers. A constant-protection arm, calibrated to the model's own endogenous protection level, reveals that the information-driven dynamics contribute almost nothing beyond the level itself (3.2 percentage points, non-significant at N=1,000)---a negative result the paper does not shy away from. A mechanism control then swaps in a prevalence-tracking awareness module at matched mean protection and extracts a significant 22.5 percentage points, locating the failure in the response function's shape rather than in behavioural dynamics as such; the finding is robust across the awareness module's parameter grid and the response-function shape sweep. Calibration on Brazilian weekly surveillance data (R² = 0.941; agent-model agreement r = 0.967) is bounded by frozen-parameter transfer tests that pass in large epidemic seasons and fail in small and atypical years---the honest boundary is reported rather than smoothed over. And a fully seeded, mechanically verified regeneration protocol---every number in the manuscript re-derived from archived output files by a consistency checker wired as a pre-commit hook, with a full seeded re-run reproducing all results byte-identically---accompanies the paper as part of its contribution.

The main text is approximately **8,400 words** including tables and figures (within the journal's 10,000-word guidance); references and two appendices are excluded. The manuscript is prepared for double-anonymous review; funding, competing-interest, generative-AI-use, and data-availability statements are included. The dengue surveillance data are public (OpenDengue v1.3); the simulation code, experiment scripts, run manifests, and archived outputs are publicly available in an anonymized repository (https://github.com/7Dt3V5TmzAtfur/HybridSimulation-InfoSaliency) for the duration of review, and will be archived with a persistent identifier upon acceptance.

We confirm that this manuscript is original, is not under consideration elsewhere, and has not been posted as a preprint. All authors have approved the submission.

Thank you for your consideration.

Sincerely,

[Corresponding Author]
[Affiliation]
[Email]

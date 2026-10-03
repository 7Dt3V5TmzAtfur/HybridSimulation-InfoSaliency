# Cover Letter — Journal of Simulation

> **[TODO before submission]** 填入通讯作者姓名/单位/邮箱；确认 AI 声明措辞与资助情况。

---

Dear Editors,

We are pleased to submit our manuscript, "**Protection level or behavioural dynamics? An effect-decomposition study of an information-saliency-driven hybrid simulation framework for dengue**," for consideration as a Research Article in the *Journal of Simulation*.

Behaviour-coupled epidemic models are routinely evaluated by switching an endogenous behavioural feedback on and off. Our manuscript shows why that evaluation design cannot support the claims usually built on it: the comparison conflates the contribution of the *level* of protective behaviour with the contribution of its *dynamics*. We address this with a four-layer hybrid simulation framework for dengue (agent-based individuals, system-dynamics transmission, discrete-event hospital resources, and explicit mosquito dynamics, with both transmission channels modulated by population protection) and an effect-decomposition evaluation design that we believe is of general methodological interest to the simulation community.

Three elements of the study are distinctive:

1. **A decomposition design with a mechanism control.** A constant-protection control arm calibrated to the model's own endogenous protection level, plus a mechanism control that replaces our saliency-driven behavioural module with a prevalence-tracking awareness-diffusion module at matched mean protection. The design locates a small dynamic margin (3.2 percentage points, non-significant at N=1,000) in the saturating shape of our response function rather than in behavioural dynamics per se: the awareness control, at the same mean protection, extracts a significant dynamic margin of 22.5 percentage points.
2. **Honest, bounded calibration.** A deterministic surrogate of the agent model makes grid-search calibration on Brazilian weekly surveillance data tractable (R² = 0.941; agent-model agreement r = 0.967), and frozen-parameter transfer tests across the 2016–2023 seasons establish the boundary of that calibration: it transfers to large epidemic seasons, and fails in small and atypical years.
3. **A fully seeded, mechanically verified regeneration protocol.** Every number in the manuscript is re-derived from archived output files by a consistency checker wired as a pre-commit hook, and a full seeded re-run reproduced all results byte-identically. We supply the protocol and tooling as part of the paper's contribution.

The main text is approximately **6,200 words** including tables and figures (within the journal's 10,000-word guidance); references and one appendix are excluded. The manuscript is prepared for double-anonymous review; funding, competing-interest, generative-AI-use, and data-availability statements are included. The dengue surveillance data are public (OpenDengue v1.3); the simulation code and archived outputs are available from the corresponding author and will be released upon acceptance.

We confirm that this manuscript is original, is not under consideration elsewhere, and has not been posted as a preprint. All authors have approved the submission.

Thank you for your consideration.

Sincerely,

[Corresponding Author]
[Affiliation]
[Email]

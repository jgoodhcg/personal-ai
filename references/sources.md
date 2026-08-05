---
title: "Sources"
blueprint_section: "BP-INSTR, BP-VERIFY"
---

# Sources

Evidence behind the instruction-design rules (`[BP-INSTR]`) and the verifiability
rules (`[BP-VERIFY]`). Load this file only when you write or revise those rules.
Rules cite it by number. Rationale stays here so it does not consume the
instruction stream (`BP-INSTR-08`).

Peer-review status is marked where it matters. Treat a working paper as weaker
evidence than a published one.

## Instruction design

Practitioner guidance:

- `[1]` Anthropic. "Claude Code: Best practices for agentic coding." anthropic.com/engineering, 2025.
- `[2]` Anthropic. Prompt engineering documentation. docs.claude.com.
- `[3]` OpenAI. "GPT-4.1 Prompting Guide." OpenAI Cookbook, 2025.
- `[8]` OpenAI. Model Spec, "Chain of Command." 2024, updated since.
- `[16]` Anthropic. "The New Rules of Context Engineering for Claude 5 Generation Models." claude.com/blog, 2026.

Model behavior research:

- `[4]` Ouyang et al. "Training language models to follow instructions with human feedback." (InstructGPT), 2022.
- `[5]` Wei et al. "Finetuned Language Models Are Zero-Shot Learners." (FLAN), 2021.
- `[6]` Liu et al. "Lost in the Middle: How Language Models Use Long Contexts." TACL, 2024. arXiv:2307.03172.
- `[7]` Brown et al. "Language Models are Few-Shot Learners." (GPT-3), 2020.
- `[17]` "IFScale: instruction-following degradation under instruction count." arXiv:2507.11538.

Human cognition parallels:

- `[9]` Grice. "Logic and Conversation." 1975. (maxim of quantity)
- `[10]` Carroll. *The Nurnberg Funnel: Designing Minimalist Instruction.* 1990.
- `[11]` Miller. "The Magical Number Seven, Plus or Minus Two." 1956. (chunking)
- `[12]` Sweller. "Cognitive Load During Problem Solving." 1988.
- `[13]` Sweller & Cooper. "The Use of Worked Examples as a Substitute for Problem Solving." 1985.
- `[14]` Clark & Chase. "On the Process of Comparing Sentences Against Pictures." 1972. (negation cost)
- `[15]` Wegner. "Ironic Processes of Mental Control." 1994.

## Controlled language

- `[18]` ASD-STE100 Simplified Technical English, Issue 9, 2025. Free download at
  asd-ste100.org. Registered trademark of ASD. This repository reproduces no
  specification or dictionary text.
- `[19]` AminBlg. *SimpleEnglish.* github.com/AminBlg/SimpleEnglish, MIT. Adapts
  ASD-STE100 for software documentation and agent instructions. Source of the
  adaptation in `BP-INSTR-09` and `BP-INSTR-10`.

## Cognitive surrender and overreliance

- `[20]` Shaw & Nave. "Thinking — Fast, Slow, and Artificial: How AI is Reshaping
  Human Reasoning and the Rise of Cognitive Surrender." Wharton School Research
  Paper, SSRN, 2026. **Working paper, not peer reviewed.** N=1,372 across three
  experiments and 9,593 trials. Correct AI advice raised accuracy from 46% to
  71%. Faulty AI advice dropped it to 31%. Participants followed incorrect
  advice 80% of the time. High general technology trust predicted vulnerability.
  High need for cognition and higher fluid intelligence predicted resistance.
  Coined the term.
- `[21]` Buçinca, Malaya & Gajos. "To Trust or to Think: Cognitive Forcing
  Functions Can Reduce Overreliance on AI in AI-assisted Decision-making."
  Proc. ACM Hum.-Comput. Interact. 5, CSCW1, 2021. arXiv:2102.09692. N=199.
  Cognitive forcing cut overreliance below simple explainable-AI designs.
  Participants rated the most effective designs least favorably. Benefits
  concentrated in participants high in need for cognition.
- `[22]` Vasconcelos et al. "Explanations Can Reduce Overreliance on AI Systems
  During Decision-Making." Proc. ACM Hum.-Comput. Interact. 7, CSCW1, Article
  129, 2023. arXiv:2212.06823. Five studies, N=731. Overreliance follows a
  cost-benefit rule. An explanation reduces overreliance when it lowers the cost
  to verify the output.
- `[23]` Lee et al. "The Impact of Generative AI on Critical Thinking:
  Self-Reported Reductions in Cognitive Effort and Confidence Effects From a
  Survey of Knowledge Workers." CHI 2025. doi:10.1145/3706598.3713778. N=319
  knowledge workers, 936 examples. Confidence in the AI correlated with less
  critical thinking. Self-confidence correlated with more.
- `[24]` Bainbridge. "Ironies of Automation." *Automatica* 19(6), 1983. Automation
  removes the easy work and leaves the hard work to an operator whose skill has
  decayed.

## Codebase reconnaissance

- `[25]` Piechowski, Ally. "The Git Commands I Run Before Reading Any Code."
  piechowski.io/post/git-commands-before-reading-code/. Source of the
  reconnaissance commands in the `AGENTS.md` template.

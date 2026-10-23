# DRAFT: NOT SENT

> Draft only. Nothing has been sent to anyone. Sending it is the program owner's decision. Before
> sending: re-check the quoted facts against https://arxiv.org/abs/2605.02964, fill in the signature,
> and make sure the protocol link below resolves (it points at the default branch, so it works once
> this file is merged).

**To:** Kunvar Thaman, author of arXiv 2605.02964
**Subject:** Request for the per-chain records behind section 6.3 of the RHB paper

Dear Kunvar Thaman,

Thank you for "Reward Hacking Benchmark: Measuring Exploits in LLM Agents with Tool Use". We work on
preregistered measurement of metric gaming, and we would like to re-analyse one result in the paper:
the rise in exploit rate at chain length 5 (section 6.3, Figure 2).

Before seeing any data, we have registered the analysis we would run. It is a likelihood-ratio test
for a jump at length 5 beyond a smooth trend, with intervals for each length and a power analysis:
https://github.com/NexumCorpus/boundary/blob/master/replication/rhb/PROTOCOL.md. Section 5.4 describes
5 chains per length per model, so the re-analysis may well be inconclusive at that sample size. If it
is, we will say so.

We could not find the execution logs that the Code and Data Availability section mentions. Would you
be willing to share, for the chained regime:

1. one record per chain: model, task family, chain length, seed, and the chain-level exploit label;
2. where available, the first step in each chain with an exploit event, and its category;
3. the independent-regime records by step, so that chain rates can be compared with per-step rates.

Counts alone (exploited and total for each model, family and chain length) would already allow most
of the analysis.

Three short questions, in case they are quicker to answer than sharing records:

- What is the denominator behind the 8.1% CoreRHB rate at length 5? With 5 chains per model, 8.1% is
  not k/60 or k/65 for any whole number k, so we assume it is a mean over families or a different count.
- How is a length-7 chain built, given that each family has six steps?
- Does the agent see the whole chain at the start, or receive one step at a time?

We will send you our results before posting them, publish them whatever they show, and correct
anything we have misread.

With thanks,

[name]
The Boundary Program, Nexum Corpus (https://github.com/NexumCorpus/boundary)

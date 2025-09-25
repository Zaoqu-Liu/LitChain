You are a professional biomedical researcher. Classify each paper according to the rules below.

# Details

The user provided a User_Query. Based on this query, I generated a plan and corresponding Steps. I need to conduct literature research for each step to gain sufficient knowledge to answer the User_query. I have now reached one of these steps. According to the requirements of this step, I have retrieved several papers from the BioRxiv, MedRxiv, and PubMed databases. Please classify all papers into different levels based on their titles and abstracts according to the following requirements:

1. First, determine if the paper is closely related to the user's query. If it is closely related to the user's query, the paper's level is 1.

2. If it is not closely related to the user's query, then determine if it is related to the current step. If it is related to the current step, the level is 2.

3. If the paper is neither related to the user's query nor to the current step, the level is 3.

You need to ensure that:
1. When categorizing each paper into a level, you need to provide a comprehensive justification for why you've assigned that particular level to the paper.

2. Please make full use of the paper's title and abstract to analyze which level the paper fits into.

# Paper Level Evaluation Process

## A. Determining "Close Relevance to User_Query"

Decides whether to directly classify as Level 1 (satisfying any one of A1~A3 "strong matches" is sufficient for Level 1; if all are weak matches or no matches, proceed to Part B)

### A1 Theme Relevance

- The paper's theme is directly related to the core theme of the User_query

### A2 Keyword Match

- The paper's title or abstract contains core keywords or terms from the User_query
- Core keywords appear repeatedly

### A3 Content Relevance

- The paper's research question, method, or conclusion directly answers or addresses the issue raised in the User_query

If A1~A3 are not satisfied, proceed to B

---

## B. Determining "Relevance to Current Step"

Decides whether to classify as Level 2 (using a similar scoring system, satisfying either B1 or B2 is sufficient for Level 2; if none are satisfied, it's Level 3)

### B1 Matching Step Objective

- The paper's title or abstract can meet the purpose or Verification_Point of the current step_query

### B2 Step Keyword Match

- The paper's title or abstract contains core keywords or terms from the Step_query
- Core keywords appear repeatedly

---

## C. Evaluation Process Summary

First run Part A, if it hits, it's Level 1; if not, run Part B, if it hits, it's Level 2; if neither hits, it's Level 3.

---

# Output Format - STRICT

Directly output the raw JSON format of `Papers` without "```json". The `Papers` interface is defined as follows:
```ts
interface Paper_Level {
    reason: string;  // The reason for classifying the paper into this level
    level: number;  // The level of the paper: 1, 2, or 3
    title: string;  // The title of the paper
}
interface Papers {
    Papers: Paper_Level[];  // The level of all papers
}
```

#  Output Example
{
"Papers":
[
    {
        "reason":"This paper focuses on adaptation to heavy-metal contaminated environments and has no relation to Sema3c, its structure, signaling pathways, or physiological functions. It does not address the user query about Sema3c's role in cancer metastasis nor the current step about Sema3c's structure and normal functions.",
        "level": 3,
        "title": "Adaptation to heavy-metal contaminated environments proceeds via selection on pre-existing genetic variation"
    },
    {
        "reason": "This paper discusses modeling methyl-sensitive transcription factor motifs and has no relation to Sema3c, its structure, signaling pathways, or physiological functions. It does not address the user query about Sema3c's role in cancer metastasis nor the current step.",
        "level": 3,
        "title": "Modeling methyl-sensitive transcription factor motifs with an expanded epigenetic alphabet"
    }
]
}
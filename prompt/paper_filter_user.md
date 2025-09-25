## requirement
The user provided a User_Query. Based on this query, I have generated a plan and corresponding Steps. I need to conduct literature research on each step to obtain sufficient knowledge to answer User_query. I have now reached one of the steps, and according to the requirements of this step, I have retrieved some papers of BioRxiv, MedRxiv, and PubMed databases. The relevant data is as follows:

## User_Query:
{{User_Query}}

## Steps:
{{Steps}} 

## Current_Step:
{{Current_Step}}
 
## Papers:
{{Papers}}


## Output Format - STRICT

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

##  Output Example
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
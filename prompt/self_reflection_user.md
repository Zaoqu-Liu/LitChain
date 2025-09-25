## requirement
The user provides a `User_Query`. Based on this `User_Query`, I generate relevant `Steps`. For each step, I search relevant papers in the BioRxiv, MedRxiv, and PubMed databases to address the `User_Query`. Currently, I am stuck at `Current_Step`: according to its `step_query`, no relevant papers were found in these three databases. You need to analyze the rationality of the current steps and adjust the logical chain appropriately.

The relevant data is as follows:

## data
User_Query:
<User_Query>
{{User_Query}}
</User_Query>
Steps:
<Steps>
{{Steps}} 
</Steps>  
Current_Step:
<Current_Step> 
{{Current_Step}}
</Current_Step>  

# Output Format

Directly output the raw JSON format of `Logical_chain` without "```json". The `Logical_chain` interface is defined as
follows:

```ts
interface Step {
    relationship: string  // The logical relationship between this step and the previous step and the logical chain
    purpose: string  // What is the purpose of this step? Why is this step necessary
    Verification_Point: string;  // The points that need to be verified in this step are, for example, whether there is any literature indicating the relationship between molecule 1 and molecule 2
    Step_query: string; //Each query should include only key terms—no modifiers allowed—and use no more than two keywords linked by AND.
}
interface logical_chain {
    thought: string;  //How to generate a qualified logical chain based on user questions, and why this logical chain is the best
    Logical_chain: string;  //The content of logical chain
    steps: Step[];  // Steps that need to be verified
}
```
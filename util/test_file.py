# -*- coding: utf-8 -*-

from util.json_util import repair_json_output
result = {
"Papers":
[
    {
        "reason": "This paper focuses on genetic adaptation in plants to heavy-metal contaminated environments and has no relation to physician, medical training, medication management, or documentation practices. It does not address the user query about physician specialty influence recording nor the current step about specialty-specific training differences.",
        "level": 3,
        "title": "Adaptation to heavy-metal contaminated environments proceeds via selection on pre-existing genetic variation"
    },
    {
        "reason": "This paper discusses biodiversity sampling and monitoring protocols for taxonomic, phylogenetic and functional diversity in ecological research. It has no relation to physician specialty, medical training, medication management, or clinical documentation practices. It does not address the user query or current step requirements.",
        "level": 3,
        "title": "Optimal inventorying and monitoring of taxonomic, phylogenetic and functional diversity"
    },
    {
        "reason": "This paper focuses onheimer's disease pathogenesis and neuronal receptor PTPσ as a therapeutic target. It has no relation to physician specialty, medical training, medication management, or documentation practices in clinical settings. It does not address the user query or current step about training differences between medical specialties.",
        "level": 3,
        "title": "Alzheimer-related pathogenesis is dependent on neuronal receptor PTPσ."
    },
    {
        "reason": "This paper investigates Zika virus open reading frames and their role in neurotropism. It has no relation to physician specialty, medical training, medication management, or clinical documentation practices. It does not address the user query about medication history recording or the current step about specialty-specific training differences.",
        "level": 3,
        "title": "Zika viruses encode multiple upstream open reading frames in the 5' viral region with a role in neurotropism"
    },
    {
        "reason": "This paper examines leaf mass components and trait variation in plants. It has no relation to physician specialty, medical training, medication management, or clinical documentation practices. It does not address the user query or current step requirements about medical specialty training differences.",
        "level": 3,
        "title": "Decomposing leaf mass into metabolic and structural components explains divergent patterns of trait variation within and among plant species"
    },
    {
        "reason": "This paper studies cognitive processes and memory scanning paradigms in psychology research. While it examines individual differences in cognitive models, it has no relation to physician specialty, medical training, medication management, or clinical documentation practices. It does not address the user query or current step about specialty-specific training differences in medicine.",
        "level": 3,
        "title": "When Group Means Fail: Can One Size Fit All?"
    },
    {
        "reason": "This paper presents a theory about brain representation and probabilistic computation using population coding. It has no relation to physician specialty, medical training, medication management, or clinical documentation practices. It does not address the user query or current step requirements.",
        "level": 3,
        "title": "A Radically New Theory of how the Brain Represents and Computes with Probabilities"
    },
    {
        "reason": "This paper develops a Bayesian theory of efficient coding for sensory systems and neuroscience. It has no relation to physician specialty, medical training, medication management, or clinical documentation practices. It does not address the user query about medication history recording or the current step about training differences between medical specialties.",
        "level": 3,
        "title": "Bayesian Efficient Coding"
    },
    {
        "reason": "This paper investigates DNA-protein interactions and helicase mechanisms in molecular biology. It has no relation to physician specialty, medical training, medication management, or clinical documentation practices. It does not address the user query or current step requirements about medical specialty training differences.",
        "level": 3,
        "title": "Communication between DNA and nucleotide binding sites facilitates stepping by the RecBCD helicase"
    },
    {
        "reason": "This paper analyzes genetic mutations in mitochondrial genomes of humans and Neanderthals. It has no relation to physician specialty, medical training, medication management, or clinical documentation practices. It does not address the user query about physician specialty influence on medication history recording or the current step about training differences.",
        "level": 3,
        "title": "Convergent mutations and single nucleotide variants in mitochondrial genomes of modern humans and Neanderthals"
    }
]
}
import json
repaired_json = repair_json_output(str(result))
parsed_data = json.loads(repaired_json)
from util.json_util import validate_papers
# 验证数据结构
if validate_papers(parsed_data):
    print("T")
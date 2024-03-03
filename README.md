# LLM_entropy_research

**Table Of Contents**

- [Description](#description)
- [Running the sample](#running-the-sample)

## Description

This repository contains 3 scripts
- `dump_natural_question.py`
A script for dumping questions from [Natural Questions dev set](https://ai.google.com/research/NaturalQuestions/download) into a text file.
The format will be one question for one line.

- `simple_generate.py`
A script to generate answers based on the questions in the text file.
The format of the text file should be one question for one line.

- `examine_entropy.ipynb`
This notebook contains the procedure to examine the entropy distribution.

For the entropy dumping procedure, check [LLM_entropy](https://github.com/Com1t/LLM_entropy).


## Running the sample

1. Run `dump_natural_question.py` to dump the questions.
2. Use `simple_generate.py` to generate the entropy dumps with the desired huggingface model(Remember to check [LLM_entropy](https://github.com/Com1t/LLM_entropy) before running this step).
3. Use `examine_entropy.ipynb` to examine the entropy distribution.

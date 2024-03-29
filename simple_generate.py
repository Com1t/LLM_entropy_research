import os
import sys
import shutil

import fire
import torch
import transformers
from transformers import GenerationConfig, LlamaForCausalLM, LlamaTokenizer
import time

import os.path as osp
from typing import Union

if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

fetch_time = 0.0
forward_time = 0.0

class Prompter(object):
    __slots__ = ("template", "_verbose")

    def __init__(self, template_name: str = "", verbose: bool = False):
        self._verbose = verbose
        self.template = dict()
        self.template["description"] = "Template used by Alpaca-LoRA."
        self.template["prompt_input"] = "Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.\n\n### Instruction:\n{instruction}\n\n### Input:\n{input}\n\n### Response:\n"
        self.template["prompt_no_input"] = "Below is an instruction that describes a task. Write a response that appropriately completes the request.\n\n### Instruction:\n{instruction}\n\n### Response:\n"
        self.template["response_split"] = "### Response:"
        if self._verbose:
            print(
                f"Using prompt template {template_name}: {self.template['description']}"
            )

    def generate_prompt(
        self,
        instruction: str,
        input: Union[None, str] = None,
        label: Union[None, str] = None,
    ) -> str:
        # returns the full prompt from instruction and optional input
        # if a label (=response, =output) is provided, it's also appended.
        if input:
            res = self.template["prompt_input"].format(
                instruction=instruction, input=input
            )
        else:
            res = self.template["prompt_no_input"].format(
                instruction=instruction
            )
        if label:
            res = f"{res}{label}"
        if self._verbose:
            print(res)
        return res

    def get_response(self, output: str) -> str:
        return output.split(self.template["response_split"])[1].strip()


def main(
    load_8bit: bool = False,
    base_model: str = "decapoda-research/llama-7b-hf",
    # lora_weights: str = "tloen/alpaca-lora-7b",
    prompt_template: str = "",  # The prompt template to use, will default to alpaca.
):
    total_start = time.time_ns()
    base_model = base_model or os.environ.get("BASE_MODEL", "")
    assert (
        base_model
    ), "Please specify a --base_model, e.g. --base_model='huggyllama/llama-7b'"

    prompter = Prompter(prompt_template)

    global fetch_time
    global forward_time
    start = time.time_ns()
    tokenizer = LlamaTokenizer.from_pretrained(base_model)

    model = LlamaForCausalLM.from_pretrained(
        base_model,
        load_in_8bit=load_8bit,
        torch_dtype=torch.float16,
        device_map="auto",
        use_cache=False,
    )

    fetch_time += (time.time_ns() - start) / 1e9

    # unwind broken decapoda-research config
    model.config.pad_token_id = tokenizer.pad_token_id = 0  # unk
    model.config.bos_token_id = 1
    model.config.eos_token_id = 2

    if not load_8bit:
        model.half()  # seems to fix bugs for some users.

    model.eval()

    def evaluate(
        instruction,
        input=None,
        temperature=0.1,
        top_p=0.75,
        top_k=40,
        max_new_tokens=128,
        **kwargs,
    ):
        prompt = prompter.generate_prompt(instruction, input)
        inputs = tokenizer(prompt, return_tensors="pt")
        input_ids = inputs["input_ids"].to(device)

        # sampling
        generation_config = GenerationConfig(
            pad_token_id=tokenizer.eos_token_id,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            **kwargs,
        )

        # disable kv cache
        # generation_config.use_cache=False

        global fetch_time
        global forward_time
        start = time.time_ns()
        with torch.no_grad():
            generation_output = model.generate(
                input_ids=input_ids,
                generation_config=generation_config,
                return_dict_in_generate=True,
                output_scores=True,
                max_new_tokens=max_new_tokens,
            )
        forward_time += (time.time_ns() - start) / 1e9

        s = generation_output.sequences[0]
        output = tokenizer.decode(s)
        yield prompter.get_response(output)


    """
    # testing code for readme
    """
    model.model.calculate_entropy = True
    model.model.save_entropy = True
    home_dir = os.environ["HOME"]
    sample_start = time.time_ns()
    NQs = []
    with open(f"{home_dir}/natural-questions-data/questions.txt", "r") as fin:
        for l in fin:
            NQs.append(l[:-1] + '?')
    
    for i, questions in enumerate(NQs):
        model.model.num_gen = 0
        model.model.entropy_save_dir = f"{home_dir}/entropy_research/dumps/q_{i}"
        # if the demo_folder directory exists, then remove it and create a new one. 
        if os.path.exists(model.model.entropy_save_dir):             
            shutil.rmtree(model.model.entropy_save_dir)
        os.makedirs(model.model.entropy_save_dir)

        print("questions:", questions)
        sentence = ""
        for tok in evaluate(questions):
            sentence = sentence + " " + tok
        print(f"Response: {sentence}")

    print(f"fetch_time {fetch_time}")
    print(f"forward_time {forward_time}")
    print(f"Total sample time = {(time.time_ns() - sample_start) / 1e9}")
    print(f"Total total time = {(time.time_ns() - total_start) / 1e9}")


if __name__ == "__main__":
    fire.Fire(main)

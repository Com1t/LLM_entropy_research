import gzip
import json
import os
import time
import argparse

def main(data_dir, split_name, num_question):
  """Runs `text_utils.simplify_nq_example` over all shards of a split.

  Prints simplified examples to a single gzipped file in the same directory
  as the input shards.
  """
  outpath = os.path.join(data_dir, "questions.txt")
  inpath = os.path.join(data_dir, split_name)

  print("Processing {}".format(inpath))
  
  with open(outpath, "w") as fout:
    with gzip.open(os.path.join(data_dir, inpath), "rb") as fin:
      for i, l in enumerate(fin):
        utf8_in = l.decode("utf8", "strict")
        utf8_out = json.loads(utf8_in)['question_text'] + u"\n"
        fout.write(utf8_out)
        if i > num_question:
          break

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("data_dir", type=str,
                      help="Path to directory containing original NQ")
  parser.add_argument("split_name", type=str,
                      help="the name of NQ (this name will also be the name of dump)")
  parser.add_argument("num_question", type=int,
                      help="the number of questions to extract from NQ")
  args = parser.parse_args()

  data_dir = args.data_dir
  split_name = args.split_name
  num_question = args.num_question
  # data_dir = "$HOME/natural-questions-data"
  # split_name = "v1.0-simplified_nq-dev-all.jsonl.gz"
  # num_question = 100

  main(data_dir, split_name, num_question)

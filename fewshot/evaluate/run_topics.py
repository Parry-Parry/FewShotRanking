import pyterrier as pt
pt.init()
import fire 
import os
from os.path import join
import ir_datasets as irds
import pandas as pd
from ..modelling.prp import PRP
from ..examples import ExampleStore

def run(topics_or_res : str, 
         run_dir : str, 
         out_dir : str, 
         model_name_or_path : str,
         batch_size : int = 4,
         window_size : int = None,
         few_shot_mode : str = 'random',
         k : int = 0,
         n_pass : int = 3,
         k_shot_file : str = None,
         eval : str = 'msmarco-passage/trec-dl-2019/judged',
         dataset : str = 'irds:msmarco-passage/train/triples-small',
         ):  
    
    lookup = irds.load(eval)
    queries = pd.DataFrame(lookup.queries_iter()).set_index('query_id').text.to_dict()
    dataset = pt.get_dataset(dataset)
    topics_or_res = pt.io.read_results(topics_or_res)
    topics_or_res['query'] = topics_or_res['qid'].apply(lambda x: queries[str(x)])
    topics_or_res = pt.text.get_text(dataset, "text")(topics_or_res)
    del queries

    os.makedirs(out_dir, exist_ok=True)

    model_base = os.path.basename(run_dir)
    out = join(out_dir, f"{model_base}_run.gz")

    if os.path.exists(out): return "Already exists"

    if k > 1: few_shot_examples = ExampleStore(lookup.replace('irds:', ''), file=k_shot_file)
    else: few_shot_examples = None

    try: 
        model = PRP(model_name_or_path, 
                     batch_size=batch_size, 
                     k=k, 
                     window_size=window_size, 
                     n_pass=n_pass, 
                     few_shot_mode=few_shot_mode, 
                     few_shot_examples=few_shot_examples)
    except OSError as e: return f"Failed to load {model_base}, {e}"

    res = model.transform(topics_or_res)
    pt.io.write_results(res, out)

    return "Success!"

if __name__ == '__main__':
    fire.Fire(run) 
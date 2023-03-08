import gradio as gr

import torch
from transformers import PegasusForConditionalGeneration, PegasusTokenizer
from sentence_transformers import SentenceTransformer, util


def paraphrase(text):
    def get_response(input_text, num_return_sequences, num_beams):
        # Beam search can work very well in tasks where the length of the desired generation is more or less predictable as in machine translation or summarization
        batch = tokenizer(
            [input_text],
            truncation=True,
            padding="longest",
            max_length=60,
            return_tensors="pt",
        ).to(torch_device)
        translated = paratrf.generate(
            **batch,
            max_length=60,
            num_beams=num_beams,
            num_return_sequences=num_return_sequences,
            temperature=1.5
        )
        tgt_text = tokenizer.batch_decode(translated, skip_special_tokens=True)
        return tgt_text

    # generate candidates
    candidates = get_response(text, 20, 20)

    # ranking model
    # Sentences we want to encode. Example:
    input_embedding = sentrf.encode(text, convert_to_tensor=True)
    candidate_embeddings = sentrf.encode(candidates, convert_to_tensor=True)

    # semantic similarities
    cosine_scores = util.cos_sim(input_embedding, candidate_embeddings)

    # sort scores
    value, indices = cosine_scores.topk(5)
    output = ""
    for idx in indices[0][-5:]:
        output += (
            " Score:" + str(cosine_scores[0][idx]) + "\t\t\t" + candidates[idx] + "\n"
        )
    return output


if __name__ == "__main__":
    # gpu or cpu
    torch_device = "cuda" if torch.cuda.is_available() else "cpu"

    # load models
    model_name = "tuner007/pegasus_paraphrase"
    tokenizer = PegasusTokenizer.from_pretrained(model_name)
    paratrf = PegasusForConditionalGeneration.from_pretrained(model_name).to(
        torch_device
    )
    sentrf = SentenceTransformer("paraphrase-MiniLM-L6-v2")

    # print(paraphrase("Let's have a pizza party!"))

    # demo = gr.Interface(fn=greet, inputs="text", outputs="text")
    demo = gr.Interface(fn=paraphrase, inputs="text", outputs="text")
    demo.launch(share=False)
    # demo.launch(shsre=True)

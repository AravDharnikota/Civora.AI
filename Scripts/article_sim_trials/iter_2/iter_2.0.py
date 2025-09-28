# chat_min.py
import argparse, torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

class Article:
    def __init__(self, title, topic, published_date, who, to_whom, action_lemma, action_family, when, where, evidence, confidence, extras):
        self.title = title
        self.topic = topic
        self.published_date = published_date
        self.who = who
        self.to_whom = to_whom
        self.action_lemma = action_lemma
        self.action_family = action_family
        self.when = when
        self.where = where
        self.evidence = evidence
        self.confidence = confidence
        self.extras = extras

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("message", nargs="?", default=None, help="Your user message")
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)

# set a real pad token (GPT-style models often reuse eos)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # choose device/dtype (bf16 on Apple M-series is stabler than fp16)
    if torch.backends.mps.is_available():
        device, dtype = "mps", torch.bfloat16
    elif torch.cuda.is_available():
        device, dtype = "cuda", torch.float16
    else:
        device, dtype = "cpu", torch.float32

    # eager attention avoids MPS matmul/shape crashes
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=dtype,
        attn_implementation="eager"
    ).to(device)

    #user_msg = args.message or input("You: ")

    user_block = """ARTICLE_META:
    title: Trump says Chicago ‘will find out why it’s called the Department of WAR’ ahead of planned crackdown
    published_iso: 2025-09-06T15:54:00Z
    url: https://www.cnn.com/2025/09/06/politics/trump-chicago-war-meme-post
    source: CNN Politics
    country_hint: United States

    ARTICLE_TEXT:
    <President Donald Trump posted a meme on social media Saturday saying that Chicago “will find out why it’s called the Department of WAR,” as the city’s officials brace for an immigration crackdown.

“I love the smell of deportations in the morning … Chicago about to find out why it’s called the Department of WAR,” the post reads. Trump signed an executive order Friday to rebrand the Pentagon as the “Department of War.”

The post includes what appears to be an artificially generated image of the president wearing a hat and sunglasses, with the Chicago skyline in the background, accompanied by text reading “Chipocalypse Now.”

Democratic Illinois Gov. JB Pritzker on Saturday called Trump’s post “not normal.” “The President of the United States is threatening to go to war with an American city. This is not a joke. This is not normal,” Pritzker wrote on X. “Donald Trump isn’t a strongman, he’s a scared man. Illinois won’t be intimidated by a wannabe dictator.”

It comes as Trump has ramped up his rhetoric against the country’s third most-populous city. CNN previously reported the Trump administration’s plans to conduct a major immigration enforcement operation in Chicago, and that officials there were bracing for it to begin as early as Friday.

In recent days, personnel from Immigration and Border Protection as well as Customs and Border Protection have begun trickling into the city, White House officials told CNN.

The Trump administration has also reserved the right to call in the National Guard if there is a reaction to the operation that warrants it, the officials said. The Chicago operation is being modeled off of a similar operation carried out in Los Angeles in June. A judge ruled this week that the June deployment broke federal law prohibiting the military from law enforcement activity on US soil in most cases; the Trump administration has appealed.

White House officials have made clear the Chicago immigration crackdown is distinct from the idea the president has floated to use federal law enforcement and National Guard troops to carry out a broader crime crackdown in the city, similar to the operation in Washington, DC.

When asked by a reporter Tuesday about sending National Guard troops into the city, Trump said, “We’re going,” adding, “I didn’t say when. We’re going in.”

Democratic officials who represent Chicago and Illinois also condemned Trump’s post Saturday.

“The President’s threats are beneath the honor of our nation, but the reality is that he wants to occupy our city and break our Constitution,” wrote Chicago Mayor Brandon Johnson on social media. “We must defend our democracy from this authoritarianism by protecting each other and protecting Chicago from Donald Trump.”

Illinois Sen. Tammy Duckworth described Trump’s post on X as “Stolen valor at its worst,” writing, “Take off that Cavalry hat, you draft dodger. You didn’t earn the right to wear it.”

Rep. Mike Quigley, who represents part of Chicago, said Saturday afternoon on CNN that the post is an example of Trump “edging more and more toward authoritarianism.”

“This is a scary time. For those who haven’t paid attention, it’s time to watch what this president is doing,” Quigley said.
>
    """

    messages = [
        {"role": "system", "content": """You extract the single primary event this article is about and output ONLY one strict JSON object (not an array, no prose, no code fences).

FIELDS:
- who: array of {name, role}  # actors of THIS event only; do not include people from other events; use canonical full names (no titles) e.g., "Donald Trump", "Chicago Police Department"; If the article contains a full name for a last-name mention (e.g., ‘Trump’), use that canonical full name in who.
- to_whom: array of {name, role}  # empty if none; add cities or larger entities if obviously targeted
- action_lemma: lowercase verb (e.g., "post", "sign", "vote", "sue", "arrest", "protest")
- action_phrase: short verb phrase (≤6 words) from the evidence (e.g., "posted meme", "signed executive order")
- when: {start:null, end:null, grain:"second|minute|hour|day|week|month|year|unknown", text}
  • If date is relative (“Friday”, “next week”), keep it in when.text and leave start/end null.
  • Set when.start=null and when.end=null unless an explicit clock time appears in the article.
  • when.grain must be exactly one allowed value (e.g., "day")—not the options list.
- where: {name:<city>, country:<country or "" if unknown>}
  • Prefer city,country; do NOT use building names (e.g., not "City Hall").
  • Set where.name to a city mentioned in the headline/lead/evidence if present; do not leave it empty when a city is clearly stated.
- summary: 1–3 sentence summary of the event (string)
- evidence: ONE exact sentence from the article (string); evidence MUST be one sentence (choose the sentence that contains the action).
- confidence: 0–1
- extras: object (free-form key/values; not a string)

DERIVED FIELDS (for grouping):
- who_canon: array of canonical full names (no titles), e.g., "Donald Trump"
- who_lastnames: array of lowercase last names/main tokens
- date_bucket: "YYYY-MM-DD" if resolvable from ARTICLE_META.published_iso + when.text; else null
- place_key: "City,Country" if known; else ""
- line_text: "{date_bucket or when.text} | {action_phrase} | WHO:{who_canon ';'-joined} | WHERE:{place_key}"
- speculative: boolean (true if plan/expected/proposed wording)

RULES:
- Output exactly ONE JSON object; no code fences or extra text.
- "who" MUST only include actors that appear in the evidence sentence (or the sentence immediately before it). If the article contains a full name elsewhere (e.g., “Donald Trump”), use that canonical form.
- Do not invent facts; use ""/null when unknown.
- If multiple concrete events are described, pick the one most supported by the headline/lead and least speculative.
"""},
        {"role": "user",   "content": user_block}
    ]

    inputs = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, return_tensors="pt"
    ).to(device)

    attention_mask = torch.ones_like(inputs)

    with torch.no_grad():
        outputs = model.generate(
            input_ids=inputs,
            attention_mask=attention_mask,
            max_new_tokens=512,    # give it room if you want all fields
            do_sample=False,       # greedy for JSON stability
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            use_cache=True
        )

    gen_ids = outputs[0][inputs.shape[-1]:]  # strip the prompt tokens
    reply = tokenizer.decode(gen_ids, skip_special_tokens=True).strip()
    print("\nAssistant:", reply)

if __name__ == "__main__":
    main()
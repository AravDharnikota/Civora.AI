import os, json, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel


# ----------------- CONFIG -----------------
BASE_MODEL  = "Qwen/Qwen2.5-1.5B-Instruct"
ADAPTER_ID  = "AravD/article_key_idea_extraction"

# ----------------- LOAD MODEL + TOKENIZER (once) -----------------
_tok = None
_model = None
_device = None

def load_model_and_tokenizer():
    global _tok, _model, _device
    if _tok is not None and _model is not None:
        return _tok, _model, _device

    tok = AutoTokenizer.from_pretrained(BASE_MODEL, use_fast=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    if torch.backends.mps.is_available():
        device, dtype = "mps", torch.bfloat16
    elif torch.cuda.is_available():
        device, dtype = "cuda", torch.float16
    else:
        device, dtype = "cpu", torch.float32

    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=dtype,
        attn_implementation="eager"
    )

    # Load adapter with error handling for unsupported config parameters
    try:
        model = PeftModel.from_pretrained(base, ADAPTER_ID)
    except TypeError as e:
        if "unexpected keyword argument" in str(e):
            print(f"Warning: Adapter config has unsupported parameters. Trying alternative loading...")
            # Try loading with a more permissive approach
            from peft import LoraConfig
            from peft.utils import _get_submodules
            
            # Load the adapter config manually and filter out unsupported parameters
            import json
            from huggingface_hub import hf_hub_download
            
            config_path = hf_hub_download(ADAPTER_ID, 'adapter_config.json')
            with open(config_path, 'r') as f:
                config_dict = json.load(f)
            
            # Filter out unsupported parameters
            supported_params = {
                'r', 'lora_alpha', 'target_modules', 'lora_dropout', 
                'bias', 'task_type', 'peft_type', 'base_model_name_or_path'
            }
            filtered_config = {k: v for k, v in config_dict.items() if k in supported_params}
            
            # Create LoRA config manually
            lora_config = LoraConfig(**filtered_config)
            
            # Load the adapter weights
            from peft import get_peft_model
            model = get_peft_model(base, lora_config)
            
            # Load the adapter weights
            adapter_path = hf_hub_download(ADAPTER_ID, 'adapter_model.safetensors')
            from safetensors import safe_open
            with safe_open(adapter_path, framework="pt", device="cpu") as f:
                state_dict = {k: f.get_tensor(k) for k in f.keys()}
            
            # Load the state dict into the model
            model.load_state_dict(state_dict, strict=False)
        else:
            raise e
    model.to(device).eval()

    # Optional: fuse LoRA for slightly faster inference (more RAM)
    # model = model.merge_and_unload().to(device).eval()

    _tok, _model, _device = tok, model, device
    return _tok, _model, _device

# ----------------- PROMPT BUILDING -----------------
instructions_string = """
You extract the SINGLE PRIMARY EVENT this article is about and return EXACTLY ONE strict JSON object (no array, no prose, no code fences). Follow this schema:

FIELDS
- who: array of {name, role}               # actors of THIS event only; use canonical full names (e.g., "Donald Trump")
- to_whom: array of {name, role}           # direct target/recipient (empty if none; can include city/org)
- action_lemma: lowercase verb             # e.g., "post", "sign", "sue", "arrest", "protest", "announce", "launch", "file"
- action_phrase: ≤6 words from the evidence sentence (e.g., "posted meme", "signed executive order")
- when: {start:null, end:null, grain:"second|minute|hour|day|week|month|year|unknown", text}
  • If only a weekday/date phrase (e.g., "Friday", "next week") is given, put it in when.text, set grain="day", and keep start=end=null.
  • Unless an explicit clock time appears in the article, keep start=end=null.
- where: {name:<city>, country:<country or "" if unknown>}
  • Prefer city,country; do NOT use building names (e.g., not "City Hall").
- summary: 1–3 sentence neutral summary of the event
- evidence: ONE exact sentence from the article that states the action (verbatim)
- confidence: number 0–1
- extras: object (free-form key/values; not a string). Use if helpful, e.g., {"platform":"social media","media_type":"meme"}.

RULES
- Output exactly ONE JSON object and nothing else.
- "who" MUST include only actors that appear in the evidence sentence OR the sentence immediately before it.
- Use canonical full names (no titles). If the article later says “Trump” but earlier gives “Donald Trump,” use “Donald Trump.”
- Do not invent facts. Use "" or null when unknown.
- Prefer concrete, least-speculative event that matches the headline/lead.
- to_whom rule: to_whom MUST NOT be empty if the evidence sentence contains a direct target introduced by "with", "to", "against", "for", or "from" (e.g., "...voted 9–4 to approve a contract **with RideLoop**" → to_whom=[{"name":"RideLoop","role":"private mobility operator"}]).
- numbers rule: Extract any numbers in the evidence sentence into extras as normalized fields when obvious: amounts → amount_usd; durations → term_years; vote tallies like "9–4" → votes_for, votes_against (integers).
- role quality: Use concrete roles ("city council", "private mobility operator"), not vague labels ("decision-makers").
- lemma choice: If the evidence says "voted X–Y to approve", set action_lemma="approve" (not "vote").
""".strip()

def make_user_block(article_meta: dict, article_text: str) -> str:
    return (
        "ARTICLE_META:\n"
        f"title: {article_meta.get('title','')}\n"
        f"published_iso: {article_meta.get('published_iso','')}\n"
        f"source: {article_meta.get('source','')}\n"
        f"country_hint: {article_meta.get('country_hint','')}\n"
        f"city_hint: {article_meta.get('city_hint','')}\n\n"
        "ARTICLE_TEXT:\n"
        f"{article_text}"
    )

def build_messages(article_meta: dict, article_text: str):
    return [
        {"role": "system", "content": instructions_string},
        {"role": "user",   "content": make_user_block(article_meta, article_text)},
    ]

# ----------------- JSON PARSE (tolerant) -----------------
def parse_single_json(text: str):
    t = text.strip()
    # strip code fences if present
    if t.startswith("```"):
        parts = t.split("```")
        if len(parts) >= 3:
            t = parts[1]
            if t.lstrip().lower().startswith("json"):
                t = t.split("\n", 1)[1] if "\n" in t else ""
    t = t.strip()

    try:
        return json.loads(t)
    except json.JSONDecodeError:
        # fallback: slice from first '{' to last '}' to drop stray chatter
        start = t.find("{")
        end   = t.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(t[start:end+1])
        raise  # bubble up if truly malformed

# ----------------- INFERENCE -----------------
def extract_event(article_meta: dict, article_text: str, max_new_tokens=400):
    tok, model, device = load_model_and_tokenizer()
    messages = build_messages(article_meta, article_text)

    inputs = tok.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(device)
    
    # Create attention mask
    attention_mask = torch.ones_like(inputs)

    with torch.no_grad():
        out = model.generate(
            inputs,
            attention_mask=attention_mask,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tok.eos_token_id
        )

    reply = tok.decode(out[0, inputs.shape[-1]:], skip_special_tokens=True).strip()
    return parse_single_json(reply)

# ----------------- DEMO -----------------
if __name__ == "__main__":
    meta = {
        "title": "Denver Council approves $120M microtransit contract after marathon hearing",
        "published_iso": "2025-10-02T16:00:00Z",
        "source": "Metro Newswire",
        "country_hint": "United States",
        "city_hint": "Denver",
    }
    article = """
    DENVER — On Thursday, the Denver City Council voted 9–4 to approve a $120 million, five-year contract with RideLoop, a private mobility operator, to expand on-demand microtransit service citywide as part of the city’s “First and Last Mile” strategy.

The vote followed a six-hour public hearing that drew more than 200 residents, transit advocates, and small-business owners to City Hall. Supporters argued the contract will fill gaps in bus and rail coverage, especially for late-night and weekend trips, while opponents questioned labor standards, data privacy, and whether funds would be better spent improving fixed-route bus frequency.

“We heard loud and clear that people need reliable rides to work at 5 a.m., to school pickups at 3 p.m., and to second shifts that end at midnight,” Council President Alicia Romero said just before the final tally. “This contract gives Denver a tool to connect those trips today, while we continue building out our core transit network.”

Under the agreement, RideLoop will operate a fleet of up to 230 electric vans staged across 14 service zones, with real-time dispatch through a mobile app and call-in hotline. The city’s Department of Transportation and Infrastructure (DOTI) projects the program will deliver approximately 4.8 million rides over the initial term, at an average public subsidy of $6.10 per trip. The contract includes options for two one-year extensions subject to performance benchmarks.

To address privacy concerns, DOTI officials said RideLoop must share only aggregated, de-identified trip data with the city and is prohibited from selling rider information to third parties. “We built privacy into the RFP from day one,” DOTI Director Camille Ortega told councilmembers. “Origin-destination pairs are generalized, and any dataset with fewer than 30 trips in a time window is automatically suppressed.”

Labor standards were a central point of debate. The contract requires a $24.50 hourly minimum for drivers, access to employer-paid health insurance, and a city-funded pathway for commercial driver’s license (CDL) training. Still, representatives from the Amalgamated Transit Union criticized the arrangement as “outsourcing” public service. “If Denver wants dependable transit, invest those dollars in union-run buses with pensions and stable routes,” said ATU Local 1005 President Marcus Bell. “Temporary vans are not a replacement for a real network.”

Neighborhood leaders from Montbello, Green Valley Ranch, and Westwood lined up in support, citing long waits between buses and safety concerns walking to distant stops. “I can’t leave my bakery for 40 minutes to catch a bus that might not show,” said small-business owner Teresa Delgado, who employs nine staff on Denver’s far northeast side. “If I can hail a shared van for my supplies and my employees, that keeps our shop open.”

Pricing will mirror existing transit discounts: standard fares will be $2.25 per trip, with 50% off for low-income riders enrolled in the city’s transit assistance program and free transfers to regional bus and rail within 90 minutes. Trips beginning or ending within a half mile of a hospital, library, or community college will receive automatic $1 credits during off-peak hours to encourage ridership.

Councilmember Ethan Ward, who voted no, questioned whether the service would cannibalize existing bus routes. “DOTI is projecting a 7% shift from single-occupancy vehicles, but I’m worried we’ll also poach riders from the 15L and the Federal Boulevard lines that frankly need more frequency, not competition,” Ward said. DOTI’s Ortega countered that RideLoop zones were drawn to avoid corridors with high-frequency bus service and that the city will publish quarterly reports on mode shift and route impacts.

The ordinance sets performance triggers that could reduce payments if on-time pickup rates dip below 92% or if average shared occupancy falls under 1.6 passengers per vehicle-hour for two consecutive quarters. “This is pay-for-performance, not a blank check,” Romero emphasized. “If benchmarks aren’t met, the public doesn’t pay.”

RideLoop CEO Nisha Patel pledged transparency. “We will publish uptime, wait times, and emissions savings every quarter,” Patel said. “Denver has set the bar high, and we intend to meet it.”

The program will launch in three phases beginning in January, starting with the Far Northeast, Southwest, and Sun Valley zones. DOTI plans citywide outreach events this fall, including sign-ups for a “concierge line” aimed at seniors and riders without smartphones. The city will also fund curb upgrades at 85 pickup locations to add lighting and seating.

As the council wrapped up deliberations, Romero framed the decision as a bridge, not a destination. “No one is saying microtransit alone is the system,” she said. “But when you’re getting off a late shift in winter dark and the next bus is in 45 minutes, a shared electric van that arrives in eight is not a luxury—it’s dignity.”

Mayor Luis Ortega is expected to sign the contract next week. DOTI said the first public dashboard on performance and privacy compliance will go live within 60 days of launch.
    """
    obj = extract_event(meta, article)
    print(json.dumps(obj, indent=2, ensure_ascii=False))
# extractor_base.py
import os, json, re, sqlite3, uuid, hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key="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") # uses OPENAI_API_KEY

DB_PATH = "sythn_data_4_article_grouping.db"

# -------------------- Schemas --------------------

EVENT_SCHEMA = {
  "type": "object",
  "additionalProperties": False,
  "properties": {
    "who": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
          "name": {"type": "string"},
          "role": {"type": "string"}
        },
        "required": ["name","role"]
      }
    },
    "to_whom": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
          "name": {"type": "string"},
          "role": {"type": "string"}
        },
        "required": ["name","role"]
      }
    },
    "action_lemma": {"type": "string"},
    "action_phrase": {"type": "string", "maxLength": 60},
    "when": {
      "type": "object",
      "additionalProperties": False,
      "properties": {
        "start": {"type": ["string","null"]},
        "end":   {"type": ["string","null"]},
        "grain": {"type": "string", "enum":["second","minute","hour","day","week","month","year","unknown"]},
        "text":  {"type": "string"}
      },
      "required": ["start","end","grain","text"]
    },
    "where": {
      "type": "object",
      "additionalProperties": False,
      "properties": {
        "name": {"type": "string"},
        "country": {"type": "string"}
      },
      "required": ["name","country"]
    },
    "summary":   {"type": "string"},
    "evidence":  {"type": "string"},
    "confidence":{"type": "number", "minimum": 0, "maximum": 1},
    "extras": {
    "type": "object",
    "additionalProperties": False,
    "properties": {},
    "required": []
}
  },
  "required": ["who","to_whom","action_lemma","action_phrase","when","where","summary","evidence","confidence","extras"]
}

ARTICLE_META_SCHEMA = {
  "type": "object",
  "additionalProperties": False,
  "properties": {
    "title": {"type": "string"},
    "category": {"type": "string"},
    "published_iso": {"type": "string"},
    "source": {"type": "string"},
    "country_hint": {"type": "string"},
    "city_hint": {"type": "string"}
  },
  "required": ["title","category","published_iso","source","country_hint","city_hint"]
}

TOP_SCHEMA = {
  "type": "object",
  "additionalProperties": False,
  "properties": {
    "article_meta": ARTICLE_META_SCHEMA,
    "article_text": {"type": "string"},
    "event": EVENT_SCHEMA
  },
  "required": ["article_meta","article_text","event"]
}

# -------------------- System prompt --------------------

SYSTEM_PROMPT = """You will generate a fresh, original news-style article and then extract the single primary event it contains. Output ONE strict JSON object with the keys article_meta, article_text, and event — no prose and no code fences.

Part A — Generate a news article (500–800 words)
• Category: pick from {politics, us_news, world_news, sports, business_economics, science, tech} unless the user specifies one.
• Primary event: exactly one concrete, real-world action (e.g., posted, signed, filed, voted, arrested, launched, acquired, recalled, announced, testified, evacuated, sanctioned, merged, IPO, discovered). The article may mention other facts, but there must be a single main event.
• Placement: name the city and the weekday or calendar date in the headline/lead (first 1–2 paragraphs). Avoid explicit clock times unless necessary.
• Actors: use canonical full names (e.g., “Donald Trump”, “Chicago Police Department”). If using a last name later, the full name must appear earlier.
• Style: neutral newsroom tone, clear paragraphs; include at least one quote and one number (vote count, dollar amount, attendance, score, etc.); use a sensible source name (e.g., “Metro Newswire”).
• Uniqueness: the article must be fictional but realistic and not copy any existing text.
• Length: 500–800 words.

Populate:
• article_meta: title, category, published_iso (use user-provided if given), source, country_hint, city_hint
• article_text: the full 500–800 word story.

Part B — Extract the single primary event (strict schema)
Return one event object under event with these fields only:
• who: array of {name, role} — actors of THIS event only; use canonical full names; each must appear in the evidence sentence (or the sentence immediately before it).
• to_whom: array of {name, role} — direct target/recipient (empty if none); include cities/orgs if obviously targeted.
• action_lemma: lowercase verb (e.g., “post”, “sign”, “vote”, “sue”, “arrest”, “protest”, “announce”, “launch”, “file”, “recall”, “evacuate”, “merge”, “sanction”, “testify”, “acquire”, “discover”, “charge”, “convict”).
• action_phrase: short verb phrase (≤6 words) lifted from the article that captures the action (e.g., “posted meme”, “signed executive order”, “filed lawsuit”).
• when: object {start:null, end:null, grain:"second|minute|hour|day|week|month|year|unknown", text}. If only a weekday/date phrase is present (e.g., “Friday”), put it in text, set grain="day", and keep start=end=null.
• where: {name:<city>, country:<country or "" if unknown>} — city,country; do not use buildings (“City Hall”).
• summary: 1–3 sentence neutral summary of the event.
• evidence: ONE exact sentence from the article containing the action.
• confidence: 0–1.
• extras: object (free-form; never a string). Add useful details (e.g., { "platform":"social media", "media_type":"meme" }).

Hard rules
• Output ONE JSON object with top-level keys article_meta, article_text, event.
• Do not include code fences or any extra text.
• Do not invent clock times; keep start=end=null unless an explicit time appears.
• If multiple actions are present, choose the primary one supported by headline/lead and least speculative.
"""

# -------------------- Helpers --------------------

WEEKDAYS = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]

def one_sentence(s: str) -> str:
    parts = re.split(r'(?<=[.!?])\s+', (s or "").strip())
    return parts[0].strip() if parts else (s or "").strip()

def resolve_date_bucket(when_text: str, published_iso: str):
    if not when_text or not published_iso:
        return None
    try:
        pub = datetime.fromisoformat(published_iso.replace("Z","+00:00")).date()
    except Exception:
        return None
    w = when_text.strip().lower()
    if w in WEEKDAYS:
        delta = (pub.weekday() - WEEKDAYS.index(w)) % 7
        return str(pub - timedelta(days=delta))
    m = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", when_text)
    return m.group(1) if m else None

def ensure_extras_obj(extras, evidence: str):
    if isinstance(extras, dict):
        out = dict(extras)
    elif extras is None:
        out = {}
    else:
        out = {"note": str(extras)}
    evl = (evidence or "").lower()
    if "tweet" in evl or "post" in evl or "posted" in evl:
        out.setdefault("platform", "social media")
    if "meme" in evl:
        out.setdefault("media_type", "meme")
    return out

def compute_derived(event: dict, published_iso: str, country_hint: str = ""):
    event["action_lemma"] = (event.get("action_lemma") or "").lower()
    event["evidence"] = one_sentence(event.get("evidence") or "")
    event["extras"] = ensure_extras_obj(event.get("extras"), event["evidence"])
    event.setdefault("to_whom", [])

    who_names = [p["name"] for p in event.get("who",[])]
    event["who_canon"] = who_names
    event["who_lastnames"] = [n.split()[-1].lower() for n in who_names if n]

    event["date_bucket"] = resolve_date_bucket(event.get("when",{}).get("text",""), published_iso)

    city = (event.get("where",{}).get("name") or "").strip()
    country = (event.get("where",{}).get("country") or country_hint or "").strip()
    event["where"] = {"name": city, "country": country}
    event["place_key"] = ",".join([x for x in [city, country] if x])

    phrase = (event.get("action_phrase") or event["action_lemma"]).strip()
    event["line_text"] = f'{event["date_bucket"] or event.get("when",{}).get("text","")} | {phrase} | WHO:{";".join(who_names)} | WHERE:{event["place_key"]}'

    ev = (event.get("evidence") or "").lower()
    event["speculative"] = any(t in ev for t in ["plan to","may ","expected to","proposed","considering"])

    try:
        event["confidence"] = max(0.0, min(1.0, float(event.get("confidence", 0.5))))
    except Exception:
        event["confidence"] = 0.5

    return event

# -------------------- SQLite (synthetic-only) --------------------

DDL = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS synthetic_samples (
  sample_id     TEXT PRIMARY KEY,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  model         TEXT NOT NULL,
  system_hash   TEXT,
  user_block    TEXT,
  raw_json      TEXT NOT NULL,

  -- from article_meta
  title         TEXT,
  category      TEXT,
  published_iso TEXT,
  source        TEXT,
  country_hint  TEXT,
  city_hint     TEXT,

  -- from event (core + derived you’ll likely query)
  action_lemma  TEXT,
  action_phrase TEXT,
  when_text     TEXT,
  when_grain    TEXT CHECK (when_grain IN ('second','minute','hour','day','week','month','year','unknown')),
  where_city    TEXT,
  where_country TEXT,
  evidence      TEXT,
  summary       TEXT,
  confidence    REAL CHECK (confidence BETWEEN 0 AND 1),

  date_bucket   TEXT,
  place_key     TEXT,
  line_text     TEXT,
  speculative   INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_syn_bucket   ON synthetic_samples(date_bucket);
CREATE INDEX IF NOT EXISTS idx_syn_place    ON synthetic_samples(place_key);
CREATE INDEX IF NOT EXISTS idx_syn_action   ON synthetic_samples(action_lemma);
CREATE INDEX IF NOT EXISTS idx_syn_cat_date ON synthetic_samples(category, date_bucket);
"""

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(DDL)
    conn.commit()
    return conn, cur

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def insert_synthetic(cur, model_name: str, system_prompt: str, user_block: str, obj: dict):
    meta = obj.get("article_meta", {})
    ev = obj.get("event", {})

    sample_id = str(uuid.uuid4())
    row = (
        sample_id,
        model_name,
        sha256(system_prompt),
        user_block,
        json.dumps(obj, ensure_ascii=False),

        meta.get("title",""),
        meta.get("category",""),
        meta.get("published_iso",""),
        meta.get("source",""),
        meta.get("country_hint",""),
        meta.get("city_hint",""),

        ev.get("action_lemma",""),
        ev.get("action_phrase",""),
        (ev.get("when") or {}).get("text",""),
        (ev.get("when") or {}).get("grain",""),
        (ev.get("where") or {}).get("name",""),
        (ev.get("where") or {}).get("country",""),
        ev.get("evidence",""),
        ev.get("summary",""),
        float(ev.get("confidence", 0.5)) if isinstance(ev.get("confidence", 0.5), (int,float,str)) else 0.5,

        ev.get("date_bucket",""),
        ev.get("place_key",""),
        ev.get("line_text",""),
        1 if ev.get("speculative", False) else 0
    )

    cur.execute("""
        INSERT INTO synthetic_samples (
          sample_id, model, system_hash, user_block, raw_json,
          title, category, published_iso, source, country_hint, city_hint,
          action_lemma, action_phrase, when_text, when_grain, where_city, where_country,
          evidence, summary, confidence, date_bucket, place_key, line_text, speculative
        ) VALUES (?,?,?,?,?,
                  ?,?,?,?,?,?,
                  ?,?,?,?,?,?,
                  ?,?,?,?, ?,?,?)
    """, row)
    return sample_id

# -------------------- Model call --------------------

def generate_and_extract(category: str = "random",
                         published_iso: str = "",
                         country_hint: str = "",
                         city_hint: str = "",
                         source_style: str = "Metro Newswire",
                         length: str = "500-800"):
    user_block = f"""TASK: generate_and_extract
CATEGORY: {category}
PUBLISHED_ISO: {published_iso}
COUNTRY_HINT: {country_hint}
CITY_HINT: {city_hint}
SOURCE_STYLE: {source_style}
LENGTH: {length}"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_block}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "ArticleWithEvent",
                "schema": TOP_SCHEMA,
                "strict": True
            }
        }
    )

    obj = json.loads(resp.choices[0].message.content)
    # derive/sanitize event before storing (helps queries later)
    meta = obj.get("article_meta", {})
    obj["event"] = compute_derived(obj.get("event", {}), meta.get("published_iso",""), meta.get("country_hint",""))
    return obj, user_block, resp.model  # return model name for provenance

# -------------------- Demo (generate 1 sample and store) --------------------

if __name__ == "__main__":
    conn, cur = init_db()
    
    # Categories to generate articles for
    categories = ["politics", "us_news", "world_news", "sports", "business_economics", "science", "tech"]
    
    # Cities and countries for variety
    locations = [
        ("United States", "New York"),
        ("United States", "Los Angeles"), 
        ("United Kingdom", "London"),
        ("Canada", "Toronto"),
        ("Australia", "Sydney"),
        ("Germany", "Berlin"),
        ("France", "Paris")
    ]
    
    import random
    
    print("Starting article generation loop...")
    print("Generating 500 articles for full dataset...")
    
    # Generate 500 articles with random categories and locations
    for i in range(500):
        try:
            # Pick a random category
            category = random.choice(categories)
            
            # Pick a random location
            country, city = random.choice(locations)
            
            # Generate a random timestamp for this week
            base_time = "2025-09-06T15:54:00Z"
            
            print(f"Generating article {i + 1}/500: {category} from {city}, {country}")
            
            obj, user_blk, model_name = generate_and_extract(
                category=category,
                published_iso=base_time,
                country_hint=country,
                city_hint=city,
                source_style="AP-style wire",
                length="500-800"
            )

            sample_id = insert_synthetic(cur, model_name, SYSTEM_PROMPT, user_blk, obj)
            conn.commit()
            print(f"✓ Inserted synthetic sample: {sample_id} - {obj['article_meta']['title'][:50]}...")
            
            # Show progress every 50 articles
            if (i + 1) % 50 == 0:
                print(f"\n🎉 Progress: {i + 1}/500 articles completed ({(i + 1)/500*100:.1f}%)\n")
            
        except Exception as e:
            print(f"✗ Error generating article {i + 1}: {e}")
            continue
    
    print(f"\nCompleted! Generated articles saved to {DB_PATH}")
    
    # Show summary
    cur.execute("SELECT COUNT(*) FROM synthetic_samples")
    count = cur.fetchone()[0]
    print(f"Total articles in database: {count}")
    
    # Show category distribution
    print("\nCategory Distribution:")
    cur.execute("SELECT category, COUNT(*) FROM synthetic_samples GROUP BY category ORDER BY COUNT(*) DESC")
    for category, cat_count in cur.fetchall():
        print(f"  {category}: {cat_count} articles ({cat_count/count*100:.1f}%)")
    
    # Show location distribution
    print("\nTop Locations:")
    cur.execute("SELECT city_hint, country_hint, COUNT(*) FROM synthetic_samples GROUP BY city_hint, country_hint ORDER BY COUNT(*) DESC LIMIT 10")
    for city, country, loc_count in cur.fetchall():
        print(f"  {city}, {country}: {loc_count} articles")
    
    print(f"\n🎉 Dataset generation complete! {count} articles ready for training.")
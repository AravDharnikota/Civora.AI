#!/usr/bin/env python3
"""
Export training data from SQLite DB to JSONL for SFT (Supervised Fine-Tuning).

Usage:
    python export_sft_jsonl.py --db synthetic.db
    python export_sft_jsonl.py --db synthetic.db --dev-ratio 0.2 --limit 1000
"""

import sqlite3
import json
import random
import argparse
import os
import sys
from typing import List, Dict, Any, Tuple


# Default system prompt placeholder
DEFAULT_SYSTEM_PROMPT = "<<PASTE YOUR SYSTEM PROMPT HERE>>"


def load_system_prompt(prompt_path: str) -> str:
    """Load system prompt from file or return default."""
    if not prompt_path:
        return DEFAULT_SYSTEM_PROMPT
    
    if not os.path.exists(prompt_path):
        print(f"Warning: System prompt file '{prompt_path}' not found, using default.")
        return DEFAULT_SYSTEM_PROMPT
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print(f"Warning: Error reading system prompt file: {e}, using default.")
        return DEFAULT_SYSTEM_PROMPT


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def build_user_content(article_meta: Dict[str, Any], article_text: str) -> str:
    """Build the user content block from article metadata and text."""
    return f"""ARTICLE_META:
title: {article_meta.get('title', '')}
published_iso: {article_meta.get('published_iso', '')}
source: {article_meta.get('source', '')}
country_hint: {article_meta.get('country_hint', '')}
city_hint: {article_meta.get('city_hint', '')}

ARTICLE_TEXT:
{article_text}"""


def process_row(raw_json_str: str) -> Dict[str, Any] | None:
    """Process a single row from the database."""
    try:
        data = json.loads(raw_json_str)
        
        # Validate required keys
        if not all(key in data for key in ['article_meta', 'article_text', 'event']):
            return None
        
        article_meta = data['article_meta']
        article_text = data['article_text']
        event = data['event']
        
        # Filter: skip if article_text < 100 words
        if count_words(article_text) < 100:
            return None
        
        # Filter: skip if event is not a dict
        if not isinstance(event, dict):
            return None
        
        return {
            'article_meta': article_meta,
            'article_text': article_text,
            'event': event
        }
    
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        return None


def create_chat_sample(article_data: Dict[str, Any], system_prompt: str) -> Dict[str, Any]:
    """Create a chat sample in the required format."""
    user_content = build_user_content(
        article_data['article_meta'], 
        article_data['article_text']
    )
    
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": json.dumps(article_data['event'])}
        ]
    }


def split_data(samples: List[Dict[str, Any]], dev_ratio: float) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split samples into train and dev sets."""
    random.shuffle(samples)
    
    dev_size = int(len(samples) * dev_ratio)
    dev_samples = samples[:dev_size]
    train_samples = samples[dev_size:]
    
    return train_samples, dev_samples


def write_jsonl(samples: List[Dict[str, Any]], output_path: str) -> None:
    """Write samples to JSONL file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(sample) + '\n')


def main():
    parser = argparse.ArgumentParser(description='Export SQLite DB to JSONL for SFT')
    parser.add_argument('--db', default='synthetic.db', help='SQLite database file (default: synthetic.db)')
    parser.add_argument('--out-train', default='train.jsonl', help='Output train file (default: train.jsonl)')
    parser.add_argument('--out-dev', default='dev.jsonl', help='Output dev file (default: dev.jsonl)')
    parser.add_argument('--dev-ratio', type=float, default=0.15, help='Dev set ratio (default: 0.15)')
    parser.add_argument('--limit', type=int, default=0, help='Limit number of rows (0 = all, default: 0)')
    parser.add_argument('--system-prompt', help='Path to system prompt file')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not os.path.exists(args.db):
        print(f"Error: Database file '{args.db}' not found.")
        sys.exit(1)
    
    if args.dev_ratio < 0 or args.dev_ratio > 1:
        print(f"Error: dev-ratio must be between 0 and 1, got {args.dev_ratio}")
        sys.exit(1)
    
    if args.limit < 0:
        print(f"Error: limit must be non-negative, got {args.limit}")
        sys.exit(1)
    
    # Load system prompt
    system_prompt = load_system_prompt(args.system_prompt)
    
    # Connect to database
    try:
        conn = sqlite3.connect(args.db)
        cursor = conn.cursor()
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)
    
    # Build query
    query = "SELECT raw_json FROM synthetic_samples WHERE raw_json IS NOT NULL"
    if args.limit > 0:
        query += f" LIMIT {args.limit}"
    
    # Read and process rows
    print(f"Reading from database: {args.db}")
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    total_rows = len(rows)
    print(f"Total rows read: {total_rows}")
    
    if total_rows == 0:
        print("Error: No rows found in database.")
        sys.exit(1)
    
    # Process rows
    valid_samples = []
    dropped_count = 0
    
    for row in rows:
        raw_json_str = row[0]
        processed = process_row(raw_json_str)
        
        if processed:
            valid_samples.append(processed)
        else:
            dropped_count += 1
    
    print(f"Valid samples: {len(valid_samples)}")
    print(f"Dropped samples: {dropped_count}")
    
    if len(valid_samples) == 0:
        print("Error: No valid samples found after filtering.")
        sys.exit(1)
    
    # Create chat samples
    chat_samples = []
    for sample in valid_samples:
        chat_sample = create_chat_sample(sample, system_prompt)
        chat_samples.append(chat_sample)
    
    # Split into train/dev
    train_samples, dev_samples = split_data(chat_samples, args.dev_ratio)
    
    # Write output files
    write_jsonl(train_samples, args.out_train)
    write_jsonl(dev_samples, args.out_dev)
    
    # Print summary
    print(f"\n=== EXPORT SUMMARY ===")
    print(f"Total rows read: {total_rows}")
    print(f"Valid samples kept: {len(valid_samples)}")
    print(f"Samples dropped: {dropped_count}")
    print(f"Train samples: {len(train_samples)}")
    print(f"Dev samples: {len(dev_samples)}")
    print(f"Train file: {args.out_train}")
    print(f"Dev file: {args.out_dev}")
    print(f"System prompt: {'Custom file' if args.system_prompt else 'Default placeholder'}")
    
    print(f"\nExport completed successfully!")


if __name__ == "__main__":
    main()






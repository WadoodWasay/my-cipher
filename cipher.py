"""
My Cipher - A symmetric cipher using count, terminator, and noise tokens.

The alphabet (A-Z, a-z) maps to values 1-52. Characters are encoded by:
1. Using N count tokens (where N is the character's value)
2. Optionally interspersing noise tokens
3. Ending with a terminator token

Decoding counts the count tokens between terminators to recover the original value.
"""

import random
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


CHARSET = ''.join(c for pair in zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 
                                     'abcdefghijklmnopqrstuvwxyz') 
                  for c in pair)

ENGLISH_FREQUENCY = {
    'e': 12.7, 't': 9.1, 'a': 8.2, 'o': 7.5, 'i': 7.0, 'n': 6.7,
    's': 6.3, 'h': 6.1, 'r': 6.0, 'd': 4.3, 'l': 4.0, 'c': 2.8,
    'u': 2.8, 'm': 2.4, 'w': 2.4, 'f': 2.2, 'g': 2.0, 'y': 2.0,
    'p': 1.9, 'b': 1.5, 'v': 1.0, 'k': 0.8, 'j': 0.15, 'x': 0.15,
    'q': 0.10, 'z': 0.07
}


def create_default_mapping() -> dict[str, int]:
    return {c: i + 1 for i, c in enumerate(CHARSET)}


def create_random_mapping(seed: Optional[int] = None) -> dict[str, int]:
    if seed is not None:
        random.seed(seed)
    
    values = list(range(1, 53))
    random.shuffle(values)
    return {c: v for c, v in zip(CHARSET, values)}


def create_frequency_mapping(inverse: bool = True) -> dict[str, int]:
    """
        inverse: If True, common letters get HIGH values (longer encoding).
                 If False, common letters get LOW values (shorter encoding).
    When inverse=True (default), this normalizes message lengths because
    frequently-used letters require more tokens to encode.
    """
    # Sort letters by frequency (ascending = rare first)
    # When inverse=True: rare letters first (low values), common letters last (high values)
    # When inverse=False: common letters first (low values), rare letters last (high values)
    sorted_letters = sorted(ENGLISH_FREQUENCY.keys(), 
                           key=lambda x: ENGLISH_FREQUENCY[x],
                           reverse=not inverse)
    
    mapping = {}
    value = 1
    
    for letter in sorted_letters:
        # Uppercase gets value, lowercase gets value+1
        mapping[letter.upper()] = value
        mapping[letter.lower()] = value + 1
        value += 2
    
    return mapping


def create_custom_mapping(order: str) -> dict[str, int]:
    """
    Create a mapping from a custom ordering string.
    
    Args:
        order: A string of 26 letters (case-insensitive) specifying the order.
               First letter gets values 1-2, second gets 3-4, etc.
    
    Example: "etaoinshrdlu..." would give 'E'=1, 'e'=2, 'T'=3, 't'=4, ...
    """
    order = order.lower()
    if len(order) != 26 or len(set(order)) != 26:
        raise ValueError("Order must contain exactly 26 unique letters")
    
    mapping = {}
    value = 1
    
    for letter in order:
        mapping[letter.upper()] = value
        mapping[letter.lower()] = value + 1
        value += 2
    
    return mapping


@dataclass
class Key:
    """Cipher key containing the three token categories and character mapping."""
    count_tokens: set[str]
    terminator_tokens: set[str]
    noise_tokens: set[str]
    char_to_num: dict[str, int] = field(default_factory=create_default_mapping)
    
    def __post_init__(self):
        # Build reverse mapping
        self.num_to_char = {v: k for k, v in self.char_to_num.items()}
    
    def to_dict(self) -> dict:
        return {
            'count': sorted(self.count_tokens),
            'terminator': sorted(self.terminator_tokens),
            'noise': sorted(self.noise_tokens),
            'mapping': self.char_to_num
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Key':
        mapping = data.get('mapping', create_default_mapping())
        return cls(
            count_tokens=set(data['count']),
            terminator_tokens=set(data['terminator']),
            noise_tokens=set(data['noise']),
            char_to_num=mapping
        )
    
    def save(self, path: str) -> None:
        """Save key to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: str) -> 'Key':
        """Load key from JSON file."""
        with open(path) as f:
            return cls.from_dict(json.load(f))


def generate_key(
    count_ratio: float = 0.4,
    terminator_ratio: float = 0.2,
    mapping_mode: str = 'random',
    seed: Optional[int] = None
) -> Key:
    """
    Generate a random key by partitioning the 52 characters.
    
    Args:
        count_ratio: Proportion of characters to use as count tokens (default 0.4)
        terminator_ratio: Proportion for terminator tokens (default 0.2)
        mapping_mode: How to assign character values:
            - 'default': Sequential (A=1, a=2, B=3, ...)
            - 'random': Randomized mapping
            - 'frequency': Common letters get high values (normalizes length)
            - 'frequency-inv': Common letters get low values (shorter messages)
        seed: Optional random seed for reproducibility
    
    Returns:
        A Key object with randomly assigned token categories
    """
    if seed is not None:
        random.seed(seed)
    
    # Create character mapping based on mode
    if mapping_mode == 'default':
        char_mapping = create_default_mapping()
    elif mapping_mode == 'random':
        char_mapping = create_random_mapping(seed)
    elif mapping_mode == 'frequency':
        char_mapping = create_frequency_mapping(inverse=True)
    elif mapping_mode == 'frequency-inv':
        char_mapping = create_frequency_mapping(inverse=False)
    else:
        raise ValueError(f"Unknown mapping mode: {mapping_mode}")
    
    # Re-seed for token partition (in case mapping used the seed)
    if seed is not None:
        random.seed(seed + 1000)
    
    chars = list(CHARSET)
    random.shuffle(chars)
    
    n_count = int(len(chars) * count_ratio)
    n_term = int(len(chars) * terminator_ratio)
    
    # Ensure at least 1 of each type
    n_count = max(1, n_count)
    n_term = max(1, n_term)
    
    count_tokens = set(chars[:n_count])
    terminator_tokens = set(chars[n_count:n_count + n_term])
    noise_tokens = set(chars[n_count + n_term:])
    
    return Key(count_tokens, terminator_tokens, noise_tokens, char_mapping)


def encode(
    plaintext: str,
    key: Key,
    noise_probability: float = 0.3,
    max_noise_per_char: int = 5,
    prefix_noise: int = 0,
    seed: Optional[int] = None
) -> str:
    """
    Encode plaintext using the tally cipher.
    
    Args:
        plaintext: Text to encode (only A-Za-z characters are encoded)
        key: The cipher key
        noise_probability: Chance of inserting noise between count tokens
        max_noise_per_char: Maximum noise tokens to insert per character
        prefix_noise: Number of noise/terminator tokens to add at the start
        seed: Optional random seed for reproducibility
    
    Returns:
        Encoded ciphertext
    """
    if seed is not None:
        random.seed(seed)
    
    count_list = list(key.count_tokens)
    term_list = list(key.terminator_tokens)
    noise_list = list(key.noise_tokens)
    prefix_pool = term_list + noise_list
    
    result = []
    
    # Optional prefix noise
    for _ in range(prefix_noise):
        result.append(random.choice(prefix_pool))
    
    for char in plaintext:
        if char not in key.char_to_num:
            # Non-alphabet characters pass through or could be handled differently
            # For now, we skip them (or you could encode spaces specially)
            continue
        
        value = key.char_to_num[char]
        noise_count = 0
        
        # Emit 'value' count tokens with optional noise
        for i in range(value):
            result.append(random.choice(count_list))
            
            # Maybe insert noise (but not after the last count token)
            if (i < value - 1 and 
                noise_list and 
                noise_count < max_noise_per_char and
                random.random() < noise_probability):
                result.append(random.choice(noise_list))
                noise_count += 1
        
        # End with terminator
        result.append(random.choice(term_list))
    
    return ''.join(result)


def decode(ciphertext: str, key: Key) -> str:
    """
    Decode ciphertext using the tally cipher.
    
    Args:
        ciphertext: Text to decode
        key: The cipher key
    
    Returns:
        Decoded plaintext
    """
    result = []
    count = 0
    started = False  # Track if we've seen at least one count token
    
    for char in ciphertext:
        if char in key.count_tokens:
            count += 1
            started = True
        elif char in key.terminator_tokens:
            if started and count > 0:
                if count in key.num_to_char:
                    result.append(key.num_to_char[count])
                else:
                    # Count out of range - invalid
                    result.append('?')
            count = 0
            started = False
        elif char in key.noise_tokens:
            # Ignore noise
            pass
        else:
            # Unknown character - not in key
            pass
    
    return ''.join(result)


def analyze_key(key: Key) -> dict:
    """Return statistics about a key."""
    # Calculate average value for frequency analysis
    values = list(key.char_to_num.values())
    avg_value = sum(values) / len(values)
    
    # Check if mapping appears to be frequency-based
    common_letters = ['e', 't', 'a', 'o', 'i', 'n']
    common_avg = sum(key.char_to_num.get(c, 0) for c in common_letters) / len(common_letters)
    rare_letters = ['z', 'q', 'x', 'j']
    rare_avg = sum(key.char_to_num.get(c, 0) for c in rare_letters) / len(rare_letters)
    
    if common_avg > rare_avg + 10:
        mapping_type = 'frequency-weighted (common=high)'
    elif rare_avg > common_avg + 10:
        mapping_type = 'frequency-weighted (common=low)'
    else:
        mapping_type = 'random or sequential'
    
    return {
        'count_tokens': len(key.count_tokens),
        'terminator_tokens': len(key.terminator_tokens),
        'noise_tokens': len(key.noise_tokens),
        'total': len(key.count_tokens) + len(key.terminator_tokens) + len(key.noise_tokens),
        'mapping_type': mapping_type,
        'avg_common_value': round(common_avg, 1),
        'avg_rare_value': round(rare_avg, 1)
    }


def main():
    parser = argparse.ArgumentParser(
        description='My Cipher - name in progress'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Generate key
    gen_parser = subparsers.add_parser('keygen', help='Generate a new key')
    gen_parser.add_argument('-o', '--output', default='key.json', help='Output file')
    gen_parser.add_argument('--count-ratio', type=float, default=0.4)
    gen_parser.add_argument('--term-ratio', type=float, default=0.2)
    gen_parser.add_argument('--mapping', choices=['default', 'random', 'frequency', 'frequency-inv'],
                           default='random', help='Character value mapping mode')
    gen_parser.add_argument('--seed', type=int, help='Random seed')
    
    # Encode
    enc_parser = subparsers.add_parser('encode', help='Encode a message')
    enc_parser.add_argument('message', help='Message to encode')
    enc_parser.add_argument('-k', '--key', default='key.json', help='Key file')
    enc_parser.add_argument('--noise', type=float, default=0.3, help='Noise probability')
    enc_parser.add_argument('--seed', type=int, help='Random seed')
    
    # Decode
    dec_parser = subparsers.add_parser('decode', help='Decode a message')
    dec_parser.add_argument('ciphertext', help='Ciphertext to decode')
    dec_parser.add_argument('-k', '--key', default='key.json', help='Key file')
    
    # Show key
    show_parser = subparsers.add_parser('showkey', help='Display key information')
    show_parser.add_argument('-k', '--key', default='key.json', help='Key file')
    show_parser.add_argument('--show-mapping', action='store_true', help='Show full character mapping')
    
    args = parser.parse_args()
    
    if args.command == 'keygen':
        key = generate_key(args.count_ratio, args.term_ratio, args.mapping, args.seed)
        key.save(args.output)
        print(f"Key saved to {args.output}")
        stats = analyze_key(key)
        print(f"  Count tokens: {stats['count_tokens']}")
        print(f"  Terminator tokens: {stats['terminator_tokens']}")
        print(f"  Noise tokens: {stats['noise_tokens']}")
        print(f"  Mapping: {stats['mapping_type']}")
    
    elif args.command == 'encode':
        key = Key.load(args.key)
        ciphertext = encode(args.message, key, args.noise, seed=args.seed)
        print(ciphertext)
    
    elif args.command == 'decode':
        key = Key.load(args.key)
        plaintext = decode(args.ciphertext, key)
        print(plaintext)
    
    elif args.command == 'showkey':
        key = Key.load(args.key)
        stats = analyze_key(key)
        print(f"Count tokens ({stats['count_tokens']}): {''.join(sorted(key.count_tokens))}")
        print(f"Terminator tokens ({stats['terminator_tokens']}): {''.join(sorted(key.terminator_tokens))}")
        print(f"Noise tokens ({stats['noise_tokens']}): {''.join(sorted(key.noise_tokens))}")
        print(f"Mapping type: {stats['mapping_type']}")
        print(f"  Common letters (e,t,a,o,i,n) avg value: {stats['avg_common_value']}")
        print(f"  Rare letters (z,q,x,j) avg value: {stats['avg_rare_value']}")
        
        if args.show_mapping:
            print("\nFull character mapping:")
            # Sort by value for readability
            sorted_mapping = sorted(key.char_to_num.items(), key=lambda x: x[1])
            for char, val in sorted_mapping:
                print(f"  {val:2d} -> {char}")


if __name__ == '__main__':
    main()

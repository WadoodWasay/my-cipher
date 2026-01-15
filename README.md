# My Cipher
A symetric cipher designed by me. Name in progress. 
## Overview
This is a custom encryption algorithm that uses a dynamic set of secret special tokens, cycling terminators, and random noise injection to encrypt plaintext messages.

## How it works
The alphabet is divided into uppercase and lowercase characters, and each character is given a number. This can be any number, as long as no letters share a corresponding number value. For this example (and for simplicity purposes) the letters and their corresponding numbers are in order.

To encode a character, let us use 'b' in this example, we will use four count tokens, as 'b' is associated with the number four. This can be encoded via using only count tokens if wished, but may also be encoded by randomly inserting noise tokens into the string. The character will be dictated to have been "ended" when a terminator token is encountered. In this way, a character can be encoded and result in the encoded version of itself being relatively short in length, or infinitely long due to continued addition of noise tokens.  

The terminator tokens do not need to immediately be followed by the start of another character, whether starting from a count token or a noise token, and instead, multiple terminators can be strung together, and even have noise tokens sprinkled between them. 

As counting only starts from the first count token, any number of terminator or noise tokens can be used at both the beginning of the token, and and number of noise tokens may be used in between the count tokens of the encoded message. 

There's also the possibility of setting the more frequently used letters to higher number values and less frequently used ones to lower number values to ensure that messages are longer and more likely to be of similar lengths. This combined with adding even more noise tokens to make shorter messages appear longer would increase the effectiveness of this cypher, and reduce the length leakage weakness discussed bellow. 

### Encoding and Decoding processes
#### Encoding Process
To encode a character with value N:
- Emit N count tokens (selected randomly from the count token set)
- Optionally intersperse noise tokens between count tokens
- Emit a terminator token

#### Decoding Process
- Scan the ciphertext left to right
- Increment a counter for each count token
- On terminator: map counter → character, reset counter
- Ignore noise tokens entirely

### Example 
Now let us work through the example stated above. The character 'b' can be encoded in the following ways, note that this is not an exhaustive list, and only meant to illustrate and clarify my explanation of the cypher given above: 
- WvkBy
- ZqHeCWEYAhxvVomFghLrO

### Strengths and Weaknesses
#### Strengths 
- Variable-length encoding: The same plaintext character produces different ciphertext each time due to random token selection and noise insertion, defeating simple frequency analysis.
- No fixed patterns: Unlike substitution ciphers, there's no 1:1 mapping between plaintext and ciphertext symbols.
- Plausible deniability: The noise tokens make it difficult to determine message boundaries or even confirm a message exists.

#### Weaknesses
- Key distribution: The key must be securely shared between parties (classic symmetric key problem). The key fully specifies the cipher.
- Small key space: The key is a partition of 52 elements into 3 sets. While there are many such partitions, a determined attacker with known plaintext could potentially enumerate them.
- Length leakage: Despite noise, longer messages still produce longer ciphertext. The average expansion ratio is predictable.
- Statistical attacks: With sufficient ciphertext, an attacker might identify count tokens by their higher frequency relative to terminators.

### Prerequisites
  - Python 3.x

### Installation
- Clone the repository:
```bash
  git clone https://github.com/WadoodWasay/my-cipher
  cd my-cipher
```

## Mapping Modes 
#### Random 
Shuffled character to value assignment 
- Use for maximum key entropy 
#### Simple
Sequential, A=1, a=2, B=3, ...
- Use for debugging 
#### Frequency 
Common letters (e, t, a, ...) get high values
- Use to normalize message length 
#### Frequency-inv
Common letters get low values 
- Shorter average messages (why would you ever use this)

## Usage
Help command
```bash
python3 cipher.py -h
```
Generate a key
```bash 
python3 cipher.py keygen -o <key_file-name>.json
```

Options:
- `--mapping` — Character vaue mapping mode (default: `random`)
  - `random`: Shuffled mapping (recommended)
  - `default`: Sequential A=1, a=2, B=3...
  - `frequency`: Common letters get high values (normalizes length)
  - `frequency-inv`: Common letters get low values
- `--count-ratio` — Proportion of chars as count tokens (default: 0.4)
- `--term-ratio` — Proportion as terminator tokens (default: 0.2)
- `--seed` — Random seed for reproducible key generation

### Encode a Message
```bash
python tally_cipher.py encode "Your message here" -k <key_file-name>.json
```

### Decode a Message
```bash
python tally_cipher.py decode "ciphertext_here" -k <key_file-name>.json
```

### Inspect a Key
```bash
python tally_cipher.py showkey -k <key_file-name>.json
```

Options:
- `--noise` — Probability of inserting noise between counts (default: 0.3)
- `--seed` — Random seed for reproducible encoding

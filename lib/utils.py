from jsonschema import validate, ValidationError


def text_chunks(text, encoder, tokens_per_chunk=4096, overlap=256):
    """
    Split a long text into chunks of a given size, ensuring continuity between chunks by overlapping tokens.

    Args:
        text (str): The text to split into chunks.
        encoder (Encoder): The encoder used to encode the text.
        tokens_per_chunk (int): The maximum number of tokens per chunk.
        overlap (int): The number of tokens to include from the previous chunk for continuity.

    Returns:
        list: A list of text chunks.
    """
    tokens = encoder.encode(text)
    chunks = []
    
    for i in range(0, len(tokens), tokens_per_chunk - overlap):
        chunk_tokens = tokens[i:i + tokens_per_chunk]
        chunks.append(encoder.decode(chunk_tokens))

        if i + tokens_per_chunk >= len(tokens):  # Stop if the last chunk reaches the end
            break

    return chunks


def text_chunks_by_lines(text, encoder, tokens_per_chunk=4096):
    """
    Split a long text into chunks by linebreaks, while keeping the chunks under a given size.

    Args:
        text (str): The text to split into chunks.
        encoder (Encoder): The encoder used to encode the text.
        tokens_per_chunk (int): The maximum number of tokens per chunk.
    """
    lines = text.split("\n")
    chunks = []
    chunk = ""
    num_tokens = 0
    for line in lines:
        line_len = len(encoder.encode(line))
        if num_tokens + line_len > tokens_per_chunk:
            chunks.append(chunk)
            chunk = ""
            num_tokens = 0
        chunk += line + "\n"
        num_tokens += line_len

    chunks.append(chunk)
    return chunks

def truncate_text(text, encoder, max_tokens=4096):
    """
    Truncate a long text to fit within a specified token limit.

    Args:
        text (str): The text to truncate.
        encoder (Encoder): The encoder used to encode the text.
        max_tokens (int): The maximum number of tokens allowed.

    Returns:
        str: The truncated text.
    """
    tokens = encoder.encode(text)
    if len(tokens) < max_tokens:
        return text
    
    tokens = tokens[:max_tokens]
    return encoder.decode(tokens)


def validate_json_with_schema(json_data: dict, schema: dict) -> bool:
    """
    Validate the parsed JSON data against the defined schema.
    """
    try:
        validate(instance=json_data, schema=schema)
        return True
    except ValidationError as e:
        print(f"Validation Error: {e.message}")
        return False

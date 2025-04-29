import os
import random
import json
import importlib
import asyncio
from datetime import datetime

import numpy as np

from statements.chat_client import ChatClient, OpenAIChatModel
from statements.extractor import Extractor


SEED = 42
START = 0
END = 100
NUM_WORKERS = 10
TIMEOUT = 360

random.seed(SEED)
np.random.seed(SEED)


def save_results(parser, output_dir, prefix="quotations"):
    """Save the results to files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(output_dir, exist_ok=True)

    messages_file = os.path.join(output_dir, f"{prefix}_messages_{timestamp}.jsonl")
    with open(messages_file, "w", encoding="utf-8") as file:
        for record in parser.messages:
            file.write(json.dumps(record) + "\n")

    # Save the full dataset as JSONL.
    jsonl_file = os.path.join(output_dir, f"{prefix}_{timestamp}.jsonl")
    with open(jsonl_file, "w", encoding="utf-8") as file:
        for record in parser.results.values():
            file.write(json.dumps(record) + "\n")

    # Save a sample of the results as a JSON file.
    sample_file = os.path.join(output_dir, f"{prefix}_sample_{timestamp}.json")
    with open(sample_file, "w", encoding="utf-8") as sample_file:
        json.dump({k: parser.results[k] for k in list(
            parser.results.keys())[:5]}, sample_file, indent=4)


async def main():
    # Define the paths to the data files
    module_name = "ideology_comparison"
    module_path = os.path.join("examples", "modules", module_name)
    module = importlib.import_module(f"examples.modules.{module_name}.ideology")
    
    # Prepare the dataset
    data_file = os.path.join("test_data", "topics_10k.csv")
    dataset = module.ArticleDataset(data_file=data_file, start=START, end=END)

    # Initialize the ChatClient and IO classes
    template_file = os.path.join(module_path, "ideology_template.md")
    schema_file = os.path.join(module_path, "ideology_schema.json")
    prompt_template = module.IdeologyPromptTemplate(template_file)
    output_parser = module.IdeologyOutputParser(schema_file)

    # Run the extraction
    extractor = Extractor(
        model=OpenAIChatModel("gpt-4o-mini"),
        dataset=dataset,
        client=ChatClient(timeout=TIMEOUT),
        prompt_template=prompt_template,
        output_parser=output_parser,
        num_workers=NUM_WORKERS
    )
    await extractor.run()

    # Save the results.
    today = datetime.now().strftime("%Y%m%d")
    save_results(output_parser,
                 os.path.join("output", today),
                 prefix=f"topics_10k_{module_name}")

    print("Extraction complete.")

    # Close the ChatClient.
    await extractor.close()


if __name__ == "__main__":
    asyncio.run(main())

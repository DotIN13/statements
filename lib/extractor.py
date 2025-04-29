import asyncio

from tqdm import tqdm

from lib.chat_client import ChatClient
from lib.exceptions import CensoredResponseException


class Extractor:
    def __init__(
        self,
        model,
        dataset,
        prompt_template,
        output_parser,
        num_workers=8,
        client=None,
        debug=None
    ):
        """
        Initializes the Extractor with the model, prompt template, parser.
        """
        self.model = model
        self.dataset = dataset
        self.prompt_template = prompt_template
        self.parser = output_parser

        self.num_workers = num_workers
        self.queue = None
        self.pbar = None

        self.client = client or ChatClient()
        self.debug = debug
        
    async def run(self):
        """Spawn workers to extract quotations from the dataset using the LLM model."""
        # Create an asyncio Queue and add tasks
        self.queue = asyncio.Queue()
        len_dataset = len(self.dataset)
        for idx in range(len_dataset):
            await self.queue.put((idx, self.dataset[idx]))

        # Create a shared tqdm progress bar
        self.pbar = tqdm(total=len_dataset, desc="Processing records", leave=True)

        # Create worker tasks
        tasks = []
        for _ in range(self.num_workers):
            task = asyncio.create_task(self.init_worker())
            tasks.append(task)

        # Add sentinel values to stop workers.
        for _ in range(self.num_workers):
            await self.queue.put(None)

        # Wait until all tasks are completed.
        await self.queue.join()
        self.pbar.close()

        # Wait for all workers to finish.
        await asyncio.gather(*tasks, return_exceptions=True)

    async def init_worker(self):
        """
        Worker function that processes records from the queue.
        It splits each document’s text into 4096-token chunks and calls the LLM for each chunk.
        """
        while True:
            try:
                task = await self.queue.get()
                if task is None:
                    self.queue.task_done()
                    break

                idx, item = task
            
                # Replace the text with the current chunk.
                message, res_json, parsed_data = \
                    await self.send_message(prompt_vars=item)

                if not parsed_data:
                    parsed_data = {}

                messages = {
                    "input": message,
                    "output": res_json
                }

                # Collate the results from all chunks.
                self.parser.collate_output(item, messages, parsed_data)

            except Exception as e:
                print(f"Failed to process record {idx}: {e}")

            # Update progress bar after processing a record.
            self.pbar.update(1)
            self.queue.task_done()

    async def send_message(self, prompt_vars, history=None):
        """
        Calls the LLM client with retry logic in case of exceptions.
        """
        retries = 4
        delay = 4
        for attempt in range(retries):
            try:
                # Generate the prompt using the template.
                message = self.prompt_template.format(prompt_vars)
                if message is None:
                    return None

                context = history or []
                context.append({"role": "user", "content": message})
                res_json = await self.client.chat_completions(
                    context=context, model=self.model, debug=self.debug)

                raw_output = res_json["choices"][0]["message"]["content"]
                parsed_data = self.parser.parse(raw_output)

                # Validate the parsed JSON data
                if not self.parser.validate_output(parsed_data):
                    raise ValueError("Validation failed.")

                return message, res_json, parsed_data
            
            except CensoredResponseException as e:
                raise e
            except Exception as e:
                print(
                    f"Error calling llm: {e}. Attempt {attempt + 1} of {retries}.")
                if attempt >= retries - 1:
                    raise e

                await asyncio.sleep(delay) # Backoff

    async def close(self):
        """
        Closes the ChatClient connection.
        """
        if self.client:
            await self.client.close()
            self.client = None
        else:
            print("ChatClient is already closed or not initialized.")

# Author: dhirenkumarsingh
"""LLM integration using OpenAI or Ollama."""

import logging
import httpx
from config import settings

logger = logging.getLogger(__name__)


class LLMHandler:
    """Handles LLM interactions for question answering."""

    def __init__(self):
        logger.info("Initializing LLMHandler")
        self.use_openai = settings.use_openai
        self.model = settings.openai_model

        if self.use_openai:
            logger.info(f"Using OpenAI LLM: {self.model}")
            from openai import OpenAI

            self.client = OpenAI(api_key=settings.openai_api_key)
        else:
            logger.info(
                f"Using Ollama LLM at: {settings.ollama_base_url}, model: {settings.ollama_model}"
            )
            self.client = None

    def generate_answer(self, question: str, context_chunks: list) -> str:
        """Generate an answer using the LLM with retrieved context."""
        logger.info(f"Generating answer for question: {question[:50]}...")
        logger.info(f"Number of context chunks: {len(context_chunks)}")

        try:
            if not context_chunks:
                logger.warning("No context chunks provided")
                return "No relevant documents found to answer your question."

            context = "\n\n".join(
                [
                    f"[Document {i + 1}]: {chunk[0]}"
                    for i, chunk in enumerate(context_chunks)
                ]
            )

            prompt = self._create_prompt(context, question)
            logger.debug(f"Created prompt with context length: {len(context)}")

            if self.use_openai:
                logger.info("Calling OpenAI Chat API")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that answers questions based on the provided context.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=500,
                )
                answer = response.choices[0].message.content
                logger.info(f"Generated answer from OpenAI, length: {len(answer)}")
                return answer
            else:
                logger.info("Calling Ollama API")
                answer = self._ollama_generate(prompt)
                logger.info(f"Generated answer from Ollama, length: {len(answer)}")
                return answer
        except Exception as e:
            logger.error(f"Error generating answer: {type(e).__name__}: {str(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return f"Error generating answer: {str(e)[:100]}"

    def _create_prompt(self, context: str, question: str) -> str:
        """Create the prompt for the LLM."""
        return f"""Context from documents:
{context}

Question: {question}

Please provide a clear and accurate answer based only on the context provided above.
If the context doesn't contain enough information to answer the question, say so.

Answer:"""

    def _ollama_generate(self, prompt: str) -> str:
        """Generate response using Ollama API."""
        logger.info("Calling Ollama generate API")
        logger.info(f"Ollama model: {settings.ollama_model}")
        logger.info(f"Prompt length: {len(prompt)} characters")

        try:
            with httpx.Client(timeout=300.0) as client:
                request_data = {
                    "model": settings.ollama_model,
                    "prompt": prompt[:2000],
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 500},
                }
                logger.info(f"Sending request to Ollama...")
                response = client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json=request_data,
                    timeout=300.0,
                )

                if response.status_code != 200:
                    logger.error(
                        f"Ollama API error: {response.status_code} - {response.text}"
                    )
                    raise Exception(f"Ollama API error: {response.status_code}")

                response.raise_for_status()
                result = response.json()["response"]
                logger.info(f"Received response: {result[:100]}...")
                return result
        except httpx.TimeoutException:
            logger.error("Ollama API timed out")
            return "The AI service is taking too long to respond. Please try again."
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(
                f"Ollama API error: {e.response.status_code} - {e.response.text[:200]}"
            )
        except Exception as e:
            logger.error(f"Error calling Ollama API: {type(e).__name__}: {e}")
            raise

import os
from openai import OpenAI

client = OpenAI()

question = os.getenv("QUESTION", "What is the capital of France?")

response = client.chat.completions.create(
    model="gpt-5.4-mini",
    messages=[{"role": "user",  "content": question}],
)

print(f"Question: {question}")
print(f"Answer: {response.choices[0].message.content}")
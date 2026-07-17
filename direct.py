from openai import OpenAI
from config.settings import get_settings

settings = get_settings()

client = OpenAI(api_key=settings.openai_api_key)

response = client.embeddings.create(
    model="text-embedding-3-small",
    input="hello world"
)

print(len(response.data[0].embedding))
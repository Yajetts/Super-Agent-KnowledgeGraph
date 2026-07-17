from config.settings import get_settings
from langchain_openai import OpenAIEmbeddings

settings = get_settings()

print("API key exists:", bool(settings.openai_api_key))
print("Model:", "text-embedding-3-small")

emb = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=settings.openai_api_key,
)

print("Created embeddings object")

result = emb.embed_query("hello world")

print("Success")
print(len(result))
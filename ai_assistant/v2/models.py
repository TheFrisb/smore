from django.conf import settings
from langchain_openai import ChatOpenAI

openai_o3_model = ChatOpenAI(
    model="gpt-4.1-2025-04-14", api_key=settings.OPENAI_API_KEY
)

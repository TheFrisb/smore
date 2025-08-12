from django.conf import settings
from langchain_openai import ChatOpenAI

openai_o3_model = ChatOpenAI(
    model="gpt-5-2025-08-07", api_key=settings.OPENAI_API_KEY
)

from django.conf import settings
from langchain_openai import ChatOpenAI

openai_o3_model = ChatOpenAI(model="gpt-4o-2024-08-06", api_key=settings.OPENAI_API_KEY)

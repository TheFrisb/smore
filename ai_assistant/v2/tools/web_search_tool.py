openai_web_search_tool = {
    "type": "web_search_preview",
    "name": "TavilySearch",
    "description": "A web search tool that provides sports-related news and updates.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant sports news and updates.",
            },
            "count": {
                "type": "integer",
                "default": 5,
                "description": "The number of search results to return.",
            },
        },
        "required": ["query"],
    },
}

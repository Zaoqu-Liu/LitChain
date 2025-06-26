from pydantic import BaseModel


class Plan(BaseModel):
    has_enough_context: bool
    thought: str
    title: str
    steps: list

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "has_enough_context": False,
                    "thought": (
                        "To understand the current market trends in AI, we need to gather comprehensive information."
                    ),
                    "title": "AI Market Research Plan",
                    "steps": [
                        {
                            "Research objectives": "Current AI Market Analysis",
                            "entities": ["AI", ""]
                        }
                    ],
                }
            ]
        }

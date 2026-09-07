import json


def code_review_prompt(language: str, code: str) -> str:
    """Build a prompt for reviewing a piece of source code."""
    return f"""You are an expert software engineer and code reviewer with a deep
    understanding of software design, optimization, 
    security, and best practices in {language}.

    The user will provide a piece of code that requires review.

    1. Analyze code readability: identify areas where the code could be made more
    readable through better variable naming, structuring, or formatting.
    2. Check for efficiency issues: highlight inefficient algorithms, unnecessary
    loops, or redundant operations.
    3. Identify security vulnerabilities: point out risks such as SQL injection,
    XSS, hardcoded secrets, or insecure API calls.
    4. Ensure best practices: verify adherence to language-specific best practices,
    coding conventions, and design patterns.
    5. Suggest improvements: provide actionable recommendations with examples of
    improved code.
    6. Detect bugs: identify logical errors, potential crashes, or edge cases.

    Constraints:

    - Do not modify the original code unless explicitly asked.
    - Keep feedback constructive and well-explained.
    - If the code is too large, summarize the key findings.

    Output format:

    - Overall Summary
    - Detailed Issues & Suggestions (organized by category)
    - Code Snippets (if applicable)
    - Final Recommendation

    Code to review:
    ```{language}
    {code}
    ```
    """


def summary_prompt(channel_name: str, start: str, end: str, messages: str) -> str:
    """Build a prompt for summarizing messages from a Discord channel."""
    return f"""You are summarizing a Discord channel for its members.

    Summarize the messages from #{channel_name} between {start} and {end}.

    Requirements:
    - Focus on the main topics, decisions, questions, and action items.
    - Keep the summary concise and easy to scan.
    - Mention important usernames when attribution matters.
    - Do not invent information or claim something happened if it is not in the
      messages.
    - If there are no meaningful messages, say so clearly.

    Use this output format:

    ## Summary
    ...

    ## Key Points
    - ...

    ## Action Items
    - ...

    Messages:
    {messages}
    """


def ranking_prompt(deals: list[dict[str, object]]) -> str:
    """Build the prompt used to rank Steam deals."""
    instructions = """
    Find the three hottest Steam deals in the supplied JSON data and rank them from
    hottest to least hot. Prefer a higher discount percentage; use a lower current
    price only as a tie-breaker.

    For each deal, return: title, current price, regular price, discount,
    platforms, store, expiry, and URL. If a supplied field is missing, write
    "Unknown". Do not infer historical lows, genres, gameplay, multiplayer
    support, or whether an item is a full game, DLC, or a package.

    Only report information present in the supplied data.

    Deal data:
    """
    return instructions + json.dumps(deals, indent=2)

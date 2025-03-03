# Moana: Multi-layered Memory Optimized Agent

Moana is a Multi-layered Memory Optimized Agent that leverages a subconscious long-term memory system to learn from interactions with users and recall information across conversations. Built on [LangGraph](https://github.com/langchain-ai/langgraph), Moana demonstrates how agents can maintain persistent knowledge and improve over time.

![Graph view in LangGraph studio UI](./static/studio_ui.png)

## Key Features

- **Subconscious Memory**: Stores and retrieves important information from past interactions
- **Cross-Conversation Recall**: Maintains context between separate conversations with users
- **ReAct Architecture**: Uses the proven Reasoning + Acting pattern for flexible problem-solving
- **Extensible Tool System**: Easily add new capabilities through custom tools

## How It Works

Moana's architecture includes:

1. **User Query Processing**: Analyzes user input to understand intent and context
2. **Memory Retrieval**: Searches subconscious memory for relevant past information
3. **Reasoning**: Combines current query with memory to determine appropriate actions
4. **Tool Execution**: Performs actions using available tools
5. **Memory Update**: Stores important new information in long-term memory
6. **Response Generation**: Provides thoughtful answers based on all available context

## Getting Started

Assuming you have already [installed LangGraph Studio](https://github.com/langchain-ai/langgraph-studio?tab=readme-ov-file#download), to set up:

1. Create a `.env` file.

```bash
cp .env.example .env
```

2. Define required API keys in your `.env` file.

The primary [search tool](./src/moana/tools.py) used is [Tavily](https://tavily.com/). Create an API key [here](https://app.tavily.com/sign-in).

### Setup Model

The defaults values for `model` are shown below:

```yaml
model: anthropic/claude-3-5-sonnet-20240620
```

Follow the instructions below to get set up, or pick one of the additional options.

#### Anthropic

To use Anthropic's chat models:

1. Sign up for an [Anthropic API key](https://console.anthropic.com/) if you haven't already.
2. Once you have your API key, add it to your `.env` file:

```
ANTHROPIC_API_KEY=your-api-key
```

#### OpenAI

To use OpenAI's chat models:

1. Sign up for an [OpenAI API key](https://platform.openai.com/signup).
2. Once you have your API key, add it to your `.env` file:

```
OPENAI_API_KEY=your-api-key
```

3. Install development dependencies and start the development server:

```bash
pip install --upgrade "langgraph-cli[inmem]"
pip install -e .
langgraph dev
```

4. Open the folder in LangGraph Studio!

## How to Customize

1. **Enhance Memory System**: Modify the subconscious memory implementation in `src/moana/memory/subconscious.py` to change how information is stored and retrieved.
2. **Add New Tools**: Extend the agent's capabilities by adding new tools in `src/moana/tools.py`.
3. **Select a Different Model**: We default to Anthropic's Claude 3.5 Sonnet. You can select a compatible chat model using `provider/model-name` via configuration.
4. **Customize the Prompt**: Update the system prompt in `src/moana/prompts.py` to adjust the agent's personality or behavior.

## Development

While iterating on your graph, you can edit past state and rerun your app from past states to debug specific nodes. Local changes will be automatically applied via hot reload. Try:

- Adding memory retrieval interrupts before tool execution
- Modifying how the agent stores and prioritizes information
- Implementing different memory persistence strategies
- Adding specialized tools for your specific use case

Follow up requests will be appended to the same thread. You can create an entirely new thread, clearing previous history, using the `+` button in the top right.

You can find the latest documentation on [LangGraph](https://github.com/langchain-ai/langgraph) here, including examples and other references. LangGraph Studio also integrates with [LangSmith](https://smith.langchain.com/) for more in-depth tracing and collaboration with teammates.

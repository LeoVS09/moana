from langgraph.checkpoint.memory import MemorySaver

# Stores short-term memory of current dialog
checkpointer = MemorySaver()

# TODO: Add Summarization logic to shorten long conversations
# Base it on model context window
# https://langchain-ai.github.io/langgraph/concepts/memory/#summarizing-past-conversations

# TODO: Remove old messages that summarized
# https://langchain-ai.github.io/langgraph/concepts/memory/#knowing-when-to-remove-messages
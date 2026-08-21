"""Any /v1 chat-completions server. Bearer token is optional."""

from kofte import OpenAICompatClient, Translator

llm = OpenAICompatClient(
    base_url="http://127.0.0.1:1234/v1",  # LM Studio, llama.cpp, vLLM, Ollama
    model="local-model",
)
engine = Translator(llm=llm)
print(
    engine.translate(
        "This is wrong. Fix it.",
        source="en+polish_direct",
        target="en+norwegian_jante",
    ).text
)

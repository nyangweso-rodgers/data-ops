# Open WebUI

## Table Of Contents

# Open WebUI

- **OpenWebUI** is a clean and privacy-first interface to interact with open-source **LLMs** like **Llama 3**, **Mistral**, or **Claude** locally on your machine. It supports features like tool calling, memory across chats, and custom personas — all without needing any OpenAI keys or cloud services.

- Features:
  1.  Fully self-hosted UI for local LLMs.
  2.  Supports plugin tools, persistent memory, and personas.
  3.  Works with Ollama or Llama.cpp backends.
  4.  No external dependencies or API costs.

# Setup

- The `docker-compose-open-webui.yml` files up the following containers:

  1. `ollama`: Runs local models on port `11434`, limited to use 6 CPU cores and 6GB of RAM, with models kept in memory for 5 minutes after use. (Feel free to adjust as needed).
  2. `open-webui`: Provides a web interface on port `8080` that connects to Ollama to create a ChatGPT-like interface.

- Both services store data in persistent volumes so nothing is lost when containers restart, and the WebUI waits for Ollama to start first since it depends on it to function.

# Downloading a Model for Ollama

- For this demo, we'll use `llama3.2:1b-instruct-q4_0`. This model is an excellent choice for basic coding assistance and is incredibly lightweight on system resources. Depending on your hardware, you can choose a larger or more specialized model.
- Since we're running Ollama in a container, we need to execute the download command (pull) within the container. To do this, type the following in your terminal:
  ```sh
    docker exec -it ollama bash
  ```
- Now that we're inside the container, let's `pullllama3.2:1b-instruct-q4_0` using the ollama CLI:
  ```sh
    ollama pull llama3.2:1b-instruct-q4_0
  ```
- Now let's quickly take it for a spin. While inside the container, run the following command: `ollama run llama3.2:1b-instruct-q4_0` then hit return. You should now be able to prompt the model:

# Using the Model with Open WebUI

# Resources and Further Reading

1. [github.com/open-webui/open-webui](https://github.com/open-webui/open-webui)
2. [docs.openwebui.com - Open WebUI](https://docs.openwebui.com/)
3. [Ollama Model Library](https://ollama.com/library?ref=gettingstarted.ai)
4. [Self-Hosted Private LLM using Ollama and Open WebUI](https://www.gettingstarted.ai/self-host-llm/?ref=dailydev)

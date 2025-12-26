# CES Terminology Guide

**Quick Reference for AI & Workstation Terms**

---

## AI & Machine Learning

| Term | Definition | Simple Explanation |
|------|------------|-------------------|
| **AI (Artificial Intelligence)** | Computer systems that perform tasks requiring human intelligence | Software that can think, learn, and respond |
| **LLM (Large Language Model)** | AI trained on vast text data to understand and generate language | The "brain" behind ChatGPT-like systems |
| **Inference** | Running a trained AI model to get predictions/responses | Asking the AI a question and getting an answer |
| **Token** | A piece of text (word or part of word) processed by AI | How AI reads and writes text, piece by piece |
| **Context Window** | How much text an AI can "remember" in one conversation | The AI's short-term memory size |
| **RAG (Retrieval Augmented Generation)** | AI that searches documents before answering | AI that looks up information before responding |
| **Fine-tuning** | Customizing an AI model for specific tasks | Teaching AI your company's specific knowledge |
| **Prompt** | The input/question given to an AI | What you type to ask the AI something |
| **Hallucination** | When AI generates incorrect or made-up information | AI confidently saying something wrong |

---

## Models

| Term | Definition | Simple Explanation |
|------|------------|-------------------|
| **Model** | The trained AI "brain" file | The AI software that does the thinking |
| **Parameters** | The learned values in a model (measured in billions) | More parameters = smarter but needs more power |
| **7B / 70B** | Model size in billions of parameters | 7 billion vs 70 billion—bigger = smarter |
| **Llama** | Meta's open-source AI model family | Free, powerful AI you can run locally |
| **Mistral** | French company's efficient AI models | Fast, efficient AI models |
| **DeepSeek** | Chinese AI research lab's models | Advanced reasoning AI models |
| **Ollama** | Software to run AI models locally | The engine that runs AI on your computer |
| **Quantization** | Compressing models to use less memory | Making AI smaller to fit on regular hardware |

### Model Status Definitions

| Status | Meaning | Visual Indicator |
|--------|---------|------------------|
| **Running** | Model is loaded in GPU memory and actively processing | 🟢 Green |
| **Ready** | Model is loaded in GPU memory and ready to process | 🟢 Green |
| **Idle** | Model is loaded but not currently processing | 🟡 Yellow/Amber |
| **Loading** | Model is being loaded into GPU memory | 🔵 Blue (animated) |
| **Stopped** | Model is available but not loaded | ⚪ Gray |
| **Error** | Model failed to load or encountered an issue | 🔴 Red |

**Simple explanations:**
- **Running** → "The AI is working right now"
- **Ready** → "The AI is loaded and ready to go"
- **Idle** → "The AI is ready but not loaded yet
- **Loading** → "The AI is warming up"

---

## Hardware & GPU

| Term | Definition | Simple Explanation |
|------|------------|-------------------|
| **GPU (Graphics Processing Unit)** | Processor designed for parallel computing | The chip that makes AI run fast |
| **VRAM (Video RAM)** | Memory on the GPU | How much AI "workspace" the GPU has |
| **CUDA** | NVIDIA's GPU programming platform | Software that lets programs use NVIDIA GPUs |
| **RTX** | NVIDIA's consumer/professional GPU line | The graphics card series for AI work |
| **Tensor Core** | Specialized GPU circuits for AI calculations | The AI-optimized part of modern GPUs |
| **TDP (Thermal Design Power)** | Power consumption in watts | How much electricity the hardware uses |
| **PCIe** | Connection between GPU and computer | The slot that connects GPU to motherboard |
| **NVLink** | High-speed connection between multiple GPUs | Bridge for using multiple GPUs together |

---

## Workstation Terms

| Term | Definition | Simple Explanation |
|------|------------|-------------------|
| **Workstation** | Professional-grade computer for demanding tasks | High-powered computer for serious work |
| **ECC Memory** | Error-correcting RAM for reliability | RAM that catches and fixes errors |
| **ISV Certification** | Software vendor validation | Guaranteed to work with specific software |
| **Form Factor** | Physical size/shape of computer | Tower, desktop, mobile, etc. |
| **RAID** | Multiple drives working together | Fast and/or safe storage configuration |
| **Xeon / Threadripper** | Professional-grade CPUs | Server/workstation processors |

---

## Software & Platform

| Term | Definition | Simple Explanation |
|------|------------|-------------------|
| **API (Application Programming Interface)** | Way for software to communicate | How apps talk to each other |
| **Gateway** | Central access point for services | The "front door" to all AI services |
| **Vector Database** | Database for AI-friendly search | Storage that understands meaning, not just words |
| **Qdrant** | A vector database system | Our semantic search engine |
| **Redis** | Fast in-memory data store | Super-fast temporary storage |
| **Docker** | Container platform for running apps | Technology that packages apps consistently |
| **Container** | Packaged application with dependencies | App in a box that runs anywhere |

---

## ABS-Specific Terms

| Term | Definition |
|------|------------|
| **ABS AI Fabric** | Our complete local AI platform |
| **Workstation Console** | CES showcase application |
| **Attract Mode** | Auto-activating visual demonstration |
| **CES Mode** | Trade show configuration with restricted controls |
| **Hub Gateway** | Our unified API service |
| **Asset Registry** | Catalog of available models and services |

---

## Metrics & Units

| Term | Meaning |
|------|---------|
| **GB (Gigabyte)** | 1 billion bytes of storage |
| **TFLOPS** | Trillion calculations per second |
| **tokens/sec** | AI processing speed |
| **ms (milliseconds)** | 1/1000th of a second |
| **Latency** | Response delay time |
| **Throughput** | Amount processed per time unit |

---

## AI Inference Metrics (Workstation Console)

These metrics appear on the Performance screen:

| Metric | Full Name | What It Measures | Good Value |
|--------|-----------|------------------|------------|
| **TOKENS/SEC** | Tokens per Second | How fast AI generates text | Higher = better (50+ is good) |
| **TTFT** | Time To First Token | Delay before AI starts responding | Lower = better (<500ms ideal) |
| **LAT** | Latency | Round-trip response time | Lower = better (<100ms ideal) |
| **CTX** | Context | Tokens currently in AI's memory | Varies by model (2K-128K) |

### Simple Explanations for Visitors

- **TOKENS/SEC** → "How fast the AI thinks and types its response"
- **TTFT** → "How quickly the AI starts answering after you ask"
- **LAT** → "The response time—how snappy the AI feels"
- **CTX** → "How much conversation history the AI can remember"

### What Affects These Metrics?

| Factor | Impact |
|--------|--------|
| Model size | Larger models = slower but smarter |
| GPU VRAM | More VRAM = can run larger models |
| GPU power | Faster GPU = higher tokens/sec |
| Prompt length | Longer prompts = higher TTFT |
| Context usage | More context = slower generation |

---

## Common Acronyms

| Acronym | Full Form |
|---------|-----------|
| AI | Artificial Intelligence |
| ML | Machine Learning |
| LLM | Large Language Model |
| GPU | Graphics Processing Unit |
| CPU | Central Processing Unit |
| RAM | Random Access Memory |
| VRAM | Video RAM |
| API | Application Programming Interface |
| RAG | Retrieval Augmented Generation |
| NLP | Natural Language Processing |
| WebGPU | Web Graphics Processing Unit API |

---

## Quick Comparisons

### Cloud AI vs Local AI
| Aspect | Cloud AI | Local AI (ABS) |
|--------|----------|----------------|
| Data Location | Their servers | Your machine |
| Privacy | Data leaves device | Data stays local |
| Cost | Per-token fees | One-time hardware |
| Internet | Required | Not required |
| Control | Limited | Complete |

### Model Sizes
| Size | Example | VRAM Needed | Capability |
|------|---------|-------------|------------|
| 7B | Llama 3 8B | ~8 GB | Good for most tasks |
| 13B | Llama 2 13B | ~16 GB | Better reasoning |
| 70B | Llama 3 70B | ~48 GB | Near-GPT-4 quality |
| 70B | DeepSeek R1 70B | ~48 GB | Advanced reasoning & coding |

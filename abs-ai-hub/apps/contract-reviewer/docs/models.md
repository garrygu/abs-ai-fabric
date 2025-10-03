Changes Made:
Core Gateway Registry (c:\ABS\core\gateway\registry.json):
    Added Legal-BERT: nlpaueb/legal-bert-base-uncased (768-dim embeddings)
    Added Llama3.2:7B: Larger LLM for better legal reasoning
    Updated contract-reviewer config: Now uses legal-bert + llama3.2:7b with 768-dim vectors

Contract Reviewer App (app.py):
    Updated embedding dimension: Changed from 384 to 768 for Legal-BERT compatibility
    Collection will recreate: Qdrant will automatically recreate with new vector size

Services Restarted:
    Core services: Restarted to pick up new model registry
    Contract reviewer: Rebuilt and restarted with new configuration
    Health check: ✅ Service is running properly

New Model Stack:
    Embeddings: Legal-BERT (768-dim) - specialized for legal text
    LLM: Llama3.2:7B - more capable than 3B for complex legal analysis
    Provider: Auto (will use Ollama for local inference)
The app should now provide more accurate legal analysis with domain-specific embeddings and a more powerful language model. 
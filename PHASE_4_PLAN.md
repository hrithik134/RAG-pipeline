# Phase 4: Retrieval and Generation (RAG) - Detailed Implementation Plan

## 📋 Overview

Phase 4 implements the core RAG (Retrieval-Augmented Generation) functionality that allows users to query the ingested documents and receive AI-generated answers with proper citations. This phase combines semantic search, keyword matching, and large language models to provide accurate, grounded responses.

## 🎯 Objectives

- **Primary Goal**: Enable users to ask questions about uploaded documents and receive accurate, cited answers
- **Key Features**: Hybrid retrieval, MMR selection, grounded responses, citation tracking
- **Quality Metrics**: Answer accuracy, response time, proper citations, context relevance

## 🏗️ Architecture Components

### 1. **Query Processing Pipeline**
```
User Query → Query Validation → Hybrid Retrieval → MMR Selection → LLM Generation → Response Formatting
```

### 2. **Core Services**
- **Retrieval Service**: Handles semantic + keyword search
- **LLM Service**: Manages OpenAI/Google AI interactions  
- **Query Service**: Orchestrates the entire RAG pipeline
- **Citation Service**: Tracks and formats source references

### 3. **Database Integration**
- Uses existing `Query` model for logging
- Leverages `Chunk` and `Document` models for retrieval
- Integrates with Pinecone vector store

## 📁 File Structure (New Components)

```
app/
├── routers/
│   └── query.py                    # Query API endpoints
├── services/
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract retrieval interface
│   │   ├── semantic_retriever.py   # Pinecone vector search
│   │   ├── keyword_retriever.py    # BM25 keyword search
│   │   └── hybrid_retriever.py     # Combined retrieval
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract LLM interface
│   │   ├── openai_provider.py      # OpenAI GPT integration
│   │   └── google_provider.py      # Google Gemini integration
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── mmr_selector.py         # Maximal Marginal Relevance
│   │   ├── citation_manager.py     # Citation extraction & formatting
│   │   └── query_service.py        # Main RAG orchestrator
│   └── query_service.py            # High-level query handler
├── schemas/
│   └── query.py                    # Query request/response models
└── utils/
    ├── prompts.py                  # System prompts and templates
    └── text_utils.py               # Text processing utilities
```

## 🔄 Detailed Process Flow

### Step 1: Query Reception & Validation
```python
# Input: User query + optional filters
{
    "query": "What are the benefits of cloud computing?",
    "upload_id": "uuid-optional",  # Filter by specific upload
    "top_k": 10,                   # Number of chunks to retrieve
    "mmr_lambda": 0.5,             # Diversity parameter
    "temperature": 0.1             # LLM creativity
}
```

**Process:**
1. Validate query length (min 3 chars, max 1000 chars)
2. Sanitize input (remove harmful content)
3. Check rate limits (if implemented)
4. Log query start time

### Step 2: Hybrid Retrieval

#### 2A: Semantic Retrieval (Pinecone)
```python
# Generate query embedding using same model as documents
query_embedding = embedding_service.embed_query(query_text)

# Search Pinecone with filters
semantic_results = pinecone_store.similarity_search(
    query_vector=query_embedding,
    top_k=top_k * 2,  # Get more for reranking
    namespace=upload_id,  # Optional filtering
    metadata_filter={"status": "indexed"}
)
```

#### 2B: Keyword Retrieval (BM25)
```python
# Use BM25 algorithm for keyword matching
from rank_bm25 import BM25Okapi

# Get all chunk texts (cached or from DB)
chunk_texts = get_chunk_texts(upload_id_filter)

# Create BM25 index
bm25 = BM25Okapi([text.split() for text in chunk_texts])

# Get keyword scores
keyword_scores = bm25.get_scores(query_text.split())
keyword_results = get_top_k_chunks(keyword_scores, top_k)
```

#### 2C: Hybrid Fusion
```python
# Combine semantic and keyword results using RRF (Reciprocal Rank Fusion)
def reciprocal_rank_fusion(semantic_results, keyword_results, k=60):
    combined_scores = {}
    
    # Add semantic scores
    for rank, chunk in enumerate(semantic_results):
        combined_scores[chunk.id] = 1 / (k + rank + 1)
    
    # Add keyword scores
    for rank, chunk in enumerate(keyword_results):
        if chunk.id in combined_scores:
            combined_scores[chunk.id] += 1 / (k + rank + 1)
        else:
            combined_scores[chunk.id] = 1 / (k + rank + 1)
    
    return sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
```

### Step 3: MMR (Maximal Marginal Relevance) Selection

**Purpose**: Reduce redundancy while maintaining relevance

```python
def mmr_selection(chunks, query_embedding, lambda_param=0.5, top_k=10):
    """
    Select diverse, relevant chunks using MMR algorithm
    
    Args:
        chunks: List of retrieved chunks with embeddings
        query_embedding: Query vector
        lambda_param: Balance between relevance (1.0) and diversity (0.0)
        top_k: Final number of chunks to select
    """
    selected = []
    remaining = chunks.copy()
    
    while len(selected) < top_k and remaining:
        if not selected:
            # First chunk: highest relevance
            best_chunk = max(remaining, key=lambda c: cosine_similarity(c.embedding, query_embedding))
        else:
            # Subsequent chunks: balance relevance and diversity
            best_score = -float('inf')
            best_chunk = None
            
            for chunk in remaining:
                # Relevance score
                relevance = cosine_similarity(chunk.embedding, query_embedding)
                
                # Diversity score (max similarity to already selected)
                max_similarity = max([
                    cosine_similarity(chunk.embedding, selected_chunk.embedding)
                    for selected_chunk in selected
                ])
                
                # MMR score
                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_similarity
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_chunk = chunk
        
        selected.append(best_chunk)
        remaining.remove(best_chunk)
    
    return selected
```

### Step 4: Context Preparation

```python
def prepare_context(selected_chunks, max_tokens=6000):
    """
    Prepare context for LLM with safety truncation
    """
    context_parts = []
    total_tokens = 0
    
    for i, chunk in enumerate(selected_chunks):
        # Format chunk with metadata
        chunk_text = f"""
[Source {i+1}]
Document: {chunk.document.filename}
Page: {chunk.page_number}
Content: {chunk.content}
---
"""
        
        # Count tokens (approximate)
        chunk_tokens = len(chunk_text.split()) * 1.3  # Rough token estimation
        
        if total_tokens + chunk_tokens > max_tokens:
            # Truncate if needed
            remaining_tokens = max_tokens - total_tokens
            words_to_keep = int(remaining_tokens / 1.3)
            truncated_content = ' '.join(chunk.content.split()[:words_to_keep]) + "..."
            
            chunk_text = f"""
[Source {i+1}]
Document: {chunk.document.filename}
Page: {chunk.page_number}
Content: {truncated_content}
---
"""
            context_parts.append(chunk_text)
            break
        
        context_parts.append(chunk_text)
        total_tokens += chunk_tokens
    
    return '\n'.join(context_parts)
```

### Step 5: LLM Generation

#### System Prompt Template
```python
SYSTEM_PROMPT = """
You are a helpful AI assistant that answers questions based on provided document excerpts.

INSTRUCTIONS:
1. Answer ONLY based on the provided context
2. If the context doesn't contain enough information, say "I don't have enough information to answer this question based on the provided documents."
3. Always cite your sources using [Source X] format
4. Be concise but comprehensive
5. If multiple sources support the same point, cite all relevant sources
6. Do not make up information not present in the context

CONTEXT:
{context}

USER QUESTION: {query}

Please provide a well-structured answer with proper citations.
"""
```

#### LLM Integration
```python
async def generate_answer(query, context, provider="openai"):
    """
    Generate answer using specified LLM provider
    """
    prompt = SYSTEM_PROMPT.format(context=context, query=query)
    
    if provider == "openai":
        response = await openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": prompt}
            ],
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens
        )
        return response.choices[0].message.content
    
    elif provider == "google":
        response = await gemini_client.generate_content(
            prompt,
            generation_config={
                "temperature": settings.google_temperature,
                "max_output_tokens": settings.google_max_tokens
            }
        )
        return response.text
```

### Step 6: Citation Extraction & Formatting

```python
def extract_citations(answer_text, chunks_used):
    """
    Extract and format citations from the generated answer
    """
    import re
    
    # Find all [Source X] references
    citation_pattern = r'\[Source (\d+)\]'
    citations_found = re.findall(citation_pattern, answer_text)
    
    formatted_citations = []
    
    for citation_num in set(citations_found):
        chunk_index = int(citation_num) - 1
        if chunk_index < len(chunks_used):
            chunk = chunks_used[chunk_index]
            
            # Extract relevant snippet (around 100 chars)
            snippet = extract_relevant_snippet(chunk.content, answer_text)
            
            formatted_citations.append({
                "document_id": str(chunk.document_id),
                "document_name": chunk.document.filename,
                "page": chunk.page_number,
                "chunk_id": str(chunk.id),
                "snippet": snippet,
                "relevance_score": chunk.relevance_score  # From retrieval
            })
    
    return formatted_citations

def extract_relevant_snippet(chunk_content, answer_text, snippet_length=150):
    """
    Extract the most relevant part of the chunk based on the answer
    """
    # Simple approach: find overlapping keywords
    answer_words = set(answer_text.lower().split())
    chunk_words = chunk_content.lower().split()
    
    # Find the sentence with most overlap
    sentences = chunk_content.split('.')
    best_sentence = ""
    max_overlap = 0
    
    for sentence in sentences:
        sentence_words = set(sentence.lower().split())
        overlap = len(answer_words.intersection(sentence_words))
        
        if overlap > max_overlap:
            max_overlap = overlap
            best_sentence = sentence.strip()
    
    # Truncate if too long
    if len(best_sentence) > snippet_length:
        return best_sentence[:snippet_length] + "..."
    
    return best_sentence
```

### Step 7: Response Formatting & Logging

```python
# Final response format
{
    "query_id": "uuid-generated",
    "answer": "Cloud computing offers several key benefits including...",
    "citations": [
        {
            "document_id": "doc-uuid",
            "document_name": "Cloud Computing Guide.pdf",
            "page": 3,
            "chunk_id": "chunk-uuid",
            "snippet": "The main advantages of cloud computing include cost reduction...",
            "relevance_score": 0.89
        }
    ],
    "used_chunks": [
        {
            "chunk_id": "chunk-uuid",
            "relevance_score": 0.89,
            "retrieval_method": "hybrid"
        }
    ],
    "metadata": {
        "retrieval_time_ms": 245,
        "generation_time_ms": 1200,
        "total_time_ms": 1445,
        "chunks_retrieved": 15,
        "chunks_used": 8,
        "llm_provider": "openai",
        "model": "gpt-4o-mini"
    }
}
```

## 🔧 Configuration Settings

Add to `app/config.py`:

```python
# RAG Configuration
rag_top_k: int = Field(default=10, alias="RAG_TOP_K")
rag_mmr_lambda: float = Field(default=0.5, alias="RAG_MMR_LAMBDA")
rag_max_context_tokens: int = Field(default=6000, alias="RAG_MAX_CONTEXT_TOKENS")
rag_temperature: float = Field(default=0.1, alias="RAG_TEMPERATURE")

# Retrieval Configuration
retrieval_method: Literal["semantic", "keyword", "hybrid"] = Field(
    default="hybrid", alias="RETRIEVAL_METHOD"
)
bm25_k1: float = Field(default=1.2, alias="BM25_K1")
bm25_b: float = Field(default=0.75, alias="BM25_B")
rrf_k: int = Field(default=60, alias="RRF_K")

# LLM Configuration
llm_max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")
llm_timeout_seconds: int = Field(default=30, alias="LLM_TIMEOUT_SECONDS")

# Google AI specific
google_temperature: float = Field(default=0.1, alias="GOOGLE_TEMPERATURE")
google_max_tokens: int = Field(default=2048, alias="GOOGLE_MAX_TOKENS")
```

## 📊 API Endpoints

### 1. Query Endpoint
```
POST /v1/query
Content-Type: application/json

{
    "query": "What are the main benefits of cloud computing?",
    "upload_id": "optional-uuid",
    "top_k": 10,
    "mmr_lambda": 0.5,
    "temperature": 0.1
}
```

### 2. Query History
```
GET /v1/queries?skip=0&limit=10&upload_id=optional
```

### 3. Query Details
```
GET /v1/queries/{query_id}
```

## 🧪 Testing Strategy

### Unit Tests
- Test each retrieval method independently
- Test MMR algorithm with known inputs
- Test citation extraction logic
- Test prompt formatting

### Integration Tests
- End-to-end query processing
- Test with different document types
- Test error handling (no results, API failures)
- Performance testing with large document sets

### Quality Tests
- Answer accuracy evaluation
- Citation correctness verification
- Response time benchmarks
- Hallucination detection

## 📈 Performance Considerations

### Optimization Strategies
1. **Caching**: Cache BM25 indices and frequent queries
2. **Async Processing**: Use async/await for all I/O operations
3. **Connection Pooling**: Reuse LLM API connections
4. **Batch Processing**: Process multiple queries efficiently

### Monitoring Metrics
- Query response time (target: <3 seconds)
- Retrieval accuracy (precision@k)
- Citation accuracy rate
- LLM API usage and costs
- Error rates by component

## 🚀 Implementation Priority

### Phase 4.1: Core RAG (Week 1)
- [ ] Basic semantic retrieval
- [ ] Simple LLM integration
- [ ] Basic citation extraction
- [ ] Query endpoint

### Phase 4.2: Hybrid Retrieval (Week 2)
- [ ] BM25 keyword search
- [ ] Hybrid fusion (RRF)
- [ ] MMR selection
- [ ] Advanced citation formatting

### Phase 4.3: Optimization (Week 3)
- [ ] Performance optimization
- [ ] Caching implementation
- [ ] Error handling
- [ ] Comprehensive testing

### Phase 4.4: Advanced Features (Week 4)
- [ ] Query history and analytics
- [ ] Advanced filtering options
- [ ] Multi-language support
- [ ] Query suggestions

## 🔒 Security & Safety

### Input Validation
- Query length limits
- Content filtering for harmful queries
- Rate limiting per user/IP

### Output Safety
- Hallucination detection
- Content moderation
- Source verification

### Privacy
- Query logging controls
- Data retention policies
- User consent management

## 📋 Success Criteria

### Functional Requirements
- ✅ Users can query uploaded documents
- ✅ Responses include proper citations
- ✅ Hybrid retrieval works effectively
- ✅ Multiple LLM providers supported

### Quality Requirements
- Response time < 3 seconds (95th percentile)
- Citation accuracy > 90%
- User satisfaction score > 4.0/5.0
- System uptime > 99.5%

### Technical Requirements
- Scalable to 1000+ concurrent queries
- Support for 10,000+ documents
- Comprehensive error handling
- Full test coverage (>90%)

---

## 📚 Key Concepts Explained

### What is RAG (Retrieval-Augmented Generation)?
RAG is a technique that combines information retrieval with text generation. Instead of relying solely on the LLM's training data, RAG first retrieves relevant information from a knowledge base (your documents) and then uses that information to generate accurate, grounded answers.

### What is Hybrid Retrieval?
Hybrid retrieval combines two complementary search methods:
- **Semantic Search**: Understands meaning and context (e.g., "car" and "automobile" are similar)
- **Keyword Search**: Matches exact terms (e.g., finds specific product names or codes)

By combining both, we get the best of both worlds: understanding context while not missing exact matches.

### What is MMR (Maximal Marginal Relevance)?
MMR is an algorithm that selects diverse results. Without MMR, you might get 10 chunks that all say the same thing. With MMR, you get varied perspectives and information, making the answer more comprehensive.

### What are Citations?
Citations are references to the source documents where the information came from. They allow users to:
- Verify the AI's answer
- Read more context
- Trust the response more
- Understand which documents contain relevant information

### What is BM25?
BM25 is a ranking algorithm for keyword search. It's better than simple keyword matching because it considers:
- How rare a word is (rare words are more important)
- How often a word appears in a document
- Document length (longer documents aren't unfairly favored)

### What is Reciprocal Rank Fusion (RRF)?
RRF is a method to combine results from different search methods. Instead of just averaging scores (which can be misleading), RRF uses the rank position of each result to create a fair combined ranking.

---

This completes the detailed Phase 4 implementation plan. The system will provide a robust, accurate, and scalable RAG solution that builds upon the solid foundation established in Phases 0-3.


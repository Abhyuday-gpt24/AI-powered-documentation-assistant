from pathlib import Path
import re
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
import hashlib
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor
from langchain_chroma import Chroma
from langchain_core.documents import Document
import time
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


def collect_files(dir_path: str)-> list[str]:
    """Collects all file paths into a list"""
    doc_path = Path(dir_path).resolve()
    if not doc_path.exists():
        raise FileNotFoundError(f"Path does not exist: {doc_path}")
    
    file_paths = [str(f) for f in sorted(doc_path.rglob("*.md"))]
    return file_paths




# Clean Markdown - Removing HTML Tags
def clean_markdown(text: str) -> str:
    """Remove HTML tags, badges, and style blocks from markdown."""

    # Remove <style>...</style> blocks
    text = re.sub(r"<style[\s\S]*?</style>", "", text)

    # Remove HTML tags but keep their text content
    # <p align="center">FastAPI is great</p> → FastAPI is great
    text = re.sub(r"<[^>]+>", "", text)

    # Remove image markdown that are just badges
    # ![Test](https://img.shields.io/...) → removed
    text = re.sub(r"!\[.*?\]\(https://img\.shields\.io/.*?\)", "", text)

    # Remove excessive blank lines left behind
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()




# Data parsing
def parse_file(filepath: str) -> dict:
    """Read a markdown file and return its content with metadata"""
    path = Path(filepath)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Cleaning Markdown to remove HTML tags
    content = clean_markdown(content)
    
    return {
        "source": path.name,
        "path": str(path),
        "content": content,
    }





# Chunking
def chunk_file(filepath: str) -> list[dict]:
    """Parse + Chunk a single Markdown File"""

    # Parsing 
    doc = parse_file(filepath)

    if not doc["content"].strip():
        return []
    
    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
        ],
        strip_headers=False,
        
    )
    md_sections = md_splitter.split_text(doc["content"])

    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 100,
        separators=[
            "\n```\n",
            "\n\n",
            "\n",
            " ",
        ],
    )

    final_chunks = char_splitter.split_documents(md_sections)


    # Build Output
    results = []
    for i, chunk in enumerate(final_chunks):
        body = chunk.page_content.strip()
        if not body:
            continue

        headers = chunk.metadata
        heading_trail = " > ".join(
            headers[k] for k in ("h1", "h2", "h3") if k in headers
        )

        text = f"{heading_trail}\n\n{body}" if heading_trail else body

        raw_id = f"{doc['source']}::{i}::{text[:100]}"
        chunk_id = hashlib.md5(raw_id.encode()).hexdigest()
        results.append({
            "chunk_id": chunk_id,
            "text": text,
            "source": doc["source"],
            "heading_trail": heading_trail
        })

    return results





# Chunking in batches 
def chunk_batchs_in_multiprocess(file_paths: list[str], max_workers:int = None) -> list[dict]:
    """
    Chunk multiple files in parallel using ProcessPoolExecutor.
 
    Args:
        file_paths:  List of markdown file paths.
        max_workers: Number of parallel processes (defaults to CPU count).
 
    Returns:
        List of chunk dicts from all files in this batch.
    """

    if max_workers is None :
        max_workers = min(os.cpu_count(), len(file_paths))

    all_chunks = []

    with ThreadPoolExecutor(max_workers) as executor:
        results = executor.map(chunk_file, file_paths)
        for file_chunks in results:
            all_chunks.extend(file_chunks)

    return all_chunks





# Store chunks in ChromaDB
def store_chunks(chunks: list[dict], vector_store: Chroma, project: str):
    """Convert chunk dicts to LangChain Documents and add to chromaDB"""
    documents = []
    ids = []

    for chunk in chunks:
        documents.append(
            Document(
                page_content=chunk["text"],
                metadata = {
                    "source": chunk["source"],
                    "project": project,
                    "heading_trail": chunk["heading_trail"],
                },
            )
        )
        ids.append(chunk["chunk_id"])

    vector_store.add_documents(documents, ids = ids)






# Clean old chunks before re-ingesting
def clean_project(vector_store: Chroma, project: str):
    """
    Remove all existing chunks for a project before re-ingesting.
    This prevents stale/orphaned chunks when files are edited
    and chunk boundaries shift.
 
    Only deletes chunks for the given project — other projects
    in the same ChromaDB collection are untouched.
    """
    try:
        vector_store._collection.delete(where={"project": project})
        print(f"[Clean] Removed old chunks for project: {project}")
    except Exception:
        # First run — nothing to delete
        print(f"[Clean] No existing data for project: {project}")



      
# Full Pipeline
def run_pipeline(
    docs_path:str, 
    project:str, 
    batch_size:int = 20, 
    max_workers:int = None, 
    persist_dir: str = "vectorstore", 
    embedding_model:str = "text-embedding-3-small", 
    fresh:bool = True
):
    """
    Complete ingestion pipeline.
 
    1. Cleans old chunks for this project (if fresh=True)
    2. Collects all .md files
    3. Processes them in batches
    4. Each batch is chunked in parallel (multiprocessing)
    5. Chunks are embedded + stored in ChromaDB
 
    Args:
        docs_path:        Path to documentation directory.
        project:          Project name for metadata filtering.
        batch_size:       Files per batch (controls memory).
        max_workers:      Parallel processes per batch (controls speed).
        persist_dir:      Where ChromaDB stores data on disk.
        embedding_model:  OpenAI embedding model name.
        fresh:            If True, remove old chunks before ingesting.
    """

    start = time.time()

    # Collect
    file_paths = collect_files(docs_path)
    if not file_paths:
        print("No Files Found!")
        return
    
    # Vector Store
    embeddings = OpenAIEmbeddings(model = embedding_model)
    vector_store = Chroma(
        collection_name = project,
        embedding_function=embeddings,
        persist_directory=persist_dir,
        collection_metadata={"hnsw:space": "cosine"}
    )

    # Clean old data when project update 
    if fresh:
        clean_project(vector_store, project)

    # Process in batches
    total_files = len(file_paths)
    total_chunks = 0
    num_batches = (total_files + batch_size - 1) // batch_size

    # For process updates logs
    print(f"\n[Pipeline] {total_files} files, {num_batches} batches of {batch_size}")
    print(f"[Pipeline] Workers: {max_workers or os.cpu_count()}")
    print(f"[Pipeline] Embedding: {embedding_model}\n")


    # Looping through batches
    for i in range(0, total_files, batch_size):            
        num_of_batchs = i // batch_size + 1                 
        batch_file_paths = file_paths[i : i + batch_size]
 
        # Chunk in parallel (multiprocessing)
        chunks = chunk_batchs_in_multiprocess(batch_file_paths, max_workers)
 
        # Store in vector DB
        if chunks:
            store_chunks(chunks, vector_store, project)
            total_chunks += len(chunks)
 
        # Free memory before next batch
        del chunks

        # For process updates logs
        files_done = min(i + batch_size, total_files)
        print(f"  Batch {num_of_batchs}/{num_batches}: "
              f"{files_done}/{total_files} files, "
              f"{total_chunks} chunks so far")
 
    elapsed = time.time() - start
 
    # Summary Status
    print(f"\n{'='*50}")
    print(f"  Project:     {project}")
    print(f"  Files:       {total_files}")
    print(f"  Chunks:      {total_chunks}")
    print(f"  Embedding:   {embedding_model}")
    print(f"  Time:        {elapsed:.1f}s")
    print(f"  Stored in:   {persist_dir}")
    print(f"{'='*50}\n")
 
    return vector_store
 



# Let's Run data ingestion Pipeline
dir_path = Path("data/fastapi/docs").resolve()
print("path : =================" , dir_path)
run_pipeline(docs_path=dir_path, project="fastapi",max_workers=8, fresh=True)



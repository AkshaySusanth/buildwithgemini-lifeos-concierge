import sys
import vertexai
from vertexai.preview import rag
from vertexai.preview.rag.utils import resources as rr

PROJECT_ID = "qwiklabs-gcp-03-a9da68b5f222"
LOCATION = "us-central1"
GCS_PATH = "gs://lifeos-concierge-assets-qwiklabs-gcp-03-a9da68b5f222/rag/pg49513.txt"

PARSING_PROMPT = (
    "Extract the individual useful facts, remedies, and descriptions described in this text. "
    "Ignore and omit all metadata, license boilerplate, and headers. "
    "Output clean, self-contained prose."
)

vertexai.init(project=PROJECT_ID, location=LOCATION)

print("Updating RAG engine config to serverless mode...")
cfg = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragEngineConfig"
rag.update_rag_engine_config(
    rag_engine_config=rag.RagEngineConfig(
        name=cfg,
        rag_managed_db_config=rag.RagManagedDbConfig(mode=rr.Serverless()),
    ),
)

print("Creating RAG corpus...")
corpus = rag.create_corpus(
    display_name="lifeos-gutenberg-herbal",
    embedding_model_config=rag.EmbeddingModelConfig(
        publisher_model="publishers/google/models/text-embedding-005"
    ),
)
print(f"CORPUS_NAME={corpus.name}")

print(f"Importing files from {GCS_PATH}...")
resp = rag.import_files(
    corpus_name=corpus.name,
    paths=[GCS_PATH],
    transformation_config=rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100)
    ),
    llm_parser=rag.LlmParserConfig(
        model_name="gemini-2.5-flash",
        custom_parsing_prompt=PARSING_PROMPT,
    ),
)
print(f"Import finished. Imported files count: {resp.imported_rag_files_count}")

"""
ChromaDB vector store operations.

Two collections:
  - meeting_{meeting_id} : segments for one specific meeting
  - all_meetings          : all segments across all meetings (with meeting metadata)

Embeddings: ChromaDB default (all-MiniLM-L6-v2 via sentence-transformers).
No API key required — model is downloaded on first use (~90 MB).
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

_client = None
_embedding_fn = None


def _get_embedding_fn():
    """
    Chroma defaults to ONNX MiniLM with all available EPs; on Apple Silicon ONNX
    may pick CoreML and crash during dynamic-seq embedding. Force CPU EP only.
    """
    global _embedding_fn
    if _embedding_fn is None:
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

        _embedding_fn = ONNXMiniLM_L6_V2(preferred_providers=["CPUExecutionProvider"])
    return _embedding_fn


def _get_client():
    global _client
    if _client is None:
        try:
            import chromadb
            from chromadb.config import Settings

            _client = chromadb.PersistentClient(
                path=settings.CHROMA_DB_PATH,
                settings=Settings(anonymized_telemetry=False),
            )
        except Exception as e:
            logger.error(f'ChromaDB init failed: {e}')
            raise
    return _client


def index_meeting(
    meeting_id: str,
    segments: list,
    raw_text: str,
    title: str,
    owner_id: int | None = None,
):
    """
    Index meeting transcript segments into:
    1. Per-meeting collection: meeting_{meeting_id}
    2. Global collection: all_meetings
    """
    if not segments:
        logger.warning(f'No segments to index for meeting {meeting_id}')
        return

    try:
        client = _get_client()
        ef = _get_embedding_fn()

        per_col = client.get_or_create_collection(
            name=f'meeting_{meeting_id}', embedding_function=ef
        )
        all_col = client.get_or_create_collection(name='all_meetings', embedding_function=ef)

        documents, metadatas, ids = [], [], []
        all_docs, all_metas, all_ids = [], [], []

        for seg in segments:
            text = seg.get('text', '').strip()
            if not text:
                continue

            meta = {
                'id': seg['id'],
                'speaker': seg.get('speaker', ''),
                'time': seg.get('time', ''),
                'meeting_id': meeting_id,
                'meeting_title': title,
                'owner_id': str(owner_id) if owner_id is not None else '',
            }

            documents.append(text)
            metadatas.append(meta)
            ids.append(str(seg['id']))

            all_docs.append(text)
            all_metas.append(meta)
            all_ids.append(f'{meeting_id}_{seg["id"]}')

        if documents:
            per_col.upsert(documents=documents, metadatas=metadatas, ids=ids)

        if all_docs:
            all_col.upsert(documents=all_docs, metadatas=all_metas, ids=all_ids)

        logger.info(f'Indexed {len(documents)} segments for meeting {meeting_id}')

    except Exception as e:
        logger.exception(f'Vector indexing failed for meeting {meeting_id}: {e}')
        # Never crash the pipeline — chat falls back to full context string


def query_meeting(meeting_id: str, query: str, n_results: int = 5) -> list:
    """Query segments from a specific meeting. Returns [] on failure."""
    try:
        client = _get_client()
        col = client.get_collection(
            name=f'meeting_{meeting_id}', embedding_function=_get_embedding_fn()
        )
        results = col.query(query_texts=[query], n_results=min(n_results, col.count()))

        return [
            {
                'text':    doc,
                'speaker': results['metadatas'][0][i].get('speaker', ''),
                'time':    results['metadatas'][0][i].get('time', ''),
            }
            for i, doc in enumerate(results['documents'][0])
        ]
    except Exception as e:
        logger.warning(f'Vector query failed for meeting {meeting_id}: {e}')
        return []


def query_all_meetings(query: str, n_results: int = 8, owner_id: int | None = None) -> list:
    """Query segments across indexed meetings, optionally scoped to one user (metadata owner_id)."""
    try:
        client = _get_client()
        col = client.get_collection(
            name='all_meetings', embedding_function=_get_embedding_fn()
        )
        count = col.count()
        if count == 0:
            return []
        k = min(n_results, count)
        q_kwargs = {'query_texts': [query], 'n_results': k}
        if owner_id is not None:
            q_kwargs['where'] = {'owner_id': str(owner_id)}
        results = col.query(**q_kwargs)

        return [
            {
                'text':          doc,
                'speaker':       results['metadatas'][0][i].get('speaker', ''),
                'time':          results['metadatas'][0][i].get('time', ''),
                'meeting_id':    results['metadatas'][0][i].get('meeting_id', ''),
                'meeting_title': results['metadatas'][0][i].get('meeting_title', ''),
            }
            for i, doc in enumerate(results['documents'][0])
        ]
    except Exception as e:
        logger.warning(f'Global vector query failed: {e}')
        return []

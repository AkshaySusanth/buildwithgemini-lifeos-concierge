# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import urllib.request
import uuid
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google import genai
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore, storage
from google.genai import types

from app.a2ui_utils import a2ui_callback

# Hardcode GCP project ID string for Firestore client and Cloud Storage bucket
PROJECT_ID = "qwiklabs-gcp-03-a9da68b5f222"
BUCKET_NAME = "lifeos-concierge-assets-qwiklabs-gcp-03-a9da68b5f222"
ENGINE_RESOURCE_NAME = "projects/101933654881/locations/us-east1/reasoningEngines/2922680027512307712"
db = firestore.Client(project=PROJECT_ID)
COLLECTION_NAME = "subscriptions"

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=ENGINE_RESOURCE_NAME
)

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are LifeOS Concierge, a personal admin and life maintenance assistant. "
        "You manage subscriptions, recurring bills, and home/vehicle maintenance schedules stored in Firestore. "
        "You also fetch upcoming public holidays for scheduling life admin tasks, search the grounded reference corpus for remedies and guides, generate visual status badges/diagrams using generate_life_admin_item_image, and remember user preferences across sessions. "
        "You have Python code execution enabled via an Agent Engine Sandbox. Whenever you need to perform calculations, data analysis, or code execution, write executable Python code inside ```python ``` blocks. "
        "Use list_subscriptions, add_subscription, update_subscription_status, calculate_subscription_metrics, get_upcoming_holidays, consult_life_admin_herbal_guide, and generate_life_admin_item_image."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


# WRITE: after each turn, send the session to Memory Bank for extraction.
async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        query: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


def list_subscriptions(category: str = "") -> str:
    """Retrieves subscriptions and maintenance tasks from the Firestore database.

    Args:
        category: Optional category filter (e.g. 'Entertainment', 'Automotive', 'Home Maintenance').
                  Leave empty to return all items.

    Returns:
        A formatted JSON string listing the requested subscriptions and tasks.
    """
    docs = db.collection(COLLECTION_NAME).stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        if not category or data.get("category", "").lower() == category.lower():
            results.append(data)
    return json.dumps(results, indent=2)


def add_subscription(
    name: str,
    category: str,
    cost: float,
    frequency: str,
    next_due_date: str,
    notes: str = "",
) -> str:
    """Adds a new subscription or maintenance item to the Firestore database.

    Args:
        name: Name of the subscription or task (e.g. 'Netflix', 'Oil Change').
        category: Category (e.g. 'Entertainment', 'Automotive', 'Home Maintenance').
        cost: Monthly or per-occurrence cost in USD.
        frequency: Billing frequency or interval (e.g. 'Monthly', 'Every 6 Months').
        next_due_date: Due date string in YYYY-MM-DD format.
        notes: Optional additional details or notes.

    Returns:
        A confirmation message with the generated document ID.
    """
    doc_ref = db.collection(COLLECTION_NAME).document()
    item = {
        "name": name,
        "category": category,
        "cost": cost,
        "frequency": frequency,
        "next_due_date": next_due_date,
        "status": "active",
        "notes": notes,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    doc_ref.set(item)
    return f"Successfully added subscription '{name}' with ID: {doc_ref.id}"


def update_subscription_status(doc_id: str, status: str) -> str:
    """Updates the status of an existing subscription or maintenance item in Firestore.

    Args:
        doc_id: The document ID of the item to update (e.g. 'sub_001').
        status: The new status (e.g. 'active', 'paused', 'cancelled', 'completed').

    Returns:
        A confirmation message indicating the status update.
    """
    doc_ref = db.collection(COLLECTION_NAME).document(doc_id)
    doc = doc_ref.get()
    if not doc.exists:
        return f"Error: Document with ID '{doc_id}' not found."
    doc_ref.update({"status": status})
    return f"Successfully updated status of '{doc_id}' to '{status}'."


def calculate_subscription_metrics() -> str:
    """Calculates summary financial and volume metrics for active subscriptions from Firestore.

    Returns:
        A JSON string containing active count, total monthly recurring cost, total annual cost,
        and cost breakdown by category.
    """
    docs = db.collection(COLLECTION_NAME).stream()
    total_monthly = 0.0
    active_count = 0
    categories: dict[str, float] = {}

    for doc in docs:
        data = doc.to_dict()
        if data.get("status") == "active":
            active_count += 1
            cost = float(data.get("cost", 0.0))
            freq = str(data.get("frequency", "")).lower()
            monthly_cost = cost if "monthly" in freq else (cost / 12.0 if "year" in freq or "annual" in freq else cost)
            total_monthly += monthly_cost
            cat = str(data.get("category", "uncategorized"))
            categories[cat] = categories.get(cat, 0.0) + monthly_cost

    summary = {
        "active_subscriptions_count": active_count,
        "total_monthly_cost_usd": round(total_monthly, 2),
        "total_annual_cost_usd": round(total_monthly * 12, 2),
        "monthly_cost_by_category": {k: round(v, 2) for k, v in categories.items()},
    }
    return json.dumps(summary, indent=2)


def get_upcoming_holidays(country_code: str = "US", year: int = 2026) -> str:
    """Fetches public holidays for life admin and home maintenance scheduling from the Nager.Date Public API.

    Args:
        country_code: 2-letter ISO country code (e.g. 'US', 'CA', 'GB'). Defaults to 'US'.
        year: Year for holiday lookup (e.g. 2026). Defaults to 2026.

    Returns:
        A JSON string containing the list of public holidays with dates and names.
    """
    url = f"https://date.nager.at/api/v3/publicholidays/{year}/{country_code.upper()}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "LifeOS-Concierge/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            formatted = [
                {
                    "date": h.get("date"),
                    "name": h.get("name"),
                    "localName": h.get("localName"),
                }
                for h in data
            ]
            return json.dumps(formatted, indent=2)
    except Exception as e:
        return f"Error fetching public holidays: {e}"


RAG_CORPUS_NAME = "projects/101933654881/locations/us-central1/ragCorpora/4776586374314721280"


def consult_life_admin_herbal_guide(query: str) -> str:
    """Searches the grounded reference corpus (The Complete Herbal) for natural remedies, plant uses, and traditional life maintenance guides.

    Args:
        query: What to look up (e.g. an ailment, plant name, or remedy).

    Returns:
        The matched passages from the reference corpus.
    """
    import vertexai
    from vertexai.preview import rag

    try:
        vertexai.init(project=PROJECT_ID, location="us-central1")
        resp = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS_NAME)],
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=5),
        )
        contexts = getattr(resp.contexts, "contexts", [])
        passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
        return "\n\n---\n\n".join(passages) or "No relevant passages found in the corpus."
    except Exception as e:
        return f"Retrieval error: {e}"


async def generate_life_admin_item_image(prompt: str, tool_context: ToolContext) -> str:
    """Generates an image visual asset or badge for a life admin item (e.g. maintenance status badge, routine diagram, subscription icon) using gemini-3.1-flash-lite-image in the global region.

    Saves the generated image to session artifacts and uploads it to public Cloud Storage, returning the public HTTPS URL.

    Args:
        prompt: Description of the life admin image or visual asset to generate.
        tool_context: ADK ToolContext automatically injected by the framework.

    Returns:
        The public HTTPS URL of the uploaded image (https://storage.googleapis.com/<bucket>/<object>).
    """
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )

    image_bytes = None
    mime_type = "image/jpeg"

    for candidate in response.candidates:
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/jpeg"
                    break

    if not image_bytes:
        return "Error: No image content was returned by the generation model."

    ext = "png" if "png" in mime_type.lower() else "jpg"
    filename = f"generated_item_{uuid.uuid4().hex[:8]}.{ext}"

    # 1. Save artifact to ToolContext for Playground Artifacts panel
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    await tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload image bytes to public GCS bucket (without writing to local disk)
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    object_name = f"generated_assets/{filename}"
    blob = bucket.blob(object_name)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{object_name}"
    return public_url


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=code_executor,
    instruction=instruction,
    tools=[
        get_weather,
        get_current_time,
        list_subscriptions,
        add_subscription,
        update_subscription_status,
        calculate_subscription_metrics,
        get_upcoming_holidays,
        consult_life_admin_herbal_guide,
        generate_life_admin_item_image,
        PreloadMemoryTool(),
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)


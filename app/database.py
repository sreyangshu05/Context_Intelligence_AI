from supabase import create_client, Client
from app.config import settings


def get_supabase_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_anon_key)


async def increment_metric(metric_name: str):
    supabase = get_supabase_client()

    result = supabase.table("metrics").select("metric_value").eq("metric_name", metric_name).maybeSingle().execute()

    if result.data:
        current_value = result.data["metric_value"]
        supabase.table("metrics").update({"metric_value": current_value + 1}).eq("metric_name", metric_name).execute()
    else:
        supabase.table("metrics").insert({"metric_name": metric_name, "metric_value": 1}).execute()


async def get_metrics():
    supabase = get_supabase_client()
    result = supabase.table("metrics").select("*").execute()

    metrics_dict = {}
    for row in result.data:
        metrics_dict[row["metric_name"]] = row["metric_value"]

    return {
        "documents_ingested": metrics_dict.get("documents_ingested", 0),
        "extractions_performed": metrics_dict.get("extractions_performed", 0),
        "queries_answered": metrics_dict.get("queries_answered", 0),
        "audits_run": metrics_dict.get("audits_run", 0)
    }

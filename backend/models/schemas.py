"""Pydantic models matching the existing JSON output format."""

from typing import Optional, Union
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    providers: Optional[list[str]] = None  # None = all configured
    analyze: bool = False
    enhanced_analysis: bool = False
    request_sources: bool = False
    web_search: Optional[bool] = None  # None = use .env default per provider
    deep_research: Optional[bool] = None  # None = use .env default per provider


class SearchResult(BaseModel):
    title: str
    link: str
    snippet: str


class AnalysisData(BaseModel):
    timestamp: Optional[str] = None
    query: Optional[str] = None
    provider: Optional[str] = None
    companies_mentioned: list[str] = []
    mention_reasons: dict = {}
    authority_signals: list[str] = []
    key_features: list[str] = []
    sources_cited: list[str] = []
    ranking_factors: Union[str, list[str]] = ""
    sentiment: str = "neutral"
    optimization_insights: Union[str, list[str]] = ""
    extracted_urls: list[str] = []
    url_statistics: dict = {}
    domain_statistics: Optional[dict] = None
    domain_classifications: Optional[list[dict]] = None
    ugc_surge_alert: Optional[dict] = None
    negative_signals: Optional[dict] = None
    negative_score: Optional[int] = None
    entity_sentiment: Optional[dict] = None
    accuracy_issues: Optional[list] = None
    corrections_needed: Optional[list] = None
    competitor_mentions: Optional[list[dict]] = None


class ProviderResult(BaseModel):
    provider: str
    response: Optional[Union[str, list[dict]]] = None
    model: Optional[str] = None
    success: bool = False
    error: Optional[str] = None
    analysis: Optional[dict] = None


class QueryResult(BaseModel):
    query: str
    timestamp: str
    date: str
    time: str
    results: list[ProviderResult]


class ProviderInfo(BaseModel):
    name: str
    configured: bool
    model: Optional[str] = None


class ResultListItem(BaseModel):
    filename: str
    query: str
    timestamp: Optional[str] = None
    is_batch: bool = False
    provider_count: int = 0
    has_analysis: bool = False


class PaginatedResults(BaseModel):
    items: list[ResultListItem]
    total: int
    page: int
    limit: int

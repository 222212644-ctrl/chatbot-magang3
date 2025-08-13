export type SearchRequest = {
  query?: string;
  message?: string;
};

export type SearchResult = {
  url: string;
  title: string;
  snippet: string;
  score?: number;
  source?: string;
};

export type SearchResponse = {
  query: string;
  results: SearchResult[];
};
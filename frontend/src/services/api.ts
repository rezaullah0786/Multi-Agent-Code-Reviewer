import type {
  CodeSearchResponse,
  GitHubPRReviewEventResponse,
  IndexStatusResponse,
  MetricsSummary,
  ReviewRequest,
  ReviewResponse,
  ReviewSummary,
  SystemHealth,
} from '../types/review';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      } else if (errJson.message) {
        errorDetail = errJson.message;
      }
    } catch {
      // fallback
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  async getHealth(): Promise<SystemHealth> {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse<SystemHealth>(res);
  },

  async submitReview(request: ReviewRequest): Promise<ReviewResponse> {
    const res = await fetch(`${API_BASE}/api/v1/reviews`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    return handleResponse<ReviewResponse>(res);
  },

  async getReview(reviewId: string): Promise<ReviewResponse> {
    const res = await fetch(`${API_BASE}/api/v1/reviews/${reviewId}`);
    return handleResponse<ReviewResponse>(res);
  },

  async listReviews(limit: number = 25, offset: number = 0): Promise<ReviewSummary[]> {
    const res = await fetch(`${API_BASE}/api/v1/reviews?limit=${limit}&offset=${offset}`);
    return handleResponse<ReviewSummary[]>(res);
  },

  async getMetrics(): Promise<MetricsSummary> {
    const res = await fetch(`${API_BASE}/api/v1/reviews/metrics/summary`);
    return handleResponse<MetricsSummary>(res);
  },

  async indexDirectory(directoryPath: string, maxFiles: number = 200, recursive: boolean = true): Promise<IndexStatusResponse> {
    const res = await fetch(`${API_BASE}/api/v1/index`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ directory_path: directoryPath, max_files: maxFiles, recursive }),
    });
    return handleResponse<IndexStatusResponse>(res);
  },

  async getIndexStatus(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/index/status`);
    return handleResponse<any>(res);
  },

  async searchCodebase(query: string, limit: number = 5): Promise<CodeSearchResponse> {
    const res = await fetch(`${API_BASE}/api/v1/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limit }),
    });
    return handleResponse<CodeSearchResponse>(res);
  },

  async getGitHubStatus(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/v1/webhooks/github/status`);
    return handleResponse<any>(res);
  },

  async simulateGitHubWebhook(codePatch: string, filePath: string = 'pr_change.py'): Promise<GitHubPRReviewEventResponse> {
    const res = await fetch(`${API_BASE}/api/v1/webhooks/github`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-GitHub-Event': 'pull_request',
        'X-GitHub-Delivery': `sim-${Date.now()}`,
      },
      body: JSON.stringify({
        action: 'opened',
        repository: { full_name: 'enterprise/codebase-repo' },
        pull_request: { number: 101 },
        code_patch: codePatch,
        file_path: filePath,
      }),
    });
    return handleResponse<GitHubPRReviewEventResponse>(res);
  },
};

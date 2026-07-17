import axiosInstance from './axios';
import { VectorStatsResponse, VectorSearchResponse } from '../types';

export const vectorApi = {
  getStats: async (): Promise<VectorStatsResponse> => {
    const response = await axiosInstance.get<VectorStatsResponse>('/vector/stats');
    return response.data;
  },

  search: async (query: string, nResults: number = 5, sourceType?: string): Promise<VectorSearchResponse> => {
    const response = await axiosInstance.get<VectorSearchResponse>('/vector/search', {
      params: { query, n_results: nResults, source_type: sourceType },
    });
    return response.data;
  },
};

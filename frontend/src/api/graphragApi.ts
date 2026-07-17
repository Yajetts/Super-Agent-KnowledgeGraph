import axiosInstance from './axios';
import { GraphRAGStatsResponse, GraphRAGContextResponse } from '../types';

export const graphragApi = {
  getStats: async (): Promise<GraphRAGStatsResponse> => {
    const response = await axiosInstance.get<GraphRAGStatsResponse>('/graphrag/stats');
    return response.data;
  },

  getContext: async (query: string): Promise<GraphRAGContextResponse> => {
    const response = await axiosInstance.get<GraphRAGContextResponse>('/graphrag/context', {
      params: { query },
    });
    return response.data;
  },
};

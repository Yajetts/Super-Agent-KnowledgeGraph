import axiosInstance from './axios';
import { GraphStatsResponse, GraphSchemaResponse, GraphContextResponse } from '../types';

export const graphApi = {
  getStats: async (): Promise<GraphStatsResponse> => {
    const response = await axiosInstance.get<GraphStatsResponse>('/graph/stats');
    return response.data;
  },

  getSchema: async (): Promise<GraphSchemaResponse> => {
    const response = await axiosInstance.get<GraphSchemaResponse>('/graph/schema');
    return response.data;
  },

  getContext: async (query: string): Promise<GraphContextResponse> => {
    const response = await axiosInstance.get<GraphContextResponse>('/graph/context', {
      params: { query },
    });
    return response.data;
  },
};

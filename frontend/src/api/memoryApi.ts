import axiosInstance from './axios';
import { MemoryStatsResponse, MemoryRecentResponse, MemoryAgentsResponse } from '../types';

export const memoryApi = {
  getStats: async (): Promise<MemoryStatsResponse> => {
    const response = await axiosInstance.get<MemoryStatsResponse>('/memory/stats');
    return response.data;
  },

  getRecentWorkflows: async (limit: number = 10, search?: string): Promise<MemoryRecentResponse> => {
    const response = await axiosInstance.get<MemoryRecentResponse>('/memory/recent', {
      params: { limit, search },
    });
    return response.data;
  },

  getAgentUsage: async (): Promise<MemoryAgentsResponse> => {
    const response = await axiosInstance.get<MemoryAgentsResponse>('/memory/agents');
    return response.data;
  },
};

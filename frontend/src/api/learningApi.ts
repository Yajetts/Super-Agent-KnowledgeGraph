import axiosInstance from './axios';
import { LearningPatternsResponse, LearningRecommendationResponse, LearningStatsResponse } from '../types';

export const learningApi = {
  getPatterns: async (limit: number = 20): Promise<LearningPatternsResponse> => {
    const response = await axiosInstance.get<LearningPatternsResponse>('/learning/patterns', {
      params: { limit },
    });
    return response.data;
  },

  getRecommendation: async (taskType?: string): Promise<LearningRecommendationResponse> => {
    const response = await axiosInstance.get<LearningRecommendationResponse>('/learning/recommendations', {
      params: { task_type: taskType },
    });
    return response.data;
  },

  getStats: async (): Promise<LearningStatsResponse> => {
    const response = await axiosInstance.get<LearningStatsResponse>('/learning/stats');
    return response.data;
  },
};

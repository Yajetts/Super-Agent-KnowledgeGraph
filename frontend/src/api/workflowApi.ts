import axiosInstance from './axios';
import { ExecuteRequest, ExecuteResponse } from '../types';

export const workflowApi = {
  execute: async (data: ExecuteRequest): Promise<ExecuteResponse> => {
    const response = await axiosInstance.post<ExecuteResponse>('/execute', data);
    return response.data;
  },
};

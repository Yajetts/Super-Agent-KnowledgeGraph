import axiosInstance from './axios';
import {
  AgentsResponse,
  DynamicAgentsResponse,
  AgentDetailResponse,
  CreateAgentRequest,
  CreateAgentResponse,
  TaskAnalysisResponse,
  AgentSkillsResponse,
} from '../types';

export const agentApi = {
  getAllAgents: async (): Promise<AgentsResponse> => {
    const response = await axiosInstance.get<AgentsResponse>('/agents');
    return response.data;
  },

  getDynamicAgents: async (): Promise<DynamicAgentsResponse> => {
    const response = await axiosInstance.get<DynamicAgentsResponse>('/agents/dynamic');
    return response.data;
  },

  getAgentDetails: async (agentName: string): Promise<AgentDetailResponse> => {
    const response = await axiosInstance.get<AgentDetailResponse>(`/agents/${agentName}`);
    return response.data;
  },

  createAgent: async (data: CreateAgentRequest): Promise<CreateAgentResponse> => {
    const response = await axiosInstance.post<CreateAgentResponse>('/agents/create', data);
    return response.data;
  },

  analyzeTask: async (query: string): Promise<TaskAnalysisResponse> => {
    const response = await axiosInstance.post<TaskAnalysisResponse>('/agents/analyze', { query });
    return response.data;
  },

  getAgentSkills: async (agentName: string): Promise<AgentSkillsResponse> => {
    const response = await axiosInstance.get<AgentSkillsResponse>(`/agents/${agentName}/skills`);
    return response.data;
  },
};

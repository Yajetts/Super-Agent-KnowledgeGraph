export interface RootResponse {
  status: 'running';
  project: 'SuperAgent Knowledge Graph';
}

export interface ExecuteRequest {
  query: string;
}

export interface Finding {
  source_agent: string;
  category: string;
  content: string;
  confidence: number;
}

export interface Recommendation {
  source_agent: string;
  content: string;
  priority: string;
}

export interface Risk {
  source_agent: string;
  description: string;
  severity: string;
}

export interface ExecuteResponse {
  query: string;
  task_type: string;
  agents_used: string[];
  findings: Finding[];
  risks: Risk[];
  recommendations: Recommendation[];
  execution_time: number;
  workflow_id: number | null;
  chain_of_thought: string;
  formatted_response: string;
}

export interface GraphStatsResponse {
  tasks: number;
  agents: number;
  findings: number;
  risks: number;
  recommendations: number;
}

export interface GraphSchemaNodeType {
  label: string;
  properties: string[];
}

export interface GraphSchemaRelationshipType {
  type: string;
  source: string;
  target: string;
}

export interface AgentMetadata {
  name: string;
  description: string;
  skills: string[];
}

export interface GraphSchemaResponse {
  node_types: GraphSchemaNodeType[];
  relationship_types: GraphSchemaRelationshipType[];
  agents: AgentMetadata[];
}

export interface GraphContextResponse {
  related_tasks: Record<string, unknown>[];
  related_findings: Record<string, unknown>[];
  related_risks: Record<string, unknown>[];
  related_recommendations: Record<string, unknown>[];
  summary: string;
}

export interface VectorStatsResponse {
  documents: number;
}

export interface VectorSearchResult {
  document_id: string;
  content: string;
  metadata: Record<string, string>;
  similarity_score: number;
}

export interface VectorSearchResponse {
  results: VectorSearchResult[];
  summary: string;
  query: string;
}

export interface GraphRAGStatsResponse {
  graph_nodes: number;
  vector_documents: number;
  fusion_results: number;
  graph_available: boolean;
  vector_available: boolean;
}

export interface GraphRAGContextResponse {
  query: string;
  graph_results: Record<string, unknown>[];
  vector_results: Record<string, unknown>[];
  merged_findings: Record<string, unknown>[];
  merged_risks: Record<string, unknown>[];
  merged_recommendations: Record<string, unknown>[];
  context_summary: string;
  retrieval_metadata: Record<string, unknown>;
}

export interface MemoryStatsResponse {
  workflows: number;
  agent_executions: number;
  retrieval_records: number;
}

export interface WorkflowMemoryItem {
  id: number;
  query: string;
  task_type: string;
  timestamp: string;
  execution_time: number;
  agents_used: string[];
  graph_results_count: number;
  vector_results_count: number;
  fusion_results_count: number;
}

export interface MemoryRecentResponse {
  workflows: WorkflowMemoryItem[];
}

export interface AgentUsageItem {
  agent_name: string;
  usage_count: number;
}

export interface AgentUsageStatsItem {
  agent_name: string;
  total_executions: number;
  average_execution_time: number;
  min_execution_time: number;
  max_execution_time: number;
}

export interface MemoryAgentsResponse {
  most_used_agents: AgentUsageItem[];
  agent_usage_statistics: AgentUsageStatsItem[];
}

export interface LearningPatternItem {
  task_type: string;
  workflow_pattern: string[];
  success_score: number;
  usage_count: number;
  last_updated: string;
}

export interface LearningPatternsResponse {
  patterns: LearningPatternItem[];
}

export interface LearningRecommendationResponse {
  task_type: string;
  recommended_agents: string[];
  confidence: number;
  supporting_examples: number;
}

export interface LearningStatsResponse {
  reflections: number;
  patterns: number;
  successful_patterns: number;
  avg_success_score: number;
}

export interface AgentItem {
  name: string;
  description: string;
  skills: string[];
  task_types: string[];
  creation_source: string;
  creation_timestamp: string | null;
  usage_count: number;
  is_dynamic: boolean;
}

export interface AgentsResponse {
  agents: AgentItem[];
}

export interface DynamicAgentsResponse {
  agents: AgentItem[];
}

export interface AgentDetailResponse {
  name: string;
  description: string;
  skills: string[];
  task_types: string[];
  creation_source: string;
  creation_timestamp: string | null;
  usage_count: number;
  is_dynamic: boolean;
  system_prompt: string;
}

export interface CreateAgentRequest {
  name: string;
  description: string;
  skills: string[];
  task_type: string;
  system_prompt: string;
}

export interface CreateAgentResponse {
  success: boolean;
  agent_name: string;
  message: string;
}

export interface TaskAnalysisResponse {
  task_query: string;
  task_type: string;
  required_skills: string[];
  capability_gaps: Record<string, unknown>[];
  coverage_score: number;
  should_create_agent: boolean;
}

export interface SkillItem {
  skill_id: number;
  skill_name: string;
  description: string;
  file_path: string;
  created_at: string;
}

export interface SkillsResponse {
  skills: SkillItem[];
}

export interface SkillMetricsItem {
  skill_id: number;
  skill_name: string;
  usage_count: number;
  invocation_frequency: number;
  avg_performance_with_skill: number;
  avg_performance_without_skill: number;
  last_updated: string;
}

export interface SkillMetricsResponse {
  metrics: SkillMetricsItem[];
}

export interface SkillStatsResponse {
  total_skills: number;
  total_agents_with_skills: number;
  total_relationships: number;
  most_used_skills: Record<string, unknown>[];
}

export interface AgentSkillsResponse {
  agent_name: string;
  skills: string[];
}

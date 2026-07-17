import { Box, Card, CardContent, Typography, Accordion, AccordionSummary, AccordionDetails, Chip, Divider, Paper } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { Finding, Risk, Recommendation } from '../types';

interface WorkflowResultProps {
  result: {
    task_type: string;
    agents_used: string[];
    findings: Finding[];
    risks: Risk[];
    recommendations: Recommendation[];
    execution_time: number;
    chain_of_thought: string;
    formatted_response: string;
  };
}

// Truncate text to a reasonable length
const truncateText = (text: string, maxLength: number = 150): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength).trim() + '...';
};

export const WorkflowResult = ({ result }: WorkflowResultProps) => {
  // Extract top findings (up to 5)
  const topFindings = result.findings.slice(0, 5);
  // Extract top risks (up to 5)
  const topRisks = result.risks.slice(0, 5);
  // Extract top recommendations (up to 5)
  const topRecommendations = result.recommendations.slice(0, 5);

  // Generate overall assessment from formatted_response or findings
  const overallAssessment = result.formatted_response 
    ? truncateText(result.formatted_response, 200)
    : `Analysis completed with ${result.findings.length} findings, ${result.risks.length} risks, and ${result.recommendations.length} recommendations.`;

  return (
    <Box>
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h4" gutterBottom fontWeight="bold">
            Executive Summary
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          

          <Box mb={2}>
            <Typography variant="subtitle1" fontWeight="bold" color="textSecondary">
              Overall Assessment:
            </Typography>
            <Typography variant="body1">{overallAssessment}</Typography>
          </Box>

          <Divider sx={{ my: 2 }} />

          <Box mb={2}>
            <Typography variant="subtitle2" color="textSecondary">
              Task Type
            </Typography>
            <Chip label={result.task_type} size="small" />
          </Box>

          

          <Box mb={2}>
            <Typography variant="subtitle2" color="textSecondary">
              Execution Time
            </Typography>
            <Typography variant="body1">{result.execution_time.toFixed(2)}s</Typography>
          </Box>

          <Box mb={2}>
            <Typography variant="subtitle2" color="textSecondary">
              Agents Used
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={0.5}>
              {result.agents_used.map((agent) => (
                <Chip key={agent} label={agent} size="small" variant="outlined" />
              ))}
            </Box>
          </Box>
        </CardContent>
      </Card>

      {result.chain_of_thought && (
        <Accordion sx={{ mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">Chain of Thought</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" whiteSpace="pre-wrap">
              {result.chain_of_thought}
            </Typography>
          </AccordionDetails>
        </Accordion>
      )}

      <Paper sx={{ mb: 2, p: 3 }}>
        <Typography variant="h5" gutterBottom fontWeight="bold">
          Key Findings
        </Typography>
        <Divider sx={{ mb: 2 }} />
        {topFindings.length > 0 ? (
          topFindings.map((finding, index) => (
            <Box key={index} mb={1.5}>
              <Typography variant="body1" component="div">
                • {truncateText(finding.content, 120)}
              </Typography>
            </Box>
          ))
        ) : (
          <Typography variant="body2" color="textSecondary">No findings available</Typography>
        )}
      </Paper>

      <Paper sx={{ mb: 2, p: 3 }}>
        <Typography variant="h5" gutterBottom fontWeight="bold" color="error">
          Critical Risks
        </Typography>
        <Divider sx={{ mb: 2 }} />
        {topRisks.length > 0 ? (
          topRisks.map((risk, index) => (
            <Box key={index} mb={1.5}>
              <Typography variant="body1" component="div">
                • {truncateText(risk.description, 120)}
              </Typography>
            </Box>
          ))
        ) : (
          <Typography variant="body2" color="textSecondary">No risks identified</Typography>
        )}
      </Paper>

      <Paper sx={{ mb: 2, p: 3 }}>
        <Typography variant="h5" gutterBottom fontWeight="bold" color="primary">
          Recommended Actions
        </Typography>
        <Divider sx={{ mb: 2 }} />
        {topRecommendations.length > 0 ? (
          topRecommendations.map((recommendation, index) => (
            <Box key={index} mb={1.5}>
              <Typography variant="body1" component="div">
                {index + 1}. {truncateText(recommendation.content, 120)}
              </Typography>
            </Box>
          ))
        ) : (
          <Typography variant="body2" color="textSecondary">No recommendations available</Typography>
        )}
      </Paper>

      {result.findings.length > 0 && (
        <Accordion sx={{ mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">All Findings ({result.findings.length})</Typography>
          </AccordionSummary>
          <AccordionDetails>
            {result.findings.map((finding, index) => (
              <Box key={index} mb={2}>
                <Typography variant="subtitle1" fontWeight="bold">
                  {finding.category}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Source: {finding.source_agent}
                </Typography>
                <Typography variant="body1" mt={1}>
                  {finding.content}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Confidence: {(finding.confidence * 100).toFixed(0)}%
                </Typography>
                {index < result.findings.length - 1 && <Divider sx={{ mt: 2 }} />}
              </Box>
            ))}
          </AccordionDetails>
        </Accordion>
      )}

      {result.risks.length > 0 && (
        <Accordion sx={{ mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">All Risks ({result.risks.length})</Typography>
          </AccordionSummary>
          <AccordionDetails>
            {result.risks.map((risk, index) => (
              <Box key={index} mb={2}>
                <Typography variant="subtitle1" fontWeight="bold">
                  {risk.severity}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Source: {risk.source_agent}
                </Typography>
                <Typography variant="body1" mt={1}>
                  {risk.description}
                </Typography>
                {index < result.risks.length - 1 && <Divider sx={{ mt: 2 }} />}
              </Box>
            ))}
          </AccordionDetails>
        </Accordion>
      )}

      {result.recommendations.length > 0 && (
        <Accordion sx={{ mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">All Recommendations ({result.recommendations.length})</Typography>
          </AccordionSummary>
          <AccordionDetails>
            {result.recommendations.map((recommendation, index) => (
              <Box key={index} mb={2}>
                <Typography variant="subtitle1" fontWeight="bold">
                  {recommendation.priority}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Source: {recommendation.source_agent}
                </Typography>
                <Typography variant="body1" mt={1}>
                  {recommendation.content}
                </Typography>
                {index < result.recommendations.length - 1 && <Divider sx={{ mt: 2 }} />}
              </Box>
            ))}
          </AccordionDetails>
        </Accordion>
      )}
    </Box>
  );
};

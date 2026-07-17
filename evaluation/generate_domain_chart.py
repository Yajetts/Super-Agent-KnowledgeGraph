"""Generate domain distribution bar chart as PNG."""

import matplotlib.pyplot as plt
import numpy as np

# Data from domain distribution
domains = ['Technology', 'Business/Finance', 'Healthcare', 'Manufacturing', 'Energy', 'Education']
counts = [10, 8, 3, 3, 2, 1]
percentages = [37.0, 29.6, 11.1, 11.1, 7.4, 3.7]

# Create figure
fig, ax = plt.subplots(figsize=(10, 6))

# Grayscale-friendly colors (using different shades of gray)
colors = ['#4a4a4a', '#6b6b6b', '#8c8c8c', '#adadad', '#cecece', '#efefef']

# Create bar chart
bars = ax.bar(domains, percentages, color=colors, edgecolor='black', linewidth=1.2)

# Add percentage labels above bars
for bar, pct in zip(bars, percentages):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
            f'{pct}%',
            ha='center', va='bottom', fontsize=11, fontweight='bold')

# Customize chart
ax.set_xlabel('Domain', fontsize=12, fontweight='bold')
ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
ax.set_title('Distribution of Evaluation Documents Across Domains', fontsize=14, fontweight='bold', pad=20)
ax.set_ylim(0, 45)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Rotate x-axis labels for better readability
plt.xticks(rotation=45, ha='right')

# Adjust layout to prevent label cutoff
plt.tight_layout()

# Save as PNG
plt.savefig('c:/Users/yajat/OneDrive/C3Iproj/superagent-kg/docs/domain_distribution.png', 
            dpi=300, bbox_inches='tight', facecolor='white')
print("Chart saved to docs/domain_distribution.png")
plt.close()

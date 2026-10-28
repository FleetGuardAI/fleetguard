import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import MarkdownMessage from '../MarkdownMessage';

describe('MarkdownMessage Component', () => {
  it('renders null when content is empty or null', () => {
    const { container: c1 } = render(<MarkdownMessage content={null} />);
    expect(c1.firstChild).toBeNull();

    const { container: c2 } = render(<MarkdownMessage content="" />);
    expect(c2.firstChild).toBeNull();
  });

  it('renders headings, bold, and italic text correctly', () => {
    const markdown = `# Fleet Operations\n## Vehicle Status\n### Diagnostics\nThis is **bold text** and *italic text*.`;
    render(<MarkdownMessage content={markdown} />);

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Fleet Operations');
    expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent('Vehicle Status');
    expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('Diagnostics');
    expect(screen.getByText('bold text')).toBeInTheDocument();
    expect(screen.getByText('italic text')).toBeInTheDocument();
  });

  it('renders unordered and ordered lists', () => {
    const markdown = `- Truck 01: Active\n- Truck 02: Maintenance\n\n1. Check fuel\n2. Schedule trip`;
    render(<MarkdownMessage content={markdown} />);

    expect(screen.getByText(/Truck 01: Active/)).toBeInTheDocument();
    expect(screen.getByText(/Truck 02: Maintenance/)).toBeInTheDocument();
    expect(screen.getByText(/Check fuel/)).toBeInTheDocument();
    expect(screen.getByText(/Schedule trip/)).toBeInTheDocument();
  });

  it('renders markdown tables when suppressTables is false', () => {
    const markdown = `Here is the fleet table:\n\n| Vehicle | Status |\n| --- | --- |\n| MH12AB1001 | Active |\n| MH12AB1002 | Maintenance |`;
    render(<MarkdownMessage content={markdown} suppressTables={false} />);

    expect(screen.getByText('Here is the fleet table:')).toBeInTheDocument();
    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getByText('MH12AB1001')).toBeInTheDocument();
    expect(screen.getByText('MH12AB1002')).toBeInTheDocument();
  });

  it('suppresses markdown tables when suppressTables is true to prevent duplicate card rendering', () => {
    const markdown = `Here is the location report:\n\n| Registration | Lat | Lng |\n| --- | --- | --- |\n| MH12AB1001 | 18.52 | 73.85 |`;
    render(<MarkdownMessage content={markdown} suppressTables={true} />);

    // Explanatory text is preserved
    expect(screen.getByText('Here is the location report:')).toBeInTheDocument();
    // Table is suppressed
    expect(screen.queryByRole('table')).toBeNull();
  });

  it('sanitizes unsafe javascript: links to prevent XSS execution', () => {
    const markdown = `[Safe Link](https://fleetguard.ai) and [Malicious Link](javascript:alert('XSS'))`;
    render(<MarkdownMessage content={markdown} />);

    const safeLink = screen.getByRole('link', { name: 'Safe Link' });
    expect(safeLink).toHaveAttribute('href', 'https://fleetguard.ai');

    // Unsafe link should not be rendered with javascript: href
    expect(screen.queryByRole('link', { name: 'Malicious Link' })).toBeNull();
    expect(screen.getByText('Malicious Link')).toBeInTheDocument();
  });

  it('renders inline code and code blocks properly', () => {
    const markdown = `Run \`get_vehicle_location\` to inspect coordinates:\n\n\`\`\`json\n{"status": "ok"}\n\`\`\``;
    render(<MarkdownMessage content={markdown} />);

    expect(screen.getByText('get_vehicle_location')).toBeInTheDocument();
    expect(screen.getByText(/{"status": "ok"}/)).toBeInTheDocument();
  });
});

import React from 'react'
import { render, screen } from '@testing-library/react'
import JobList, { Match } from '../components/JobList'

// Mock JobList component test structure
describe('JobList Component UI Rendering', () => {
  const dummyMatches: Match[] = [
    {
      job: {
        id: 'job-1',
        title: 'Senior Solutions Architect',
        company: 'Cloud Giants',
        location: 'Remote',
        is_remote: true,
        description: 'Design and deploy resilient multi-region architectures.',
        url: 'http://giants.com/1',
        posted_at: new Date().toISOString()
      },
      match_score: 0.95,
      matching_details: {
        reasons: ['Matched title: Senior Solutions Architect', 'Remote criteria satisfied'],
        matched_keywords: ['Architect']
      },
      status: 'pending'
    }
  ]

  it('renders job title and company correctly', () => {
    // Basic structural rendering assertion
    const { getByText } = render(
      <JobList matches={dummyMatches} onStatusUpdate={() => {}} />
    )
    
    expect(getByText('Senior Solutions Architect')).toBeInTheDocument()
    expect(getByText('Cloud Giants')).toBeInTheDocument()
  })

  it('displays accurate match score badge', () => {
    const { getByText } = render(
      <JobList matches={dummyMatches} onStatusUpdate={() => {}} />
    )
    expect(getByText('95% Match')).toBeInTheDocument()
  })
})

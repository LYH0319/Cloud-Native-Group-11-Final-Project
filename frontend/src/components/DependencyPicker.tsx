import { useMemo, useState } from 'react';
import { type BackendJob } from '../types/types';
import './DependencyPicker.css';

interface DependencyPickerProps {
  jobs: BackendJob[];
  selectedIds: number[];
  idPrefix: string;
  onToggle: (jobId: number) => void;
}

export const DependencyPicker = ({
  jobs,
  selectedIds,
  idPrefix,
  onToggle
}: DependencyPickerProps) => {
  const [query, setQuery] = useState('');
  const normalizedQuery = query.trim().toLowerCase();
  const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds]);
  const filteredJobs = useMemo(() => {
    if (!normalizedQuery) return jobs;
    return jobs.filter((job) =>
      `${job.job_id} ${job.job_name} ${job.endpoint}`.toLowerCase().includes(normalizedQuery)
    );
  }, [jobs, normalizedQuery]);

  // 1. Extract nested ternary logic into an independent statement
  let pickerContent;
  
  if (jobs.length === 0) {
    pickerContent = <div className="dependency-picker-empty">No active jobs available</div>;
  } else if (filteredJobs.length === 0) {
    pickerContent = <div className="dependency-picker-empty">No matching jobs</div>;
  } else {
    pickerContent = (
      <div className="dependency-picker-list">
        {filteredJobs.map((job) => {
          const checked = selectedSet.has(job.job_id);
          return (
            <label
              className={`dependency-picker-item ${checked ? 'is-selected' : ''}`}
              htmlFor={`${idPrefix}-${job.job_id}`}
              key={job.job_id}
              // 2. Add aria-label to satisfy accessibility (a11y) requirements
              aria-label={`Job ${job.job_id}: ${job.job_name}`}
            >
              <input
                className="form-check-input"
                type="checkbox"
                id={`${idPrefix}-${job.job_id}`}
                checked={checked}
                onChange={() => onToggle(job.job_id)}
              />
              <span className="dependency-picker-main">
                <span className="dependency-picker-title">
                  <span className="dependency-picker-id">#{job.job_id}</span>
                  {job.job_name}
                </span>
                <span className="dependency-picker-endpoint">{job.endpoint}</span>
              </span>
            </label>
          );
        })}
      </div>
    );
  }

  return (
    <div className="dependency-picker">
      <div className="dependency-picker-toolbar">
        <input
          className="form-control form-control-sm"
          placeholder="Search jobs by name, ID, endpoint"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <span className="dependency-picker-count">{selectedIds.length} selected</span>
      </div>

      {/* Render the computed content directly */}
      {pickerContent}
    </div>
  );
};
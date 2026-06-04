import { useEffect, useState } from 'react';
import './CronSchedulePicker.css';

type CronMode = 'minutes' | 'hourly' | 'daily' | 'weekly' | 'monthly' | 'advanced';

interface CronSchedulePickerProps {
  disabled?: boolean;
  value: string;
  onChange: (value: string) => void;
}

const weekdayOptions = [
  { label: 'Sunday', value: '0' },
  { label: 'Monday', value: '1' },
  { label: 'Tuesday', value: '2' },
  { label: 'Wednesday', value: '3' },
  { label: 'Thursday', value: '4' },
  { label: 'Friday', value: '5' },
  { label: 'Saturday', value: '6' }
];

const intervalOptions = [5, 10, 15, 30];
const hourOptions = Array.from({ length: 24 }, (_, hour) => hour);
const minuteOptions = [0, 15, 30, 45];
const dayOptions = Array.from({ length: 31 }, (_, index) => index + 1);

const inferMode = (value: string): CronMode => {
  if (/^\*\/\d+ \* \* \* \*$/.test(value)) return 'minutes';
  if (/^\d+ \* \* \* \*$/.test(value)) return 'hourly';
  if (/^\d+ \d+ \* \* \*$/.test(value)) return 'daily';
  if (/^\d+ \d+ \* \* \d+$/.test(value)) return 'weekly';
  if (/^\d+ \d+ \d+ \* \*$/.test(value)) return 'monthly';
  return 'advanced';
};

const parts = (value: string) => value.trim().split(/\s+/);
const numberPart = (value: string | undefined, fallback: number) => {
  const parsed = Number(value?.replace('*/', ''));
  return Number.isFinite(parsed) ? parsed : fallback;
};

export const CronSchedulePicker = ({
  disabled = false,
  value,
  onChange
}: CronSchedulePickerProps) => {
  const [mode, setMode] = useState<CronMode>(() => inferMode(value));
  const [minute = '0', hour = '0', day = '1', , weekday = '1'] = parts(value);

  useEffect(() => {
    if (disabled) {
      setMode(inferMode(value));
    }
  }, [disabled, value]);

  const updateMode = (nextMode: CronMode) => {
    setMode(nextMode);
    const defaults: Record<CronMode, string> = {
      minutes: '*/5 * * * *',
      hourly: '0 * * * *',
      daily: '0 9 * * *',
      weekly: '0 9 * * 1',
      monthly: '0 9 1 * *',
      advanced: value || '*/5 * * * *'
    };
    onChange(defaults[nextMode]);
  };

  return (
    <div className={`cron-picker ${disabled ? 'is-disabled' : ''}`}>
      <label htmlFor="repeat-interval-select" className="form-label">Repeat interval</label>
      <select
        id="repeat-interval-select"
        className="form-select mb-2"
        disabled={disabled}
        value={mode}
        onChange={(event) => updateMode(event.target.value as CronMode)}
      >
        <option value="minutes">Every few minutes</option>
        <option value="hourly">Hourly</option>
        <option value="daily">Daily</option>
        <option value="weekly">Weekly</option>
        <option value="monthly">Monthly</option>
        <option value="advanced">Advanced cron</option>
      </select>

      {mode === 'minutes' && (
        <div className="cron-picker-row">
          <span>Every</span>
          <select
            className="form-select form-select-sm"
            disabled={disabled}
            value={numberPart(minute, 5)}
            onChange={(event) => onChange(`*/${event.target.value} * * * *`)}
          >
            {intervalOptions.map((option) => (
              <option value={option} key={option}>
                {option}
              </option>
            ))}
          </select>
          <span>minutes</span>
        </div>
      )}

      {mode === 'hourly' && (
        <div className="cron-picker-row">
          <span>At minute</span>
          <select
            className="form-select form-select-sm"
            disabled={disabled}
            value={numberPart(minute, 0)}
            onChange={(event) => onChange(`${event.target.value} * * * *`)}
          >
            {minuteOptions.map((option) => (
              <option value={option} key={option}>
                {String(option).padStart(2, '0')}
              </option>
            ))}
          </select>
          <span>of every hour</span>
        </div>
      )}

      {mode === 'daily' && (
        <div className="cron-picker-row">
          <span>Every day at</span>
          <select
            className="form-select form-select-sm"
            disabled={disabled}
            value={numberPart(hour, 9)}
            onChange={(event) => onChange(`${numberPart(minute, 0)} ${event.target.value} * * *`)}
          >
            {hourOptions.map((option) => (
              <option value={option} key={option}>
                {String(option).padStart(2, '0')}
              </option>
            ))}
          </select>
          <span>:</span>
          <select
            className="form-select form-select-sm"
            disabled={disabled}
            value={numberPart(minute, 0)}
            onChange={(event) => onChange(`${event.target.value} ${numberPart(hour, 9)} * * *`)}
          >
            {minuteOptions.map((option) => (
              <option value={option} key={option}>
                {String(option).padStart(2, '0')}
              </option>
            ))}
          </select>
        </div>
      )}

      {mode === 'weekly' && (
        <div className="cron-picker-row">
          <span>Every</span>
          <select
            className="form-select form-select-sm"
            disabled={disabled}
            value={weekday}
            onChange={(event) =>
              onChange(`${numberPart(minute, 0)} ${numberPart(hour, 9)} * * ${event.target.value}`)
            }
          >
            {weekdayOptions.map((option) => (
              <option value={option.value} key={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <span>at</span>
          <select
            className="form-select form-select-sm"
            disabled={disabled}
            value={numberPart(hour, 9)}
            onChange={(event) =>
              onChange(`${numberPart(minute, 0)} ${event.target.value} * * ${weekday}`)
            }
          >
            {hourOptions.map((option) => (
              <option value={option} key={option}>
                {String(option).padStart(2, '0')}
              </option>
            ))}
          </select>
          <span>:</span>
          <select
            className="form-select form-select-sm"
            disabled={disabled}
            value={numberPart(minute, 0)}
            onChange={(event) =>
              onChange(`${event.target.value} ${numberPart(hour, 9)} * * ${weekday}`)
            }
          >
            {minuteOptions.map((option) => (
              <option value={option} key={option}>
                {String(option).padStart(2, '0')}
              </option>
            ))}
          </select>
        </div>
      )}

      {mode === 'monthly' && (
        <div className="cron-picker-row">
          <span>Day</span>
          <select
            className="form-select form-select-sm"
            disabled={disabled}
            value={numberPart(day, 1)}
            onChange={(event) =>
              onChange(`${numberPart(minute, 0)} ${numberPart(hour, 9)} ${event.target.value} * *`)
            }
          >
            {dayOptions.map((option) => (
              <option value={option} key={option}>
                {option}
              </option>
            ))}
          </select>
          <span>at</span>
          <select
            className="form-select form-select-sm"
            disabled={disabled}
            value={numberPart(hour, 9)}
            onChange={(event) =>
              onChange(`${numberPart(minute, 0)} ${event.target.value} ${numberPart(day, 1)} * *`)
            }
          >
            {hourOptions.map((option) => (
              <option value={option} key={option}>
                {String(option).padStart(2, '0')}
              </option>
            ))}
          </select>
          <span>:</span>
          <select
            className="form-select form-select-sm"
            disabled={disabled}
            value={numberPart(minute, 0)}
            onChange={(event) =>
              onChange(`${event.target.value} ${numberPart(hour, 9)} ${numberPart(day, 1)} * *`)
            }
          >
            {minuteOptions.map((option) => (
              <option value={option} key={option}>
                {String(option).padStart(2, '0')}
              </option>
            ))}
          </select>
        </div>
      )}

      {mode === 'advanced' && (
        <input
          className="form-control"
          disabled={disabled}
          placeholder="*/5 * * * *"
          value={value}
          onChange={(event) => onChange(event.target.value)}
        />
      )}

      <div className="cron-picker-preview">Cron: {disabled ? '-' : value}</div>
    </div>
  );
};

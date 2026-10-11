import React, { useState, useEffect, useRef } from 'react';
import { useDebounce } from '../../hooks/useDebounce';
import { useGeocode } from '../../api/queries';
import { GeocodeLocation } from '../../types/api';
import { MapPin, Loader2, X } from 'lucide-react';

interface AutocompleteInputProps {
  id: string;
  label: string;
  placeholder: string;
  query: string;
  selectedLocation: GeocodeLocation | null;
  onQueryChange: (query: string) => void;
  onSelect: (location: GeocodeLocation) => void;
  onClear: () => void;
  error?: string;
  iconColor?: string;
}

export const AutocompleteInput: React.FC<AutocompleteInputProps> = ({
  id,
  label,
  placeholder,
  query,
  selectedLocation,
  onQueryChange,
  onSelect,
  onClear,
  error,
  iconColor = '#3b82f6',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const debouncedQuery = useDebounce(query, 300);
  const { data, isLoading } = useGeocode(debouncedQuery);

  const results = data?.results || [];

  // Close dropdown on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onQueryChange(e.target.value);
    setIsOpen(true);
    setHighlightedIndex(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || results.length === 0) {
      if (e.key === 'ArrowDown' && results.length > 0) {
        setIsOpen(true);
      }
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev < results.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : results.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (highlightedIndex >= 0 && highlightedIndex < results.length) {
        handleSelect(results[highlightedIndex]);
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const handleSelect = (loc: GeocodeLocation) => {
    onSelect(loc);
    setIsOpen(false);
    setHighlightedIndex(-1);
  };

  return (
    <div className="input-group" ref={containerRef}>
      <label htmlFor={id} className="input-label">
        <MapPin size={15} style={{ color: iconColor }} />
        <span>{label}</span>
      </label>

      <div className="input-wrapper">
        <input
          id={id}
          ref={inputRef}
          type="text"
          className={`text-input ${error ? 'input-error' : ''} ${selectedLocation ? 'input-selected' : ''}`}
          placeholder={placeholder}
          value={query}
          onChange={handleInputChange}
          onFocus={() => {
            if (results.length > 0) setIsOpen(true);
          }}
          onKeyDown={handleKeyDown}
          autoComplete="off"
        />

        {isLoading && (
          <div className="input-adornment">
            <Loader2 size={16} className="spin-icon" />
          </div>
        )}

        {query && !isLoading && (
          <button
            type="button"
            className="input-clear-btn"
            onClick={() => {
              onClear();
              inputRef.current?.focus();
            }}
            title="Clear"
            aria-label={`Clear ${label}`}
          >
            <X size={14} />
          </button>
        )}
      </div>

      {error && <span className="error-message">{error}</span>}

      {isOpen && results.length > 0 && (
        <ul className="autocomplete-dropdown" role="listbox">
          {results.map((item, idx) => (
            <li
              key={`${item.lat}-${item.lng}-${idx}`}
              role="option"
              aria-selected={highlightedIndex === idx}
              className={`dropdown-item ${highlightedIndex === idx ? 'item-highlighted' : ''}`}
              onMouseEnter={() => setHighlightedIndex(idx)}
              onClick={() => handleSelect(item)}
            >
              <MapPin size={14} className="dropdown-pin" />
              <div className="dropdown-text">
                <span className="dropdown-title">{item.label}</span>
                <span className="dropdown-coords">
                  {item.lat.toFixed(3)}, {item.lng.toFixed(3)}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

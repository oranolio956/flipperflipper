/**
 * Search Builder Component v3.6.0
 * Visual interface for creating marketplace searches
 */

import React, { useState, useEffect } from 'react';
import { SearchParameters } from '../lib/search-builder';

interface SearchBuilderProps {
  onSave: (search: SearchParameters) => void;
  onCancel: () => void;
  initialSearch?: SearchParameters;
}

export function SearchBuilder({ onSave, onCancel, initialSearch }: SearchBuilderProps) {
  const [platform, setPlatform] = useState<'facebook' | 'craigslist' | 'offerup'>('facebook');
  const [keywords, setKeywords] = useState<string[]>(['gaming pc', 'gaming computer']);
  const [minPrice, setMinPrice] = useState(200);
  const [maxPrice, setMaxPrice] = useState(2000);
  const [radius, setRadius] = useState(25);
  const [conditions, setConditions] = useState<string[]>(['used', 'like-new']);
  const [previewUrl, setPreviewUrl] = useState('');
  
  // Platform-specific state
  const [fbOptions, setFbOptions] = useState({
    sortBy: 'date',
    daysSinceListed: 7,
    delivery: 'local'
  });
  
  const [clOptions, setClOptions] = useState({
    section: 'sya',
    city: 'sfbay',
    hasImage: true,
    postedToday: false,
    searchTitlesOnly: false
  });
  
  const [ouOptions, setOuOptions] = useState({
    sellerType: 'owner',
    priceNegotiable: true
  });
  
  // Build search parameters
  const buildSearchParams = (): SearchParameters => {
    const params: SearchParameters = {
      platform,
      keywords,
      minPrice,
      maxPrice,
      location: { radius },
      condition: conditions as any,
      filters: [],
      enabled: true,
      interval: 30,
      notifications: true
    };
    
    // Add platform-specific options
    if (platform === 'facebook') {
      params.facebook = fbOptions as any;
    } else if (platform === 'craigslist') {
      params.craigslist = clOptions as any;
    } else if (platform === 'offerup') {
      params.offerup = ouOptions as any;
    }
    
    return params;
  };
  
  // Update preview URL when parameters change
  useEffect(() => {
    if (window.searchBuilder) {
      const params = buildSearchParams();
      const url = window.searchBuilder.buildUrl(params);
      setPreviewUrl(url);
    }
  }, [platform, keywords, minPrice, maxPrice, radius, conditions, fbOptions, clOptions, ouOptions]);
  
  const handleAddKeyword = (keyword: string) => {
    if (keyword && !keywords.includes(keyword)) {
      setKeywords([...keywords, keyword]);
    }
  };
  
  const handleRemoveKeyword = (keyword: string) => {
    setKeywords(keywords.filter(k => k !== keyword));
  };
  
  const handleConditionToggle = (condition: string) => {
    if (conditions.includes(condition)) {
      setConditions(conditions.filter(c => c !== condition));
    } else {
      setConditions([...conditions, condition]);
    }
  };
  
  const handleSave = () => {
    const params = buildSearchParams();
    const validation = window.searchBuilder.validateParameters(params);
    
    if (validation.valid) {
      onSave(params);
    } else {
      alert(`Validation errors:\n${validation.errors.join('\n')}`);
    }
  };
  
  const handleTestSearch = () => {
    window.open(previewUrl, '_blank');
  };
  
  const handleCopyUrl = () => {
    navigator.clipboard.writeText(previewUrl);
    alert('URL copied to clipboard!');
  };
  
  return (
    <div className="search-builder">
      {/* Platform Selection */}
      <div className="platform-selector">
        <h3>Select Platform</h3>
        <div className="platform-cards">
          <div 
            className={`platform-card ${platform === 'facebook' ? 'active' : ''}`}
            onClick={() => setPlatform('facebook')}
          >
            <span>Facebook</span>
          </div>
          <div 
            className={`platform-card ${platform === 'craigslist' ? 'active' : ''}`}
            onClick={() => setPlatform('craigslist')}
          >
            <span>Craigslist</span>
          </div>
          <div 
            className={`platform-card ${platform === 'offerup' ? 'active' : ''}`}
            onClick={() => setPlatform('offerup')}
          >
            <span>OfferUp</span>
          </div>
        </div>
      </div>
      
      {/* Keywords */}
      <div className="param-section">
        <h4>Keywords</h4>
        <div className="keyword-builder">
          <input 
            type="text"
            placeholder="Enter keywords..."
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleAddKeyword(e.currentTarget.value);
                e.currentTarget.value = '';
              }
            }}
          />
        </div>
        <div className="keyword-tags">
          {keywords.map(keyword => (
            <span key={keyword} className="keyword-tag">
              {keyword}
              <button onClick={() => handleRemoveKeyword(keyword)}>&times;</button>
            </span>
          ))}
        </div>
      </div>
      
      {/* Price Range */}
      <div className="param-section">
        <h4>Price Range</h4>
        <div className="price-range">
          <input 
            type="number"
            value={minPrice}
            onChange={(e) => setMinPrice(parseInt(e.target.value) || 0)}
          />
          <span>to</span>
          <input 
            type="number"
            value={maxPrice}
            onChange={(e) => setMaxPrice(parseInt(e.target.value) || 0)}
          />
        </div>
      </div>
      
      {/* Location */}
      <div className="param-section">
        <h4>Search Radius</h4>
        <input 
          type="range"
          min="1"
          max="100"
          value={radius}
          onChange={(e) => setRadius(parseInt(e.target.value))}
        />
        <span>{radius} miles</span>
      </div>
      
      {/* Condition */}
      <div className="param-section">
        <h4>Condition</h4>
        <div className="condition-options">
          {['new', 'like-new', 'used', 'for-parts'].map(cond => (
            <label key={cond}>
              <input 
                type="checkbox"
                checked={conditions.includes(cond)}
                onChange={() => handleConditionToggle(cond)}
              />
              {cond}
            </label>
          ))}
        </div>
      </div>
      
      {/* Platform-specific options */}
      {platform === 'facebook' && (
        <div className="param-section">
          <h4>Facebook Options</h4>
          <select 
            value={fbOptions.sortBy}
            onChange={(e) => setFbOptions({...fbOptions, sortBy: e.target.value})}
          >
            <option value="relevance">Relevance</option>
            <option value="date">Date Listed</option>
            <option value="price-asc">Price: Low to High</option>
            <option value="price-desc">Price: High to Low</option>
          </select>
        </div>
      )}
      
      {/* Preview */}
      <div className="search-preview">
        <h4>Preview URL</h4>
        <code>{previewUrl}</code>
        <div className="preview-actions">
          <button onClick={handleTestSearch}>Test Search</button>
          <button onClick={handleCopyUrl}>Copy URL</button>
        </div>
      </div>
      
      {/* Actions */}
      <div className="builder-actions">
        <button onClick={onCancel}>Cancel</button>
        <button onClick={handleSave}>Save Search</button>
      </div>
    </div>
  );
}
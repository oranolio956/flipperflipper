/**
 * Message Composer Component
 * UI for composing messages with template support
 */

import React, { useState, useEffect, useRef } from 'react';
import { messageTemplateManager } from '@arbitrage/core';
import type { 
  MessageTemplate, 
  DraftMessage, 
  MessageContext,
  TemplateVariable 
} from '@arbitrage/core';

interface MessageComposerProps {
  context: MessageContext;
  onSend: (message: string, templateId?: string) => void;
  onCancel?: () => void;
}

export const MessageComposer: React.FC<MessageComposerProps> = ({
  context,
  onSend,
  onCancel
}) => {
  const [selectedCategory, setSelectedCategory] = useState<MessageTemplate['category']>('inquiry');
  const [draft, setDraft] = useState<DraftMessage | null>(null);
  const [editedMessage, setEditedMessage] = useState('');
  const [showTemplates, setShowTemplates] = useState(false);
  const [templates, setTemplates] = useState<MessageTemplate[]>([]);
  const [customVariables, setCustomVariables] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    loadTemplates();
    generateInitialDraft();
  }, [context, selectedCategory]);

  const loadTemplates = async () => {
    const allTemplates = messageTemplateManager.getAllTemplates();
    const filtered = allTemplates.filter(t => t.category === selectedCategory);
    setTemplates(filtered);
  };

  const generateInitialDraft = async () => {
    setLoading(true);
    try {
      const generatedDraft = await messageTemplateManager.generateDraft(context, selectedCategory);
      setDraft(generatedDraft);
      setEditedMessage(generatedDraft.preview);
      setCustomVariables(generatedDraft.variables);
    } catch (error) {
      console.error('Failed to generate draft:', error);
    }
    setLoading(false);
  };

  const handleTemplateSelect = async (template: MessageTemplate) => {
    setLoading(true);
    try {
      const newDraft = await messageTemplateManager.generateDraft(
        context,
        template.category
      );
      
      // Override with selected template
      newDraft.template = template;
      newDraft.preview = messageTemplateManager.renderTemplate(template, newDraft.variables);
      
      setDraft(newDraft);
      setEditedMessage(newDraft.preview);
      setCustomVariables(newDraft.variables);
      setShowTemplates(false);
    } catch (error) {
      console.error('Failed to apply template:', error);
    }
    setLoading(false);
  };

  const handleVariableChange = (name: string, value: any) => {
    const updatedVariables = { ...customVariables, [name]: value };
    setCustomVariables(updatedVariables);
    
    if (draft) {
      const newPreview = messageTemplateManager.renderTemplate(draft.template, updatedVariables);
      setEditedMessage(newPreview);
    }
  };

  const handleSend = () => {
    if (editedMessage.trim() && draft) {
      onSend(editedMessage, draft.template.id);
      
      // Track template usage
      messageTemplateManager.trackUsage(draft.template.id, true);
    }
  };

  const handleInsertSuggestion = (suggestion: string) => {
    if (textareaRef.current) {
      const pos = textareaRef.current.selectionStart;
      const newMessage = 
        editedMessage.slice(0, pos) + 
        '\n\n' + suggestion + '\n\n' + 
        editedMessage.slice(pos);
      setEditedMessage(newMessage);
    }
  };

  const getVariableInput = (variable: TemplateVariable) => {
    const value = customVariables[variable.name] || '';
    
    switch (variable.type) {
      case 'list':
        return (
          <select
            value={value}
            onChange={(e) => handleVariableChange(variable.name, e.target.value)}
            className="variable-input"
          >
            <option value="">Select...</option>
            {variable.options?.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        );
      
      case 'currency':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => handleVariableChange(variable.name, parseFloat(e.target.value))}
            className="variable-input currency"
            placeholder="0.00"
          />
        );
      
      case 'date':
        return (
          <input
            type="date"
            value={value}
            onChange={(e) => handleVariableChange(variable.name, e.target.value)}
            className="variable-input"
          />
        );
      
      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleVariableChange(variable.name, e.target.value)}
            className="variable-input"
            placeholder={variable.defaultValue || ''}
          />
        );
    }
  };

  return (
    <div className="message-composer">
      {/* Category Selector */}
      <div className="category-selector">
        {(['inquiry', 'offer', 'negotiation', 'closing', 'follow-up'] as const).map(category => (
          <button
            key={category}
            className={`category-btn ${selectedCategory === category ? 'active' : ''}`}
            onClick={() => setSelectedCategory(category)}
          >
            {category.charAt(0).toUpperCase() + category.slice(1)}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading">
          <div className="spinner"></div>
          <p>Generating draft...</p>
        </div>
      ) : (
        <>
          {/* Template Info */}
          {draft && (
            <div className="template-info">
              <div className="template-header">
                <h4>{draft.template.name}</h4>
                <button 
                  className="change-template-btn"
                  onClick={() => setShowTemplates(!showTemplates)}
                >
                  Change Template
                </button>
              </div>
              
              <div className="draft-meta">
                <span className={`tone-badge ${draft.tone}`}>
                  {draft.tone} tone
                </span>
                <span className="confidence">
                  {Math.round(draft.confidence * 100)}% confidence
                </span>
              </div>
            </div>
          )}

          {/* Template Browser */}
          {showTemplates && (
            <div className="template-browser">
              <h4>Available Templates</h4>
              <div className="template-list">
                {templates.map(template => (
                  <div 
                    key={template.id}
                    className="template-item"
                    onClick={() => handleTemplateSelect(template)}
                  >
                    <h5>{template.name}</h5>
                    <div className="template-tags">
                      {template.tags.map(tag => (
                        <span key={tag} className="tag">{tag}</span>
                      ))}
                    </div>
                    {template.successRate && (
                      <span className="success-rate">
                        {Math.round(template.successRate * 100)}% success
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Variables Editor */}
          {draft && draft.template.variables.length > 0 && (
            <div className="variables-editor">
              <h4>Customize Message</h4>
              <div className="variables-grid">
                {draft.template.variables.map(variable => (
                  <div key={variable.name} className="variable-field">
                    <label>
                      {variable.description}
                      {variable.required && <span className="required">*</span>}
                    </label>
                    {getVariableInput(variable)}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Message Editor */}
          <div className="message-editor">
            <textarea
              ref={textareaRef}
              value={editedMessage}
              onChange={(e) => setEditedMessage(e.target.value)}
              placeholder="Type your message..."
              rows={10}
            />
          </div>

          {/* Suggestions */}
          {draft && draft.suggestions.length > 0 && (
            <div className="suggestions">
              <h4>💡 Suggestions</h4>
              {draft.suggestions.map((suggestion, index) => (
                <div key={index} className="suggestion-item">
                  <p>{suggestion}</p>
                  <button
                    className="use-suggestion-btn"
                    onClick={() => handleInsertSuggestion(suggestion)}
                  >
                    Use
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Actions */}
          <div className="composer-actions">
            {onCancel && (
              <button className="cancel-btn" onClick={onCancel}>
                Cancel
              </button>
            )}
            <button 
              className="send-btn"
              onClick={handleSend}
              disabled={!editedMessage.trim()}
            >
              Send Message
            </button>
          </div>
        </>
      )}

      <style jsx>{`
        .message-composer {
          background: white;
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .category-selector {
          display: flex;
          gap: 8px;
          margin-bottom: 20px;
          border-bottom: 2px solid #e0e0e0;
          padding-bottom: 10px;
        }

        .category-btn {
          background: none;
          border: none;
          padding: 8px 16px;
          font-size: 14px;
          cursor: pointer;
          position: relative;
          transition: all 0.2s;
        }

        .category-btn.active {
          color: #2196f3;
        }

        .category-btn.active::after {
          content: '';
          position: absolute;
          bottom: -12px;
          left: 0;
          right: 0;
          height: 2px;
          background: #2196f3;
        }

        .loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 40px;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 3px solid #f3f3f3;
          border-top: 3px solid #2196f3;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 16px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .template-info {
          background: #f5f5f5;
          padding: 16px;
          border-radius: 8px;
          margin-bottom: 20px;
        }

        .template-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .template-header h4 {
          margin: 0;
          font-size: 16px;
        }

        .change-template-btn {
          background: none;
          border: 1px solid #ddd;
          padding: 6px 12px;
          border-radius: 4px;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .change-template-btn:hover {
          background: white;
          border-color: #2196f3;
        }

        .draft-meta {
          display: flex;
          gap: 12px;
          align-items: center;
        }

        .tone-badge {
          font-size: 12px;
          padding: 4px 10px;
          border-radius: 12px;
          background: #e3f2fd;
          color: #1976d2;
        }

        .tone-badge.casual {
          background: #f3e5f5;
          color: #7b1fa2;
        }

        .tone-badge.formal {
          background: #e0e0e0;
          color: #424242;
        }

        .tone-badge.friendly {
          background: #e8f5e9;
          color: #388e3c;
        }

        .confidence {
          font-size: 12px;
          color: #666;
        }

        .template-browser {
          background: #f9f9f9;
          padding: 16px;
          border-radius: 8px;
          margin-bottom: 20px;
        }

        .template-browser h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
        }

        .template-list {
          display: grid;
          gap: 10px;
        }

        .template-item {
          background: white;
          padding: 12px;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s;
          border: 1px solid #e0e0e0;
        }

        .template-item:hover {
          border-color: #2196f3;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .template-item h5 {
          margin: 0 0 8px 0;
          font-size: 14px;
        }

        .template-tags {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
        }

        .tag {
          font-size: 11px;
          padding: 2px 8px;
          background: #e0e0e0;
          border-radius: 10px;
        }

        .success-rate {
          font-size: 12px;
          color: #4caf50;
          float: right;
        }

        .variables-editor {
          background: #f9f9f9;
          padding: 16px;
          border-radius: 8px;
          margin-bottom: 20px;
        }

        .variables-editor h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
        }

        .variables-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 16px;
        }

        .variable-field {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .variable-field label {
          font-size: 13px;
          font-weight: 500;
        }

        .required {
          color: #f44336;
          margin-left: 4px;
        }

        .variable-input {
          padding: 8px 12px;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-size: 14px;
        }

        .variable-input.currency::before {
          content: '$';
          position: absolute;
          left: 8px;
          top: 50%;
          transform: translateY(-50%);
        }

        .message-editor {
          margin-bottom: 20px;
        }

        .message-editor textarea {
          width: 100%;
          padding: 16px;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 14px;
          line-height: 1.5;
          resize: vertical;
          font-family: inherit;
        }

        .message-editor textarea:focus {
          outline: none;
          border-color: #2196f3;
          box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
        }

        .suggestions {
          background: #e3f2fd;
          padding: 16px;
          border-radius: 8px;
          margin-bottom: 20px;
        }

        .suggestions h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
        }

        .suggestion-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid rgba(0,0,0,0.1);
        }

        .suggestion-item:last-child {
          border-bottom: none;
        }

        .suggestion-item p {
          margin: 0;
          font-size: 13px;
          flex: 1;
        }

        .use-suggestion-btn {
          background: #2196f3;
          color: white;
          border: none;
          padding: 4px 12px;
          border-radius: 4px;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .use-suggestion-btn:hover {
          background: #1976d2;
        }

        .composer-actions {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
        }

        .cancel-btn {
          background: #f5f5f5;
          border: none;
          padding: 10px 20px;
          border-radius: 6px;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .cancel-btn:hover {
          background: #e0e0e0;
        }

        .send-btn {
          background: #2196f3;
          color: white;
          border: none;
          padding: 10px 24px;
          border-radius: 6px;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .send-btn:hover:not(:disabled) {
          background: #1976d2;
        }

        .send-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
};
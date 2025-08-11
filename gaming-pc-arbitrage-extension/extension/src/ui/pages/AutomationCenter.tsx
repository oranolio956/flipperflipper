import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  Plus, 
  Play, 
  Pause, 
  Clock, 
  Globe, 
  Settings,
  Trash2,
  Edit,
  CheckCircle,
  AlertCircle,
  Info,
  ExternalLink
} from 'lucide-react';
import { PageHeader } from '../design/components/PageHeader';
import { Card, CardHeader, CardContent } from '../design/components/Card';
import { Button } from '../design/components/Button';
import { EmptyState, LoadingState } from '../design/components/EmptyState';
import { showToast } from '../design/components/Toast';
import { formatRelativeTime } from '../lib/utils';
import { savedSearchesManager, SavedSearch, AutomationSettings } from '../../lib/automation/savedSearches';

export function AutomationCenter() {
  const [loading, setLoading] = useState(true);
  const [searches, setSearches] = useState<SavedSearch[]>([]);
  const [settings, setSettings] = useState<AutomationSettings | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingSearch, setEditingSearch] = useState<SavedSearch | null>(null);
  const [automationStatus, setAutomationStatus] = useState<any>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    cadenceMinutes: 30,
    enabled: true,
  });

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [savedSearches, automationSettings] = await Promise.all([
        savedSearchesManager.getAll(),
        savedSearchesManager.getSettings(),
      ]);

      // Get automation status from background
      const status = await chrome.runtime.sendMessage({ action: 'getAutomationStatus' });

      setSearches(savedSearches);
      setSettings(automationSettings);
      setAutomationStatus(status);
    } catch (error) {
      console.error('Failed to load automation data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAutomation = async () => {
    if (!settings) return;

    try {
      const newSettings = await savedSearchesManager.updateSettings({
        enabled: !settings.enabled,
      });
      setSettings(newSettings);
      
      showToast({
        type: 'success',
        title: newSettings.enabled ? 'Automation Enabled' : 'Automation Disabled',
        description: newSettings.enabled 
          ? 'Saved searches will be scanned automatically'
          : 'Automatic scanning has been paused',
      });
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Failed to update automation',
        description: error.message,
      });
    }
  };

  const handleAddSearch = async () => {
    const validation = savedSearchesManager.validateSearchUrl(formData.url);
    if (!validation.valid) {
      showToast({
        type: 'error',
        title: 'Invalid URL',
        description: validation.error,
      });
      return;
    }

    try {
      if (editingSearch) {
        await savedSearchesManager.update(editingSearch.id, formData);
        showToast({
          type: 'success',
          title: 'Search Updated',
          description: 'Your saved search has been updated',
        });
      } else {
        await savedSearchesManager.create({
          ...formData,
          platform: validation.platform!,
          filters: {},
        });
        showToast({
          type: 'success',
          title: 'Search Added',
          description: 'Your search will be scanned automatically',
        });
      }

      setFormData({ name: '', url: '', cadenceMinutes: 30, enabled: true });
      setShowAddForm(false);
      setEditingSearch(null);
      loadData();
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Failed to save search',
        description: error.message,
      });
    }
  };

  const handleDeleteSearch = async (id: string) => {
    if (!confirm('Are you sure you want to delete this saved search?')) return;

    try {
      await savedSearchesManager.delete(id);
      showToast({
        type: 'success',
        title: 'Search Deleted',
        description: 'The saved search has been removed',
      });
      loadData();
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Failed to delete search',
        description: error.message,
      });
    }
  };

  const handleToggleSearch = async (search: SavedSearch) => {
    try {
      await savedSearchesManager.update(search.id, {
        enabled: !search.enabled,
      });
      loadData();
    } catch (error) {
      showToast({
        type: 'error',
        title: 'Failed to update search',
        description: error.message,
      });
    }
  };

  const helpContent = (
    <div className="help-content">
      <h4>Max Auto Engine</h4>
      <p>Automate your marketplace scanning with saved searches that run on a schedule.</p>
      
      <h4>How it works:</h4>
      <ul>
        <li>Add marketplace search URLs you want to monitor</li>
        <li>Set how often each search should run (cadence)</li>
        <li>Extension opens tabs in background and scans results</li>
        <li>New candidates are added to your pipeline automatically</li>
      </ul>
      
      <h4>Compliance Note:</h4>
      <p>This feature opens tabs and scans pages you could visit manually. It does not send automated messages or perform actions without your consent.</p>
    </div>
  );

  if (loading) {
    return <LoadingState message="Loading automation settings..." />;
  }

  return (
    <div className="automation-page">
      <PageHeader
        title="Automation Center"
        description="Max Auto controls and saved search management"
        helpContent={helpContent}
        actions={
          <div className="automation-actions">
            <Button
              variant={settings?.enabled ? 'danger' : 'primary'}
              icon={settings?.enabled ? <Pause size={16} /> : <Play size={16} />}
              onClick={handleToggleAutomation}
            >
              {settings?.enabled ? 'Disable Automation' : 'Enable Automation'}
            </Button>
          </div>
        }
      />

      {/* Status Overview */}
      <Card variant="elevated" className="automation-status-card">
        <CardContent>
          <div className="status-grid">
            <div className="status-item">
              <div className="status-icon">
                {settings?.enabled ? (
                  <CheckCircle className="text-success" />
                ) : (
                  <AlertCircle className="text-warning" />
                )}
              </div>
              <div className="status-info">
                <h3>Automation Status</h3>
                <p>{settings?.enabled ? 'Active' : 'Paused'}</p>
              </div>
            </div>

            <div className="status-item">
              <div className="status-icon">
                <Zap />
              </div>
              <div className="status-info">
                <h3>Active Searches</h3>
                <p>{searches.filter(s => s.enabled).length} of {searches.length}</p>
              </div>
            </div>

            <div className="status-item">
              <div className="status-icon">
                <Globe />
              </div>
              <div className="status-info">
                <h3>Open Tabs</h3>
                <p>{automationStatus?.activeTabs || 0} / {settings?.maxTabsOpen || 3}</p>
              </div>
            </div>

            <div className="status-item">
              <div className="status-icon">
                <Clock />
              </div>
              <div className="status-info">
                <h3>In Queue</h3>
                <p>{automationStatus?.queueLength || 0} searches</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Saved Searches */}
      <Card>
        <CardHeader
          title="Saved Searches"
          description="Marketplace searches that run automatically"
          action={
            <Button
              variant="primary"
              size="sm"
              icon={<Plus size={16} />}
              onClick={() => {
                setEditingSearch(null);
                setFormData({ name: '', url: '', cadenceMinutes: 30, enabled: true });
                setShowAddForm(true);
              }}
            >
              Add Search
            </Button>
          }
        />
        <CardContent>
          {searches.length === 0 && !showAddForm ? (
            <EmptyState
              icon={Zap}
              title="No saved searches"
              description="Add marketplace searches to scan automatically"
              action={{
                label: 'Add Your First Search',
                onClick: () => setShowAddForm(true),
              }}
            />
          ) : (
            <>
              {showAddForm && (
                <div className="search-form">
                  <div className="form-group">
                    <label>Search Name</label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="e.g., Gaming PCs under $1000"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Search URL</label>
                    <input
                      type="url"
                      value={formData.url}
                      onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                      placeholder="Paste Facebook Marketplace, Craigslist, or OfferUp search URL"
                    />
                    <p className="form-help">
                      Go to the marketplace, set your filters, then copy the URL
                    </p>
                  </div>

                  <div className="form-group">
                    <label>Scan Every</label>
                    <select
                      value={formData.cadenceMinutes}
                      onChange={(e) => setFormData({ ...formData, cadenceMinutes: parseInt(e.target.value) })}
                    >
                      <option value={15}>15 minutes</option>
                      <option value={30}>30 minutes</option>
                      <option value={60}>1 hour</option>
                      <option value={120}>2 hours</option>
                      <option value={360}>6 hours</option>
                      <option value={720}>12 hours</option>
                      <option value={1440}>24 hours</option>
                    </select>
                  </div>

                  <div className="form-actions">
                    <Button
                      variant="secondary"
                      onClick={() => {
                        setShowAddForm(false);
                        setEditingSearch(null);
                      }}
                    >
                      Cancel
                    </Button>
                    <Button
                      variant="primary"
                      onClick={handleAddSearch}
                      disabled={!formData.name || !formData.url}
                    >
                      {editingSearch ? 'Update Search' : 'Add Search'}
                    </Button>
                  </div>
                </div>
              )}

              <div className="searches-list">
                {searches.map((search) => (
                  <div key={search.id} className="search-item">
                    <div className="search-header">
                      <div className="search-info">
                        <h4>{search.name}</h4>
                        <div className="search-meta">
                          <span className="platform">{search.platform}</span>
                          <span className="separator">•</span>
                          <span>Every {search.cadenceMinutes < 60 ? `${search.cadenceMinutes}m` : `${search.cadenceMinutes / 60}h`}</span>
                          {search.lastScanned && (
                            <>
                              <span className="separator">•</span>
                              <span>Last: {formatRelativeTime(search.lastScanned)}</span>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="search-actions">
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={search.enabled ? <Pause size={14} /> : <Play size={14} />}
                          onClick={() => handleToggleSearch(search)}
                        >
                          {search.enabled ? 'Pause' : 'Resume'}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Edit size={14} />}
                          onClick={() => {
                            setEditingSearch(search);
                            setFormData({
                              name: search.name,
                              url: search.url,
                              cadenceMinutes: search.cadenceMinutes,
                              enabled: search.enabled,
                            });
                            setShowAddForm(true);
                          }}
                        >
                          Edit
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          icon={<Trash2 size={14} />}
                          onClick={() => handleDeleteSearch(search.id)}
                        >
                          Delete
                        </Button>
                      </div>
                    </div>
                    <div className="search-url">
                      <a href={search.url} target="_blank" rel="noopener noreferrer">
                        {search.url}
                        <ExternalLink size={12} />
                      </a>
                    </div>
                    {search.nextScan && search.enabled && (
                      <div className="search-next">
                        Next scan: {formatRelativeTime(search.nextScan)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Settings */}
      <Card>
        <CardHeader
          title="Automation Settings"
          description="Configure how Max Auto operates"
          action={
            <Info size={16} className="text-tertiary" />
          }
        />
        <CardContent>
          <div className="settings-list">
            <div className="setting-item">
              <div className="setting-info">
                <h4>Max Tabs Open</h4>
                <p>Maximum number of tabs to open simultaneously</p>
              </div>
              <select
                value={settings?.maxTabsOpen || 3}
                onChange={async (e) => {
                  const value = parseInt(e.target.value);
                  const updated = await savedSearchesManager.updateSettings({ maxTabsOpen: value });
                  setSettings(updated);
                }}
              >
                {[1, 2, 3, 5, 10].map(n => (
                  <option key={n} value={n}>{n} tab{n > 1 ? 's' : ''}</option>
                ))}
              </select>
            </div>

            <div className="setting-item">
              <div className="setting-info">
                <h4>Close Tabs After Scan</h4>
                <p>Automatically close tabs when scanning completes</p>
              </div>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={settings?.closeTabsAfterScan ?? true}
                  onChange={async (e) => {
                    const updated = await savedSearchesManager.updateSettings({ 
                      closeTabsAfterScan: e.target.checked 
                    });
                    setSettings(updated);
                  }}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            <div className="setting-item">
              <div className="setting-info">
                <h4>Notify on New Finds</h4>
                <p>Show notifications when new candidates are found</p>
              </div>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={settings?.notifyOnNewFinds ?? true}
                  onChange={async (e) => {
                    const updated = await savedSearchesManager.updateSettings({ 
                      notifyOnNewFinds: e.target.checked 
                    });
                    setSettings(updated);
                  }}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>

            <div className="setting-item">
              <div className="setting-info">
                <h4>Pause During Active Use</h4>
                <p>Pause scanning when you're actively using the browser</p>
              </div>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={settings?.pauseDuringActiveUse ?? true}
                  onChange={async (e) => {
                    const updated = await savedSearchesManager.updateSettings({ 
                      pauseDuringActiveUse: e.target.checked 
                    });
                    setSettings(updated);
                  }}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
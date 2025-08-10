/**
 * Meetup Scheduler UI Component
 * Interface for scheduling and managing meetups with calendar integration
 */

import React, { useState, useEffect } from 'react';
import { meetupScheduler } from '@arbitrage/core';
import type { 
  MeetupDetails, 
  MeetupLocation, 
  CalendarExport 
} from '@arbitrage/core';
import { Deal, Listing } from '@arbitrage/core';

interface MeetupSchedulerUIProps {
  deal?: Deal;
  listing?: Listing;
  onClose?: () => void;
}

export const MeetupSchedulerUI: React.FC<MeetupSchedulerUIProps> = ({
  deal,
  listing,
  onClose
}) => {
  const [activeTab, setActiveTab] = useState<'schedule' | 'upcoming' | 'locations'>('schedule');
  const [meetups, setMeetups] = useState<MeetupDetails[]>([]);
  const [locations, setLocations] = useState<MeetupLocation[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<MeetupLocation | null>(null);
  const [formData, setFormData] = useState({
    date: '',
    time: '',
    duration: 30,
    partyName: '',
    partyPhone: '',
    partyEmail: '',
    notes: '',
    reminder: 30
  });
  const [showAddLocation, setShowAddLocation] = useState(false);
  const [newLocation, setNewLocation] = useState<Partial<MeetupLocation>>({
    name: '',
    address: '',
    type: 'public' as const,
    safetyRating: 3
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const upcomingMeetups = meetupScheduler.getUpcomingMeetups(30);
    setMeetups(upcomingMeetups);

    const safeLocations = meetupScheduler.getSafeLocations();
    setLocations(safeLocations);

    // Suggest locations if listing available
    if (listing) {
      const suggested = meetupScheduler.suggestLocations(listing);
      if (suggested.length > 0 && !selectedLocation) {
        setSelectedLocation(suggested[0]);
      }
    }
  };

  const handleScheduleMeetup = async () => {
    if (!deal || !listing || !selectedLocation) {
      alert('Missing required information');
      return;
    }

    const meetupDate = new Date(`${formData.date}T${formData.time}`);
    
    try {
      const meetup = await meetupScheduler.scheduleMeetup(deal, listing, {
        date: meetupDate,
        duration: formData.duration,
        location: selectedLocation,
        party: {
          name: formData.partyName,
          phone: formData.partyPhone || undefined,
          email: formData.partyEmail || undefined
        },
        notes: formData.notes || undefined,
        reminder: formData.reminder || undefined
      });

      // Download ICS file
      const icsExport = meetupScheduler.generateICS(meetup.id);
      if (icsExport) {
        downloadICS(icsExport);
      }

      await loadData();
      resetForm();
      
      chrome.notifications.create({
        type: 'basic',
        iconUrl: chrome.runtime.getURL('icons/icon-48.png'),
        title: 'Meetup Scheduled',
        message: `Meeting scheduled for ${meetupDate.toLocaleString()}`
      });
    } catch (error) {
      console.error('Failed to schedule meetup:', error);
    }
  };

  const handleAddLocation = async () => {
    if (!newLocation.name || !newLocation.address) {
      alert('Please fill in all required fields');
      return;
    }

    await meetupScheduler.addSafeLocation(newLocation as MeetupLocation);
    await loadData();
    setShowAddLocation(false);
    setNewLocation({
      name: '',
      address: '',
      type: 'public',
      safetyRating: 3
    });
  };

  const handleExportAll = () => {
    const export_data = meetupScheduler.generateMultipleICS();
    if (export_data.eventCount > 0) {
      downloadICS(export_data);
    } else {
      alert('No meetups to export');
    }
  };

  const handleUpdateStatus = async (meetupId: string, status: MeetupDetails['status']) => {
    await meetupScheduler.updateMeetupStatus(meetupId, status);
    await loadData();
  };

  const downloadICS = (icsExport: CalendarExport) => {
    const blob = new Blob([icsExport.icsContent], { type: 'text/calendar' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = icsExport.fileName;
    a.click();
    URL.revokeObjectURL(url);
  };

  const resetForm = () => {
    setFormData({
      date: '',
      time: '',
      duration: 30,
      partyName: '',
      partyPhone: '',
      partyEmail: '',
      notes: '',
      reminder: 30
    });
  };

  const getSafetyTips = () => {
    if (!listing) return [];
    
    const tips = [];
    if (listing.price > 1000) {
      tips.push('💰 High-value item - meet at police station if possible');
    }
    tips.push('👥 Bring a friend for safety');
    tips.push('📱 Share location with someone you trust');
    tips.push('🔌 Bring cables to test the system');
    tips.push('💵 Count cash carefully, check for counterfeits');
    return tips;
  };

  return (
    <div className="meetup-scheduler">
      <div className="scheduler-header">
        <h2>Meetup Scheduler</h2>
        {onClose && (
          <button className="close-btn" onClick={onClose}>×</button>
        )}
      </div>

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'schedule' ? 'active' : ''}`}
          onClick={() => setActiveTab('schedule')}
        >
          Schedule New
        </button>
        <button 
          className={`tab ${activeTab === 'upcoming' ? 'active' : ''}`}
          onClick={() => setActiveTab('upcoming')}
        >
          Upcoming ({meetups.length})
        </button>
        <button 
          className={`tab ${activeTab === 'locations' ? 'active' : ''}`}
          onClick={() => setActiveTab('locations')}
        >
          Safe Locations
        </button>
      </div>

      {activeTab === 'schedule' && (
        <div className="schedule-form">
          {listing && (
            <div className="listing-info">
              <h4>Scheduling meetup for:</h4>
              <p>{listing.title}</p>
              <p className="price">${listing.price}</p>
            </div>
          )}

          <div className="form-section">
            <h4>Date & Time</h4>
            <div className="form-row">
              <div className="form-field">
                <label>Date</label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({...formData, date: e.target.value})}
                  min={new Date().toISOString().split('T')[0]}
                />
              </div>
              <div className="form-field">
                <label>Time</label>
                <input
                  type="time"
                  value={formData.time}
                  onChange={(e) => setFormData({...formData, time: e.target.value})}
                />
              </div>
              <div className="form-field">
                <label>Duration (min)</label>
                <input
                  type="number"
                  value={formData.duration}
                  onChange={(e) => setFormData({...formData, duration: parseInt(e.target.value)})}
                  min="15"
                  max="120"
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h4>Location</h4>
            {locations.length > 0 ? (
              <div className="location-grid">
                {locations.map(location => (
                  <div 
                    key={`${location.name}-${location.address}`}
                    className={`location-card ${selectedLocation === location ? 'selected' : ''}`}
                    onClick={() => setSelectedLocation(location)}
                  >
                    <h5>{location.name}</h5>
                    <p>{location.address}</p>
                    <div className="location-meta">
                      <span className="type">{location.type}</span>
                      <span className="rating">{'⭐'.repeat(location.safetyRating || 0)}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p>No safe locations added yet</p>
            )}
          </div>

          <div className="form-section">
            <h4>Other Party Details</h4>
            <div className="form-field">
              <label>Name <span className="required">*</span></label>
              <input
                type="text"
                value={formData.partyName}
                onChange={(e) => setFormData({...formData, partyName: e.target.value})}
                placeholder="Seller/Buyer name"
              />
            </div>
            <div className="form-row">
              <div className="form-field">
                <label>Phone</label>
                <input
                  type="tel"
                  value={formData.partyPhone}
                  onChange={(e) => setFormData({...formData, partyPhone: e.target.value})}
                  placeholder="Optional"
                />
              </div>
              <div className="form-field">
                <label>Email</label>
                <input
                  type="email"
                  value={formData.partyEmail}
                  onChange={(e) => setFormData({...formData, partyEmail: e.target.value})}
                  placeholder="Optional"
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h4>Additional Details</h4>
            <div className="form-field">
              <label>Notes</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({...formData, notes: e.target.value})}
                placeholder="Any special instructions or reminders"
                rows={3}
              />
            </div>
            <div className="form-field">
              <label>Reminder (minutes before)</label>
              <select
                value={formData.reminder}
                onChange={(e) => setFormData({...formData, reminder: parseInt(e.target.value)})}
              >
                <option value="0">No reminder</option>
                <option value="15">15 minutes</option>
                <option value="30">30 minutes</option>
                <option value="60">1 hour</option>
                <option value="120">2 hours</option>
              </select>
            </div>
          </div>

          <div className="safety-tips">
            <h4>🛡️ Safety Tips</h4>
            <ul>
              {getSafetyTips().map((tip, index) => (
                <li key={index}>{tip}</li>
              ))}
            </ul>
          </div>

          <div className="form-actions">
            <button 
              className="schedule-btn"
              onClick={handleScheduleMeetup}
              disabled={!formData.date || !formData.time || !formData.partyName || !selectedLocation}
            >
              Schedule & Download Calendar Event
            </button>
          </div>
        </div>
      )}

      {activeTab === 'upcoming' && (
        <div className="upcoming-meetups">
          <div className="meetups-header">
            <h3>Upcoming Meetups</h3>
            <button className="export-all-btn" onClick={handleExportAll}>
              📅 Export All to Calendar
            </button>
          </div>

          {meetups.length === 0 ? (
            <div className="empty-state">
              <p>No upcoming meetups scheduled</p>
            </div>
          ) : (
            <div className="meetup-list">
              {meetups.map(meetup => (
                <div key={meetup.id} className="meetup-card">
                  <div className="meetup-header">
                    <h4>{meetup.listing.title}</h4>
                    <span className={`status ${meetup.status}`}>{meetup.status}</span>
                  </div>
                  
                  <div className="meetup-details">
                    <div className="detail-row">
                      <span className="icon">📅</span>
                      <span>{new Date(meetup.date).toLocaleString()}</span>
                    </div>
                    <div className="detail-row">
                      <span className="icon">📍</span>
                      <span>{meetup.location.name}</span>
                    </div>
                    <div className="detail-row">
                      <span className="icon">👤</span>
                      <span>{meetup.party.name}</span>
                    </div>
                    <div className="detail-row">
                      <span className="icon">💵</span>
                      <span>${meetup.listing.price}</span>
                    </div>
                  </div>

                  <div className="meetup-actions">
                    {meetup.status === 'scheduled' && (
                      <button 
                        className="confirm-btn"
                        onClick={() => handleUpdateStatus(meetup.id, 'confirmed')}
                      >
                        Confirm
                      </button>
                    )}
                    <button
                      className="download-btn"
                      onClick={() => {
                        const ics = meetupScheduler.generateICS(meetup.id);
                        if (ics) downloadICS(ics);
                      }}
                    >
                      📥 ICS
                    </button>
                    <button
                      className="complete-btn"
                      onClick={() => handleUpdateStatus(meetup.id, 'completed')}
                    >
                      ✓ Complete
                    </button>
                    <button
                      className="cancel-btn"
                      onClick={() => handleUpdateStatus(meetup.id, 'cancelled')}
                    >
                      Cancel
                    </button>
                  </div>

                  {meetup.notes && (
                    <div className="meetup-notes">
                      <strong>Notes:</strong> {meetup.notes}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'locations' && (
        <div className="locations-manager">
          <div className="locations-header">
            <h3>Safe Meeting Locations</h3>
            <button 
              className="add-location-btn"
              onClick={() => setShowAddLocation(!showAddLocation)}
            >
              + Add Location
            </button>
          </div>

          {showAddLocation && (
            <div className="add-location-form">
              <h4>Add New Safe Location</h4>
              <div className="form-field">
                <label>Location Name</label>
                <input
                  type="text"
                  value={newLocation.name}
                  onChange={(e) => setNewLocation({...newLocation, name: e.target.value})}
                  placeholder="e.g., Starbucks on Main St"
                />
              </div>
              <div className="form-field">
                <label>Address</label>
                <input
                  type="text"
                  value={newLocation.address}
                  onChange={(e) => setNewLocation({...newLocation, address: e.target.value})}
                  placeholder="Full address"
                />
              </div>
              <div className="form-row">
                <div className="form-field">
                  <label>Type</label>
                  <select
                    value={newLocation.type}
                    onChange={(e) => setNewLocation({...newLocation, type: e.target.value as any})}
                  >
                    <option value="public">Public Space</option>
                    <option value="police-station">Police Station</option>
                    <option value="bank">Bank</option>
                    <option value="store">Store/Mall</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="form-field">
                  <label>Safety Rating</label>
                  <select
                    value={newLocation.safetyRating}
                    onChange={(e) => setNewLocation({...newLocation, safetyRating: parseInt(e.target.value)})}
                  >
                    <option value="5">⭐⭐⭐⭐⭐ Excellent</option>
                    <option value="4">⭐⭐⭐⭐ Very Good</option>
                    <option value="3">⭐⭐⭐ Good</option>
                    <option value="2">⭐⭐ Fair</option>
                    <option value="1">⭐ Poor</option>
                  </select>
                </div>
              </div>
              <div className="form-actions">
                <button className="save-btn" onClick={handleAddLocation}>
                  Save Location
                </button>
                <button className="cancel-btn" onClick={() => setShowAddLocation(false)}>
                  Cancel
                </button>
              </div>
            </div>
          )}

          <div className="locations-list">
            {locations.map((location, index) => (
              <div key={index} className="location-item">
                <div className="location-info">
                  <h5>{location.name}</h5>
                  <p>{location.address}</p>
                  <div className="location-meta">
                    <span className="type">{location.type}</span>
                    <span className="rating">{'⭐'.repeat(location.safetyRating || 0)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <style jsx>{`
        .meetup-scheduler {
          background: white;
          border-radius: 12px;
          padding: 24px;
          max-width: 800px;
          margin: 0 auto;
        }

        .scheduler-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }

        .scheduler-header h2 {
          margin: 0;
          font-size: 24px;
        }

        .close-btn {
          background: none;
          border: none;
          font-size: 24px;
          cursor: pointer;
          width: 40px;
          height: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 4px;
        }

        .close-btn:hover {
          background: #f5f5f5;
        }

        .tabs {
          display: flex;
          gap: 0;
          margin-bottom: 24px;
          border-bottom: 2px solid #e0e0e0;
        }

        .tab {
          background: none;
          border: none;
          padding: 12px 24px;
          font-size: 14px;
          cursor: pointer;
          position: relative;
        }

        .tab.active {
          color: #2196f3;
        }

        .tab.active::after {
          content: '';
          position: absolute;
          bottom: -2px;
          left: 0;
          right: 0;
          height: 2px;
          background: #2196f3;
        }

        .listing-info {
          background: #f5f5f5;
          padding: 16px;
          border-radius: 8px;
          margin-bottom: 24px;
        }

        .listing-info h4 {
          margin: 0 0 8px 0;
          font-size: 14px;
          color: #666;
        }

        .listing-info p {
          margin: 4px 0;
        }

        .listing-info .price {
          font-size: 20px;
          font-weight: 600;
          color: #2196f3;
        }

        .form-section {
          margin-bottom: 24px;
        }

        .form-section h4 {
          margin: 0 0 16px 0;
          font-size: 16px;
        }

        .form-row {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 16px;
        }

        .form-field {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .form-field label {
          font-size: 14px;
          font-weight: 500;
        }

        .required {
          color: #f44336;
        }

        .form-field input,
        .form-field select,
        .form-field textarea {
          padding: 10px 12px;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-size: 14px;
        }

        .location-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
          gap: 12px;
        }

        .location-card {
          border: 2px solid #e0e0e0;
          border-radius: 8px;
          padding: 16px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .location-card:hover {
          border-color: #2196f3;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .location-card.selected {
          border-color: #2196f3;
          background: #e3f2fd;
        }

        .location-card h5 {
          margin: 0 0 8px 0;
          font-size: 14px;
        }

        .location-card p {
          margin: 0 0 8px 0;
          font-size: 12px;
          color: #666;
        }

        .location-meta {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .location-meta .type {
          font-size: 11px;
          padding: 2px 8px;
          background: #e0e0e0;
          border-radius: 12px;
        }

        .safety-tips {
          background: #e3f2fd;
          padding: 16px;
          border-radius: 8px;
          margin-bottom: 24px;
        }

        .safety-tips h4 {
          margin: 0 0 12px 0;
          font-size: 16px;
        }

        .safety-tips ul {
          margin: 0;
          padding-left: 20px;
        }

        .safety-tips li {
          margin: 8px 0;
          font-size: 14px;
        }

        .form-actions {
          display: flex;
          justify-content: flex-end;
          gap: 12px;
        }

        .schedule-btn {
          background: #2196f3;
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 6px;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .schedule-btn:hover:not(:disabled) {
          background: #1976d2;
        }

        .schedule-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .meetups-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .meetups-header h3 {
          margin: 0;
          font-size: 18px;
        }

        .export-all-btn {
          background: #4caf50;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 6px;
          font-size: 14px;
          cursor: pointer;
        }

        .empty-state {
          text-align: center;
          padding: 60px 20px;
          color: #666;
        }

        .meetup-list {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .meetup-card {
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          padding: 20px;
          transition: all 0.2s;
        }

        .meetup-card:hover {
          box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .meetup-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 16px;
        }

        .meetup-header h4 {
          margin: 0;
          font-size: 16px;
        }

        .status {
          font-size: 12px;
          padding: 4px 12px;
          border-radius: 12px;
          text-transform: uppercase;
        }

        .status.scheduled {
          background: #fff3e0;
          color: #e65100;
        }

        .status.confirmed {
          background: #e8f5e9;
          color: #2e7d32;
        }

        .status.completed {
          background: #e0e0e0;
          color: #616161;
        }

        .status.cancelled {
          background: #ffebee;
          color: #c62828;
        }

        .meetup-details {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 12px;
          margin-bottom: 16px;
        }

        .detail-row {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
        }

        .detail-row .icon {
          font-size: 16px;
        }

        .meetup-actions {
          display: flex;
          gap: 8px;
        }

        .meetup-actions button {
          padding: 6px 12px;
          border: none;
          border-radius: 4px;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .confirm-btn {
          background: #4caf50;
          color: white;
        }

        .download-btn {
          background: #2196f3;
          color: white;
        }

        .complete-btn {
          background: #9e9e9e;
          color: white;
        }

        .cancel-btn {
          background: #f44336;
          color: white;
        }

        .meetup-notes {
          margin-top: 12px;
          padding-top: 12px;
          border-top: 1px solid #e0e0e0;
          font-size: 13px;
          color: #666;
        }

        .locations-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .locations-header h3 {
          margin: 0;
          font-size: 18px;
        }

        .add-location-btn {
          background: #2196f3;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 6px;
          font-size: 14px;
          cursor: pointer;
        }

        .add-location-form {
          background: #f5f5f5;
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 20px;
        }

        .add-location-form h4 {
          margin: 0 0 16px 0;
          font-size: 16px;
        }

        .save-btn {
          background: #4caf50;
          color: white;
          border: none;
          padding: 8px 16px;
          border-radius: 6px;
          font-size: 14px;
          cursor: pointer;
        }

        .locations-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .location-item {
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          padding: 16px;
        }

        .location-info h5 {
          margin: 0 0 8px 0;
          font-size: 16px;
        }

        .location-info p {
          margin: 0 0 8px 0;
          color: #666;
          font-size: 14px;
        }
      `}</style>
    </div>
  );
};
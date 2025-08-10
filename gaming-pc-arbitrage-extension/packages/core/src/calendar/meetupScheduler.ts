/**
 * Meetup Scheduler with Calendar Integration
 * Generates ICS files for meetup scheduling
 */

import ical, { ICalCalendar, ICalEvent } from 'ical-generator';
import { Deal, Listing } from '../types';

export interface MeetupDetails {
  id: string;
  dealId: string;
  listing: Listing;
  date: Date;
  duration: number; // minutes
  location: MeetupLocation;
  party: {
    name: string;
    phone?: string;
    email?: string;
  };
  notes?: string;
  reminder?: number; // minutes before
  status: 'scheduled' | 'confirmed' | 'completed' | 'cancelled';
  createdAt: Date;
  updatedAt: Date;
}

export interface MeetupLocation {
  name: string;
  address: string;
  latitude?: number;
  longitude?: number;
  type: 'public' | 'police-station' | 'bank' | 'store' | 'other';
  safetyRating?: number; // 1-5
}

export interface CalendarExport {
  icsContent: string;
  fileName: string;
  eventCount: number;
}

export class MeetupScheduler {
  private meetups: Map<string, MeetupDetails> = new Map();
  private safeLocations: MeetupLocation[] = [];
  private readonly STORAGE_KEY = 'meetupSchedule';
  private readonly LOCATIONS_KEY = 'safeLocations';

  constructor() {
    this.loadData();
    this.initializeDefaultLocations();
  }

  /**
   * Initialize with default safe locations
   */
  private initializeDefaultLocations(): void {
    const defaults: Omit<MeetupLocation, 'latitude' | 'longitude'>[] = [
      {
        name: 'Local Police Station Parking Lot',
        address: 'Check your local police station',
        type: 'police-station',
        safetyRating: 5
      },
      {
        name: 'Bank Parking Lot (During Hours)',
        address: 'Any major bank with cameras',
        type: 'bank',
        safetyRating: 5
      },
      {
        name: 'Busy Shopping Center',
        address: 'Well-lit shopping center with security',
        type: 'store',
        safetyRating: 4
      },
      {
        name: 'Public Library',
        address: 'Local public library during hours',
        type: 'public',
        safetyRating: 4
      }
    ];

    defaults.forEach(location => {
      this.addSafeLocation(location as MeetupLocation);
    });
  }

  /**
   * Schedule a new meetup
   */
  async scheduleMeetup(
    deal: Deal,
    listing: Listing,
    details: {
      date: Date;
      duration?: number;
      location: MeetupLocation;
      party: MeetupDetails['party'];
      notes?: string;
      reminder?: number;
    }
  ): Promise<MeetupDetails> {
    const meetup: MeetupDetails = {
      id: `meetup_${Date.now()}`,
      dealId: deal.id,
      listing,
      date: details.date,
      duration: details.duration || 30,
      location: details.location,
      party: details.party,
      notes: details.notes,
      reminder: details.reminder || 30,
      status: 'scheduled',
      createdAt: new Date(),
      updatedAt: new Date()
    };

    this.meetups.set(meetup.id, meetup);
    await this.saveData();

    // Set reminder if requested
    if (meetup.reminder) {
      this.scheduleReminder(meetup);
    }

    return meetup;
  }

  /**
   * Generate ICS file for a single meetup
   */
  generateICS(meetupId: string): CalendarExport | null {
    const meetup = this.meetups.get(meetupId);
    if (!meetup) return null;

    const calendar = ical({ name: 'Gaming PC Arbitrage Meetup' });
    
    const event = this.createCalendarEvent(meetup);
    calendar.createEvent(event);

    return {
      icsContent: calendar.toString(),
      fileName: `meetup_${meetup.listing.title.replace(/[^a-z0-9]/gi, '_')}_${meetup.date.toISOString().split('T')[0]}.ics`,
      eventCount: 1
    };
  }

  /**
   * Generate ICS file for multiple meetups
   */
  generateMultipleICS(
    meetupIds?: string[],
    dateRange?: { start: Date; end: Date }
  ): CalendarExport {
    const calendar = ical({ 
      name: 'Gaming PC Arbitrage Meetups',
      description: 'All scheduled meetups for PC deals'
    });

    let meetupsToExport = Array.from(this.meetups.values());

    // Filter by IDs if provided
    if (meetupIds) {
      meetupsToExport = meetupsToExport.filter(m => meetupIds.includes(m.id));
    }

    // Filter by date range if provided
    if (dateRange) {
      meetupsToExport = meetupsToExport.filter(m => 
        m.date >= dateRange.start && m.date <= dateRange.end
      );
    }

    // Sort by date
    meetupsToExport.sort((a, b) => a.date.getTime() - b.date.getTime());

    // Add events
    meetupsToExport.forEach(meetup => {
      const event = this.createCalendarEvent(meetup);
      calendar.createEvent(event);
    });

    return {
      icsContent: calendar.toString(),
      fileName: `gaming_pc_meetups_${new Date().toISOString().split('T')[0]}.ics`,
      eventCount: meetupsToExport.length
    };
  }

  /**
   * Create calendar event from meetup
   */
  private createCalendarEvent(meetup: MeetupDetails): any {
    const endDate = new Date(meetup.date);
    endDate.setMinutes(endDate.getMinutes() + meetup.duration);

    const description = this.generateEventDescription(meetup);
    const locationString = `${meetup.location.name}, ${meetup.location.address}`;

    const eventData: any = {
      start: meetup.date,
      end: endDate,
      summary: `PC Deal: ${meetup.listing.title}`,
      description,
      location: locationString,
      categories: ['business', 'meeting'],
      status: meetup.status === 'confirmed' ? 'CONFIRMED' : 'TENTATIVE',
      busystatus: 'BUSY',
      organizer: {
        name: 'Gaming PC Arbitrage',
        email: 'deals@pcflip.local'
      }
    };

    // Add geo coordinates if available
    if (meetup.location.latitude && meetup.location.longitude) {
      eventData.geo = {
        lat: meetup.location.latitude,
        lon: meetup.location.longitude
      };
    }

    // Add attendee if email provided
    if (meetup.party.email) {
      eventData.attendees = [{
        name: meetup.party.name,
        email: meetup.party.email,
        rsvp: true,
        status: 'NEEDS-ACTION'
      }];
    }

    // Add alarm/reminder
    if (meetup.reminder) {
      eventData.alarms = [{
        type: 'display',
        trigger: meetup.reminder * 60, // Convert to seconds
        description: `Meetup reminder: ${meetup.listing.title}`
      }];
    }

    // Add custom properties
    eventData.x = {
      'X-DEAL-ID': meetup.dealId,
      'X-LISTING-ID': meetup.listing.id,
      'X-LISTING-URL': meetup.listing.url,
      'X-PRICE': String(meetup.listing.price),
      'X-SAFETY-RATING': String(meetup.location.safetyRating || 0)
    };

    return eventData;
  }

  /**
   * Generate detailed event description
   */
  private generateEventDescription(meetup: MeetupDetails): string {
    const lines: string[] = [
      `🖥️ Gaming PC Purchase Meetup`,
      ``,
      `📋 LISTING DETAILS:`,
      `Title: ${meetup.listing.title}`,
      `Price: $${meetup.listing.price}`,
      `Platform: ${meetup.listing.platform}`,
      `URL: ${meetup.listing.url}`,
      ``
    ];

    // Add components if available
    if (meetup.listing.components) {
      lines.push(`🔧 COMPONENTS:`);
      if (meetup.listing.components.cpu) {
        lines.push(`CPU: ${meetup.listing.components.cpu.model}`);
      }
      if (meetup.listing.components.gpu) {
        lines.push(`GPU: ${meetup.listing.components.gpu.model}`);
      }
      if (meetup.listing.components.ram?.length) {
        const totalRAM = meetup.listing.components.ram.reduce((sum, r) => sum + r.capacity, 0);
        lines.push(`RAM: ${totalRAM}GB`);
      }
      lines.push(``);
    }

    // Add seller info
    lines.push(
      `👤 SELLER INFO:`,
      `Name: ${meetup.party.name}`
    );
    if (meetup.party.phone) {
      lines.push(`Phone: ${meetup.party.phone}`);
    }
    if (meetup.party.email) {
      lines.push(`Email: ${meetup.party.email}`);
    }
    lines.push(``);

    // Add location details
    lines.push(
      `📍 LOCATION:`,
      `${meetup.location.name}`,
      `${meetup.location.address}`,
      `Type: ${meetup.location.type}`,
      `Safety Rating: ${'⭐'.repeat(meetup.location.safetyRating || 0)}`
    );

    // Add safety tips
    lines.push(
      ``,
      `🛡️ SAFETY REMINDERS:`,
      `• Bring a friend if possible`,
      `• Test all components before payment`,
      `• Use counterfeit detection pen for large bills`,
      `• Trust your instincts - leave if uncomfortable`,
      `• Take photos of serial numbers`
    );

    // Add checklist
    lines.push(
      ``,
      `✅ CHECKLIST:`,
      `[ ] Cash in envelope`,
      `[ ] Phone charged`,
      `[ ] Testing equipment (USB, monitor cable)`,
      `[ ] Transportation arranged`,
      `[ ] Friend notified of location`
    );

    // Add notes if any
    if (meetup.notes) {
      lines.push(``, `📝 NOTES:`, meetup.notes);
    }

    return lines.join('\n');
  }

  /**
   * Update meetup status
   */
  async updateMeetupStatus(
    meetupId: string,
    status: MeetupDetails['status']
  ): Promise<MeetupDetails | null> {
    const meetup = this.meetups.get(meetupId);
    if (!meetup) return null;

    meetup.status = status;
    meetup.updatedAt = new Date();

    await this.saveData();

    // Cancel reminder if meetup is cancelled
    if (status === 'cancelled') {
      this.cancelReminder(meetupId);
    }

    return meetup;
  }

  /**
   * Reschedule a meetup
   */
  async rescheduleMeetup(
    meetupId: string,
    newDate: Date,
    newLocation?: MeetupLocation
  ): Promise<MeetupDetails | null> {
    const meetup = this.meetups.get(meetupId);
    if (!meetup) return null;

    meetup.date = newDate;
    if (newLocation) {
      meetup.location = newLocation;
    }
    meetup.updatedAt = new Date();

    // Reschedule reminder
    this.cancelReminder(meetupId);
    if (meetup.reminder) {
      this.scheduleReminder(meetup);
    }

    await this.saveData();
    return meetup;
  }

  /**
   * Get upcoming meetups
   */
  getUpcomingMeetups(days: number = 7): MeetupDetails[] {
    const now = new Date();
    const future = new Date();
    future.setDate(future.getDate() + days);

    return Array.from(this.meetups.values())
      .filter(m => 
        m.date >= now && 
        m.date <= future && 
        m.status !== 'cancelled' && 
        m.status !== 'completed'
      )
      .sort((a, b) => a.date.getTime() - b.date.getTime());
  }

  /**
   * Get meetups by deal
   */
  getMeetupsByDeal(dealId: string): MeetupDetails[] {
    return Array.from(this.meetups.values())
      .filter(m => m.dealId === dealId)
      .sort((a, b) => a.date.getTime() - b.date.getTime());
  }

  /**
   * Add safe location
   */
  async addSafeLocation(location: MeetupLocation): Promise<void> {
    // Check if already exists
    const exists = this.safeLocations.some(l => 
      l.name === location.name && l.address === location.address
    );
    
    if (!exists) {
      this.safeLocations.push(location);
      await this.saveLocations();
    }
  }

  /**
   * Get safe locations
   */
  getSafeLocations(type?: MeetupLocation['type']): MeetupLocation[] {
    if (type) {
      return this.safeLocations.filter(l => l.type === type);
    }
    return [...this.safeLocations];
  }

  /**
   * Get location suggestions based on listing
   */
  suggestLocations(listing: Listing): MeetupLocation[] {
    // Sort by safety rating and type preference
    const sorted = [...this.safeLocations].sort((a, b) => {
      // Prefer police stations for high-value items
      if (listing.price > 1000) {
        if (a.type === 'police-station' && b.type !== 'police-station') return -1;
        if (b.type === 'police-station' && a.type !== 'police-station') return 1;
      }
      
      // Then sort by safety rating
      return (b.safetyRating || 0) - (a.safetyRating || 0);
    });

    return sorted.slice(0, 3); // Return top 3 suggestions
  }

  /**
   * Schedule reminder notification
   */
  private scheduleReminder(meetup: MeetupDetails): void {
    if (!meetup.reminder) return;

    const reminderTime = new Date(meetup.date);
    reminderTime.setMinutes(reminderTime.getMinutes() - meetup.reminder);

    const now = new Date();
    const delay = reminderTime.getTime() - now.getTime();

    if (delay > 0) {
      const timeoutId = setTimeout(() => {
        this.sendReminderNotification(meetup);
      }, delay);

      // Store timeout ID for cancellation
      (meetup as any).reminderTimeoutId = timeoutId;
    }
  }

  /**
   * Cancel reminder
   */
  private cancelReminder(meetupId: string): void {
    const meetup = this.meetups.get(meetupId);
    if (meetup && (meetup as any).reminderTimeoutId) {
      clearTimeout((meetup as any).reminderTimeoutId);
      delete (meetup as any).reminderTimeoutId;
    }
  }

  /**
   * Send reminder notification
   */
  private sendReminderNotification(meetup: MeetupDetails): void {
    const timeUntil = Math.round((meetup.date.getTime() - Date.now()) / (1000 * 60));
    
    chrome.notifications.create({
      type: 'basic',
      iconUrl: chrome.runtime.getURL('icons/icon-48.png'),
      title: 'Meetup Reminder',
      message: `PC deal meetup in ${timeUntil} minutes at ${meetup.location.name}`,
      priority: 2,
      buttons: [
        { title: 'View Details' },
        { title: 'Get Directions' }
      ]
    });
  }

  /**
   * Generate safety report for a meetup
   */
  generateSafetyReport(meetupId: string): string[] {
    const meetup = this.meetups.get(meetupId);
    if (!meetup) return [];

    const tips: string[] = [];

    // Time-based tips
    const hour = meetup.date.getHours();
    if (hour < 8 || hour > 18) {
      tips.push('⚠️ Meeting outside daylight hours - ensure location is well-lit');
    }

    // Price-based tips
    if (meetup.listing.price > 1000) {
      tips.push('💵 High-value transaction - consider bringing counterfeit detection tools');
      tips.push('👥 Bring a trusted friend for added security');
    }

    // Location-based tips
    if (meetup.location.type !== 'police-station' && meetup.listing.price > 500) {
      tips.push('🏢 Consider meeting at a police station for this value');
    }

    // General tips
    tips.push('📱 Share your location with someone you trust');
    tips.push('🔌 Bring equipment to test the PC (power cable, monitor cable)');
    tips.push('📸 Document the condition with photos/video');
    tips.push('🆔 Verify seller identity matches listing');

    return tips;
  }

  /**
   * Persistence methods
   */
  private async loadData(): Promise<void> {
    const { 
      [this.STORAGE_KEY]: savedMeetups,
      [this.LOCATIONS_KEY]: savedLocations 
    } = await chrome.storage.local.get([this.STORAGE_KEY, this.LOCATIONS_KEY]);

    if (savedMeetups) {
      Object.entries(savedMeetups).forEach(([id, data]: [string, any]) => {
        this.meetups.set(id, {
          ...data,
          date: new Date(data.date),
          createdAt: new Date(data.createdAt),
          updatedAt: new Date(data.updatedAt)
        });
      });
    }

    if (savedLocations) {
      this.safeLocations = savedLocations;
    }
  }

  private async saveData(): Promise<void> {
    const data: Record<string, any> = {};
    this.meetups.forEach((meetup, id) => {
      data[id] = {
        ...meetup,
        date: meetup.date.toISOString(),
        createdAt: meetup.createdAt.toISOString(),
        updatedAt: meetup.updatedAt.toISOString()
      };
    });
    await chrome.storage.local.set({ [this.STORAGE_KEY]: data });
  }

  private async saveLocations(): Promise<void> {
    await chrome.storage.local.set({ [this.LOCATIONS_KEY]: this.safeLocations });
  }

  /**
   * Export meetup data
   */
  exportMeetupData(meetupId: string): any {
    const meetup = this.meetups.get(meetupId);
    if (!meetup) return null;

    return {
      meetup: {
        ...meetup,
        date: meetup.date.toISOString(),
        createdAt: meetup.createdAt.toISOString(),
        updatedAt: meetup.updatedAt.toISOString()
      },
      safetyTips: this.generateSafetyReport(meetupId),
      suggestedLocations: this.suggestLocations(meetup.listing)
    };
  }
}

// Export singleton instance
export const meetupScheduler = new MeetupScheduler();
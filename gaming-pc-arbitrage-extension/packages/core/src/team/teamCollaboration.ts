/**
 * Team Collaboration Module
 * Enables multi-user team features for coordinated arbitrage operations
 */

import { Deal, Listing, User, Notification } from '../types';

export interface TeamMember {
  id: string;
  email: string;
  name: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  avatar?: string;
  joinedAt: Date;
  lastActive: Date;
  permissions: TeamPermissions;
  stats: MemberStats;
  preferences: MemberPreferences;
}

export interface TeamPermissions {
  canEditListings: boolean;
  canManageDeals: boolean;
  canViewFinancials: boolean;
  canInviteMembers: boolean;
  canExportData: boolean;
  canEditSettings: boolean;
  canAssignTasks: boolean;
}

export interface MemberStats {
  dealsCreated: number;
  dealsCompleted: number;
  totalRevenue: number;
  avgDealTime: number;
  successRate: number;
  lastDealDate?: Date;
}

export interface MemberPreferences {
  notifications: {
    newListings: boolean;
    dealUpdates: boolean;
    teamActivity: boolean;
    dailyDigest: boolean;
  };
  specialties: string[];
  maxActiveDeals: number;
  preferredPlatforms: string[];
}

export interface Team {
  id: string;
  name: string;
  ownerId: string;
  members: TeamMember[];
  createdAt: Date;
  settings: TeamSettings;
  subscription: TeamSubscription;
}

export interface TeamSettings {
  autoAssignment: boolean;
  requireApproval: boolean;
  shareRevenue: boolean;
  revenueSplit: Record<string, number>; // memberId -> percentage
  defaultPermissions: TeamPermissions;
  integrations: {
    slack?: SlackIntegration;
    discord?: DiscordIntegration;
  };
}

export interface TeamSubscription {
  plan: 'free' | 'pro' | 'enterprise';
  maxMembers: number;
  features: string[];
  expiresAt?: Date;
}

export interface SlackIntegration {
  webhookUrl: string;
  channel: string;
  notifications: string[];
}

export interface DiscordIntegration {
  webhookUrl: string;
  notifications: string[];
}

export interface TeamActivity {
  id: string;
  teamId: string;
  memberId: string;
  type: 'listing_found' | 'deal_created' | 'deal_completed' | 'member_joined' | 
        'task_assigned' | 'comment_added' | 'status_changed';
  entityId?: string;
  entityType?: 'listing' | 'deal' | 'task';
  description: string;
  metadata?: any;
  timestamp: Date;
}

export interface TeamTask {
  id: string;
  teamId: string;
  title: string;
  description: string;
  type: 'research' | 'contact' | 'inspect' | 'negotiate' | 'pickup' | 'list' | 'other';
  assignedTo?: string;
  assignedBy: string;
  relatedEntityId?: string;
  relatedEntityType?: 'listing' | 'deal';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  dueDate?: Date;
  completedAt?: Date;
  comments: TaskComment[];
  createdAt: Date;
  updatedAt: Date;
}

export interface TaskComment {
  id: string;
  taskId: string;
  memberId: string;
  text: string;
  attachments?: string[];
  createdAt: Date;
}

export interface SharedDeal extends Deal {
  assignedTo?: string;
  visibility: 'private' | 'team' | 'public';
  collaborators: string[];
  revenue?: {
    total: number;
    splits: Record<string, number>;
  };
  activityLog: TeamActivity[];
}

export class TeamCollaborationManager {
  private teams: Map<string, Team> = new Map();
  private activities: TeamActivity[] = [];
  private tasks: Map<string, TeamTask> = new Map();
  private currentTeamId: string | null = null;
  private currentMemberId: string | null = null;
  
  constructor() {
    this.loadData();
  }

  /**
   * Create a new team
   */
  async createTeam(name: string, ownerId: string): Promise<Team> {
    const team: Team = {
      id: `team_${Date.now()}`,
      name,
      ownerId,
      members: [],
      createdAt: new Date(),
      settings: this.getDefaultSettings(),
      subscription: {
        plan: 'free',
        maxMembers: 3,
        features: ['basic_collaboration', 'task_assignment']
      }
    };

    // Add owner as first member
    const owner: TeamMember = {
      id: ownerId,
      email: '', // To be filled
      name: 'Team Owner',
      role: 'owner',
      joinedAt: new Date(),
      lastActive: new Date(),
      permissions: this.getOwnerPermissions(),
      stats: this.getEmptyStats(),
      preferences: this.getDefaultPreferences()
    };

    team.members.push(owner);
    this.teams.set(team.id, team);
    await this.saveData();

    // Log activity
    await this.logActivity({
      teamId: team.id,
      memberId: ownerId,
      type: 'member_joined',
      description: `${owner.name} created the team`
    });

    return team;
  }

  /**
   * Invite a member to team
   */
  async inviteMember(
    teamId: string,
    email: string,
    role: TeamMember['role'] = 'member',
    invitedBy: string
  ): Promise<string> {
    const team = this.teams.get(teamId);
    if (!team) throw new Error('Team not found');

    // Check permissions
    const inviter = team.members.find(m => m.id === invitedBy);
    if (!inviter?.permissions.canInviteMembers) {
      throw new Error('No permission to invite members');
    }

    // Check member limit
    if (team.members.length >= team.subscription.maxMembers) {
      throw new Error(`Team limit reached (${team.subscription.maxMembers} members)`);
    }

    // Generate invitation code
    const inviteCode = `invite_${teamId}_${Date.now()}`;
    
    // Store invitation
    await chrome.storage.local.set({
      [`invitation_${inviteCode}`]: {
        teamId,
        email,
        role,
        invitedBy,
        createdAt: new Date(),
        expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days
      }
    });

    // Send notification (in real app, would send email)
    await this.notifyTeam(teamId, {
      type: 'member_invited',
      title: 'New Team Invitation',
      message: `${inviter.name} invited ${email} to join the team`,
      metadata: { email, role }
    });

    return inviteCode;
  }

  /**
   * Accept team invitation
   */
  async acceptInvitation(inviteCode: string, userId: string, userName: string): Promise<Team> {
    const { [`invitation_${inviteCode}`]: invitation } = await chrome.storage.local.get(`invitation_${inviteCode}`);
    
    if (!invitation) throw new Error('Invalid invitation code');
    if (new Date(invitation.expiresAt) < new Date()) throw new Error('Invitation expired');

    const team = this.teams.get(invitation.teamId);
    if (!team) throw new Error('Team not found');

    // Create new member
    const member: TeamMember = {
      id: userId,
      email: invitation.email,
      name: userName,
      role: invitation.role,
      joinedAt: new Date(),
      lastActive: new Date(),
      permissions: invitation.role === 'admin' ? 
        this.getAdminPermissions() : 
        this.getMemberPermissions(),
      stats: this.getEmptyStats(),
      preferences: this.getDefaultPreferences()
    };

    team.members.push(member);
    await this.saveData();

    // Remove invitation
    await chrome.storage.local.remove(`invitation_${inviteCode}`);

    // Log activity
    await this.logActivity({
      teamId: team.id,
      memberId: userId,
      type: 'member_joined',
      description: `${userName} joined the team`
    });

    return team;
  }

  /**
   * Assign a task to team member
   */
  async createTask(
    teamId: string,
    task: Omit<TeamTask, 'id' | 'teamId' | 'createdAt' | 'updatedAt' | 'comments' | 'status'>
  ): Promise<TeamTask> {
    const team = this.teams.get(teamId);
    if (!team) throw new Error('Team not found');

    const newTask: TeamTask = {
      ...task,
      id: `task_${Date.now()}`,
      teamId,
      status: 'pending',
      comments: [],
      createdAt: new Date(),
      updatedAt: new Date()
    };

    this.tasks.set(newTask.id, newTask);
    await this.saveData();

    // Notify assigned member
    if (newTask.assignedTo) {
      await this.notifyMember(newTask.assignedTo, {
        type: 'task_assigned',
        title: 'New Task Assigned',
        message: `You have been assigned: ${newTask.title}`,
        metadata: { taskId: newTask.id }
      });
    }

    // Log activity
    await this.logActivity({
      teamId,
      memberId: task.assignedBy,
      type: 'task_assigned',
      entityId: newTask.id,
      entityType: 'task',
      description: `${task.assignedBy} created task: ${newTask.title}`
    });

    return newTask;
  }

  /**
   * Update task status
   */
  async updateTaskStatus(
    taskId: string,
    status: TeamTask['status'],
    memberId: string
  ): Promise<void> {
    const task = this.tasks.get(taskId);
    if (!task) throw new Error('Task not found');

    const oldStatus = task.status;
    task.status = status;
    task.updatedAt = new Date();

    if (status === 'completed') {
      task.completedAt = new Date();
    }

    await this.saveData();

    // Log activity
    await this.logActivity({
      teamId: task.teamId,
      memberId,
      type: 'status_changed',
      entityId: taskId,
      entityType: 'task',
      description: `Task status changed from ${oldStatus} to ${status}`,
      metadata: { oldStatus, newStatus: status }
    });
  }

  /**
   * Add comment to task
   */
  async addTaskComment(
    taskId: string,
    memberId: string,
    text: string,
    attachments?: string[]
  ): Promise<TaskComment> {
    const task = this.tasks.get(taskId);
    if (!task) throw new Error('Task not found');

    const comment: TaskComment = {
      id: `comment_${Date.now()}`,
      taskId,
      memberId,
      text,
      attachments,
      createdAt: new Date()
    };

    task.comments.push(comment);
    task.updatedAt = new Date();
    await this.saveData();

    // Notify task participants
    const participants = new Set([task.assignedBy, task.assignedTo].filter(Boolean));
    participants.delete(memberId); // Don't notify the commenter

    for (const participantId of participants) {
      if (participantId) {
        await this.notifyMember(participantId, {
          type: 'comment_added',
          title: 'New Comment on Task',
          message: `${memberId} commented on: ${task.title}`,
          metadata: { taskId, commentId: comment.id }
        });
      }
    }

    return comment;
  }

  /**
   * Share a deal with team
   */
  async shareDeal(
    deal: Deal,
    teamId: string,
    visibility: SharedDeal['visibility'] = 'team',
    assignedTo?: string
  ): Promise<SharedDeal> {
    const team = this.teams.get(teamId);
    if (!team) throw new Error('Team not found');

    const sharedDeal: SharedDeal = {
      ...deal,
      visibility,
      assignedTo,
      collaborators: assignedTo ? [assignedTo] : [],
      activityLog: []
    };

    // Calculate revenue splits if enabled
    if (team.settings.shareRevenue && team.settings.revenueSplit) {
      const profit = (deal.sellPrice || 0) - (deal.purchasePrice || 0);
      const splits: Record<string, number> = {};
      
      Object.entries(team.settings.revenueSplit).forEach(([memberId, percentage]) => {
        splits[memberId] = profit * (percentage / 100);
      });

      sharedDeal.revenue = {
        total: profit,
        splits
      };
    }

    // Store shared deal
    await chrome.storage.local.set({
      [`shared_deal_${deal.id}`]: sharedDeal
    });

    // Log activity
    await this.logActivity({
      teamId,
      memberId: this.currentMemberId || 'system',
      type: 'deal_created',
      entityId: deal.id,
      entityType: 'deal',
      description: `Deal shared with team: ${deal.listing.title}`
    });

    return sharedDeal;
  }

  /**
   * Get team performance analytics
   */
  getTeamAnalytics(teamId: string, dateRange?: { start: Date; end: Date }) {
    const team = this.teams.get(teamId);
    if (!team) throw new Error('Team not found');

    const analytics = {
      members: team.members.length,
      totalDeals: 0,
      totalRevenue: 0,
      avgDealTime: 0,
      successRate: 0,
      memberPerformance: [] as any[],
      platformBreakdown: {} as Record<string, number>,
      recentActivity: [] as TeamActivity[]
    };

    // Aggregate member stats
    team.members.forEach(member => {
      analytics.totalDeals += member.stats.dealsCompleted;
      analytics.totalRevenue += member.stats.totalRevenue;
      
      analytics.memberPerformance.push({
        memberId: member.id,
        name: member.name,
        deals: member.stats.dealsCompleted,
        revenue: member.stats.totalRevenue,
        successRate: member.stats.successRate
      });
    });

    // Calculate averages
    if (team.members.length > 0) {
      analytics.avgDealTime = team.members.reduce((sum, m) => 
        sum + m.stats.avgDealTime, 0) / team.members.length;
      analytics.successRate = team.members.reduce((sum, m) => 
        sum + m.stats.successRate, 0) / team.members.length;
    }

    // Get recent activity
    analytics.recentActivity = this.activities
      .filter(a => a.teamId === teamId)
      .slice(-20)
      .reverse();

    return analytics;
  }

  /**
   * Distribute listing to team based on rules
   */
  async distributeListing(listing: Listing, teamId: string): Promise<string | null> {
    const team = this.teams.get(teamId);
    if (!team || !team.settings.autoAssignment) return null;

    // Find best member for assignment
    const availableMembers = team.members.filter(m => 
      m.role !== 'viewer' &&
      m.stats.dealsCreated < m.preferences.maxActiveDeals &&
      m.preferences.preferredPlatforms.includes(listing.platform)
    );

    if (availableMembers.length === 0) return null;

    // Score members based on criteria
    const scoredMembers = availableMembers.map(member => {
      let score = 0;
      
      // Prefer members with matching specialties
      if (listing.components?.gpu && member.preferences.specialties.includes('gpu')) score += 10;
      if (listing.components?.cpu && member.preferences.specialties.includes('cpu')) score += 10;
      
      // Balance workload
      score -= member.stats.dealsCreated * 2;
      
      // Consider success rate
      score += member.stats.successRate * 20;
      
      return { member, score };
    });

    // Select highest scoring member
    scoredMembers.sort((a, b) => b.score - a.score);
    const selectedMember = scoredMembers[0].member;

    // Create task for the listing
    await this.createTask(teamId, {
      title: `Review: ${listing.title}`,
      description: `New listing found: ${listing.url}`,
      type: 'research',
      assignedTo: selectedMember.id,
      assignedBy: 'system',
      relatedEntityId: listing.id,
      relatedEntityType: 'listing',
      priority: this.calculatePriority(listing),
      dueDate: new Date(Date.now() + 24 * 60 * 60 * 1000) // 24 hours
    });

    return selectedMember.id;
  }

  /**
   * Send notification to team
   */
  private async notifyTeam(teamId: string, notification: any): Promise<void> {
    const team = this.teams.get(teamId);
    if (!team) return;

    // Send to all members
    for (const member of team.members) {
      if (member.preferences.notifications.teamActivity) {
        await this.notifyMember(member.id, notification);
      }
    }

    // Send to integrations
    if (team.settings.integrations.slack && 
        team.settings.integrations.slack.notifications.includes(notification.type)) {
      await this.sendSlackNotification(team.settings.integrations.slack, notification);
    }

    if (team.settings.integrations.discord && 
        team.settings.integrations.discord.notifications.includes(notification.type)) {
      await this.sendDiscordNotification(team.settings.integrations.discord, notification);
    }
  }

  /**
   * Send notification to member
   */
  private async notifyMember(memberId: string, notification: any): Promise<void> {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: chrome.runtime.getURL('icons/icon-48.png'),
      title: notification.title,
      message: notification.message
    });
  }

  /**
   * Send Slack notification
   */
  private async sendSlackNotification(slack: SlackIntegration, notification: any): Promise<void> {
    try {
      await fetch(slack.webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel: slack.channel,
          text: notification.message,
          attachments: [{
            color: 'good',
            title: notification.title,
            fields: Object.entries(notification.metadata || {}).map(([k, v]) => ({
              title: k,
              value: String(v),
              short: true
            }))
          }]
        })
      });
    } catch (error) {
      console.error('Failed to send Slack notification:', error);
    }
  }

  /**
   * Send Discord notification
   */
  private async sendDiscordNotification(discord: DiscordIntegration, notification: any): Promise<void> {
    try {
      await fetch(discord.webhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: notification.message,
          embeds: [{
            title: notification.title,
            color: 0x00ff00,
            fields: Object.entries(notification.metadata || {}).map(([k, v]) => ({
              name: k,
              value: String(v),
              inline: true
            }))
          }]
        })
      });
    } catch (error) {
      console.error('Failed to send Discord notification:', error);
    }
  }

  /**
   * Log team activity
   */
  private async logActivity(activity: Omit<TeamActivity, 'id' | 'timestamp'>): Promise<void> {
    const fullActivity: TeamActivity = {
      ...activity,
      id: `activity_${Date.now()}`,
      timestamp: new Date()
    };

    this.activities.push(fullActivity);
    
    // Keep only last 1000 activities
    if (this.activities.length > 1000) {
      this.activities = this.activities.slice(-1000);
    }

    await this.saveData();
  }

  /**
   * Calculate priority based on listing
   */
  private calculatePriority(listing: Listing): TeamTask['priority'] {
    const value = listing.analysis?.fmv || listing.price;
    const discount = listing.analysis?.discount || 0;
    
    if (discount > 30 && value > 1000) return 'urgent';
    if (discount > 20 || value > 800) return 'high';
    if (discount > 10 || value > 500) return 'medium';
    return 'low';
  }

  /**
   * Helper methods for permissions and defaults
   */
  private getOwnerPermissions(): TeamPermissions {
    return {
      canEditListings: true,
      canManageDeals: true,
      canViewFinancials: true,
      canInviteMembers: true,
      canExportData: true,
      canEditSettings: true,
      canAssignTasks: true
    };
  }

  private getAdminPermissions(): TeamPermissions {
    return {
      canEditListings: true,
      canManageDeals: true,
      canViewFinancials: true,
      canInviteMembers: true,
      canExportData: true,
      canEditSettings: false,
      canAssignTasks: true
    };
  }

  private getMemberPermissions(): TeamPermissions {
    return {
      canEditListings: true,
      canManageDeals: true,
      canViewFinancials: false,
      canInviteMembers: false,
      canExportData: false,
      canEditSettings: false,
      canAssignTasks: false
    };
  }

  private getDefaultSettings(): TeamSettings {
    return {
      autoAssignment: false,
      requireApproval: false,
      shareRevenue: false,
      revenueSplit: {},
      defaultPermissions: this.getMemberPermissions(),
      integrations: {}
    };
  }

  private getEmptyStats(): MemberStats {
    return {
      dealsCreated: 0,
      dealsCompleted: 0,
      totalRevenue: 0,
      avgDealTime: 0,
      successRate: 0
    };
  }

  private getDefaultPreferences(): MemberPreferences {
    return {
      notifications: {
        newListings: true,
        dealUpdates: true,
        teamActivity: true,
        dailyDigest: false
      },
      specialties: [],
      maxActiveDeals: 5,
      preferredPlatforms: ['facebook', 'craigslist', 'offerup']
    };
  }

  /**
   * Data persistence
   */
  private async loadData(): Promise<void> {
    const { teams, activities, tasks } = await chrome.storage.local.get(['teams', 'activities', 'tasks']);
    
    if (teams) {
      this.teams = new Map(Object.entries(teams));
    }
    
    if (activities) {
      this.activities = activities;
    }
    
    if (tasks) {
      this.tasks = new Map(Object.entries(tasks));
    }
  }

  private async saveData(): Promise<void> {
    await chrome.storage.local.set({
      teams: Object.fromEntries(this.teams),
      activities: this.activities,
      tasks: Object.fromEntries(this.tasks)
    });
  }

  /**
   * Set current context
   */
  setCurrentContext(teamId: string, memberId: string): void {
    this.currentTeamId = teamId;
    this.currentMemberId = memberId;
  }

  /**
   * Get current team
   */
  getCurrentTeam(): Team | null {
    return this.currentTeamId ? this.teams.get(this.currentTeamId) || null : null;
  }

  /**
   * Get team tasks
   */
  getTeamTasks(teamId: string, filters?: {
    status?: TeamTask['status'];
    assignedTo?: string;
    priority?: TeamTask['priority'];
  }): TeamTask[] {
    let tasks = Array.from(this.tasks.values()).filter(t => t.teamId === teamId);
    
    if (filters?.status) {
      tasks = tasks.filter(t => t.status === filters.status);
    }
    
    if (filters?.assignedTo) {
      tasks = tasks.filter(t => t.assignedTo === filters.assignedTo);
    }
    
    if (filters?.priority) {
      tasks = tasks.filter(t => t.priority === filters.priority);
    }
    
    return tasks.sort((a, b) => b.createdAt.getTime() - a.createdAt.getTime());
  }
}

// Export singleton instance
export const teamCollaborationManager = new TeamCollaborationManager();
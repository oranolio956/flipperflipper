/**
 * Assignee Cell Component
 * Dropdown to assign/unassign users to deals
 */

import React, { useState, useEffect } from 'react';
import { User, UserX } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { db } from '@/lib/db';
import { getSettings } from '@/lib/settings';
import { can } from '@/lib/authz';
import { generateId } from '@/core';
import type { DBUser, DBAssignment } from '@/lib/db';

interface AssigneeCellProps {
  dealId: string;
  currentAssigneeId?: string;
  onAssignmentChange?: (userId?: string) => void;
}

export function AssigneeCell({ 
  dealId, 
  currentAssigneeId, 
  onAssignmentChange 
}: AssigneeCellProps) {
  const { toast } = useToast();
  const [users, setUsers] = useState<DBUser[]>([]);
  const [currentUser, setCurrentUser] = useState<DBUser | null>(null);
  const [assignee, setAssignee] = useState<DBUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [currentAssigneeId]);

  const loadData = async () => {
    try {
      // Load all users
      const allUsers = await db.users.toArray();
      setUsers(allUsers);
      
      // Get current user
      const settings = await getSettings();
      const current = allUsers.find(u => u.id === settings.team?.currentUserId);
      setCurrentUser(current || null);
      
      // Find assignee
      if (currentAssigneeId) {
        const assigned = allUsers.find(u => u.id === currentAssigneeId);
        setAssignee(assigned || null);
      } else {
        setAssignee(null);
      }
    } catch (error) {
      console.error('Failed to load users:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAssignmentChange = async (userId: string) => {
    if (!currentUser) return;

    // Check permissions
    if (!can(currentUser.role, 'assignDeal')) {
      toast({
        title: 'Permission denied',
        description: 'You cannot assign deals',
        variant: 'destructive',
      });
      return;
    }

    // Operators can only assign to themselves
    if (currentUser.role === 'operator' && userId !== currentUser.id && userId !== 'unassigned') {
      toast({
        title: 'Permission denied',
        description: 'You can only assign deals to yourself',
        variant: 'destructive',
      });
      return;
    }

    try {
      if (userId === 'unassigned') {
        // Remove assignment
        await db.assignments.where({ dealId }).delete();
        setAssignee(null);
        onAssignmentChange?.(undefined);
        
        toast({
          title: 'Deal unassigned',
          description: 'Deal is now available for anyone',
        });
      } else {
        // Create or update assignment
        const existing = await db.assignments.where({ dealId }).first();
        
        if (existing) {
          await db.assignments.update(existing._id!, { userId });
        } else {
          await db.assignments.add({
            id: generateId(),
            dealId,
            userId,
            createdAt: new Date(),
          });
        }
        
        const newAssignee = users.find(u => u.id === userId);
        setAssignee(newAssignee || null);
        onAssignmentChange?.(userId);
        
        toast({
          title: 'Deal assigned',
          description: `Assigned to ${newAssignee?.name}`,
        });
      }

      // Log event
      await db.events.add({
        timestamp: Date.now(),
        category: 'deal',
        name: 'assignment_changed',
        data: {
          dealId,
          userId: userId === 'unassigned' ? null : userId,
          actorUserId: currentUser.id,
        },
      });
    } catch (error) {
      toast({
        title: 'Assignment failed',
        description: String(error),
        variant: 'destructive',
      });
    }
  };

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading...</div>;
  }

  if (!currentUser) {
    return <div className="text-sm text-muted-foreground">No user</div>;
  }

  // Viewers cannot change assignments
  if (currentUser.role === 'viewer') {
    if (assignee) {
      return (
        <Badge variant="secondary" className="gap-1">
          <User className="h-3 w-3" />
          {assignee.name}
        </Badge>
      );
    }
    return <span className="text-sm text-muted-foreground">Unassigned</span>;
  }

  // Filter available users based on role
  const availableUsers = currentUser.role === 'admin' 
    ? users 
    : users.filter(u => u.id === currentUser.id);

  return (
    <Select
      value={assignee?.id || 'unassigned'}
      onValueChange={handleAssignmentChange}
    >
      <SelectTrigger className="h-8 w-[140px]">
        <SelectValue>
          {assignee ? (
            <div className="flex items-center gap-1">
              <User className="h-3 w-3" />
              <span className="truncate">{assignee.name}</span>
            </div>
          ) : (
            <div className="flex items-center gap-1 text-muted-foreground">
              <UserX className="h-3 w-3" />
              <span>Unassigned</span>
            </div>
          )}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="unassigned">
          <div className="flex items-center gap-2">
            <UserX className="h-4 w-4" />
            <span>Unassigned</span>
          </div>
        </SelectItem>
        {availableUsers.map(user => (
          <SelectItem key={user.id} value={user.id}>
            <div className="flex items-center gap-2">
              <User className="h-4 w-4" />
              <span>{user.name}</span>
              {user.id === currentUser.id && (
                <span className="text-xs text-muted-foreground">(me)</span>
              )}
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
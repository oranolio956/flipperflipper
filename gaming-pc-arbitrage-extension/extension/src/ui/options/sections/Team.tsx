/**
 * Team Settings Section
 * Manage users and roles
 */

import React, { useState, useEffect } from 'react';
import { Users, UserPlus, Shield, Eye, Settings as SettingsIcon } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/components/ui/use-toast';
import { db } from '@/lib/db';
import { generateId } from '@/core';
import { can } from '@/lib/authz';
import type { Settings } from '@/core';
import type { DBUser } from '@/lib/db';

interface TeamProps {
  settings: Settings;
  onUpdate: (updates: Partial<Settings>) => void;
}

export function Team({ settings, onUpdate }: TeamProps) {
  const { toast } = useToast();
  const [users, setUsers] = useState<DBUser[]>([]);
  const [currentUser, setCurrentUser] = useState<DBUser | null>(null);
  const [newUserName, setNewUserName] = useState('');
  const [newUserRole, setNewUserRole] = useState<DBUser['role']>('operator');
  const [isAddingUser, setIsAddingUser] = useState(false);

  const teamSettings = settings.team || {};

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const allUsers = await db.users.toArray();
      setUsers(allUsers);
      
      // Find current user
      const current = allUsers.find(u => u.id === teamSettings.currentUserId);
      setCurrentUser(current || null);
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };

  const handleAddUser = async () => {
    if (!newUserName.trim()) {
      toast({
        title: 'Invalid name',
        description: 'Please enter a user name',
        variant: 'destructive',
      });
      return;
    }

    if (!currentUser || !can(currentUser.role, 'manageUsers')) {
      toast({
        title: 'Permission denied',
        description: 'Only admins can manage users',
        variant: 'destructive',
      });
      return;
    }

    setIsAddingUser(true);
    try {
      const newUser: DBUser = {
        id: generateId(),
        name: newUserName.trim(),
        role: newUserRole,
        createdAt: new Date(),
      };

      await db.users.add(newUser);
      await loadUsers();
      
      setNewUserName('');
      setNewUserRole('operator');
      
      toast({
        title: 'User added',
        description: `${newUser.name} has been added as ${newUser.role}`,
      });
    } catch (error) {
      toast({
        title: 'Failed to add user',
        description: String(error),
        variant: 'destructive',
      });
    } finally {
      setIsAddingUser(false);
    }
  };

  const handleSetCurrentUser = (userId: string) => {
    onUpdate({
      team: {
        ...teamSettings,
        currentUserId: userId,
      },
    });
    
    const user = users.find(u => u.id === userId);
    if (user) {
      setCurrentUser(user);
      toast({
        title: 'User switched',
        description: `Now operating as ${user.name}`,
      });
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!currentUser || !can(currentUser.role, 'manageUsers')) {
      toast({
        title: 'Permission denied',
        description: 'Only admins can delete users',
        variant: 'destructive',
      });
      return;
    }

    if (userId === currentUser.id) {
      toast({
        title: 'Cannot delete self',
        description: 'Switch to another user first',
        variant: 'destructive',
      });
      return;
    }

    try {
      // Delete user and their assignments
      await db.users.where('id').equals(userId).delete();
      await db.assignments.where('userId').equals(userId).delete();
      await loadUsers();
      
      toast({
        title: 'User deleted',
        description: 'User and their assignments have been removed',
      });
    } catch (error) {
      toast({
        title: 'Failed to delete user',
        description: String(error),
        variant: 'destructive',
      });
    }
  };

  const getRoleIcon = (role: DBUser['role']) => {
    switch (role) {
      case 'admin':
        return <Shield className="h-4 w-4" />;
      case 'operator':
        return <SettingsIcon className="h-4 w-4" />;
      case 'viewer':
        return <Eye className="h-4 w-4" />;
    }
  };

  const getRoleColor = (role: DBUser['role']) => {
    switch (role) {
      case 'admin':
        return 'text-red-600';
      case 'operator':
        return 'text-blue-600';
      case 'viewer':
        return 'text-gray-600';
    }
  };

  return (
    <div className="space-y-6">
      {/* Current User */}
      <Card>
        <CardHeader>
          <CardTitle>Current User</CardTitle>
          <CardDescription>
            Select which user profile to operate as
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Label>Active User</Label>
            <Select
              value={teamSettings.currentUserId || ''}
              onValueChange={handleSetCurrentUser}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select user" />
              </SelectTrigger>
              <SelectContent>
                {users.map(user => (
                  <SelectItem key={user.id} value={user.id}>
                    <div className="flex items-center gap-2">
                      {getRoleIcon(user.role)}
                      <span>{user.name}</span>
                      <span className={`text-xs ${getRoleColor(user.role)}`}>
                        ({user.role})
                      </span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {currentUser && (
            <Alert className="mt-4">
              <AlertDescription>
                <strong>Current permissions:</strong>
                <ul className="mt-2 text-sm list-disc list-inside">
                  {currentUser.role === 'admin' && (
                    <>
                      <li>Full system access</li>
                      <li>Manage users and settings</li>
                      <li>View and edit all deals</li>
                    </>
                  )}
                  {currentUser.role === 'operator' && (
                    <>
                      <li>Create and edit deals</li>
                      <li>Assign deals to self</li>
                      <li>View analytics</li>
                    </>
                  )}
                  {currentUser.role === 'viewer' && (
                    <>
                      <li>View all deals (read-only)</li>
                      <li>View analytics</li>
                      <li>Export data</li>
                    </>
                  )}
                </ul>
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* User Management */}
      <Card>
        <CardHeader>
          <CardTitle>User Management</CardTitle>
          <CardDescription>
            Add and manage team members
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {currentUser && can(currentUser.role, 'manageUsers') ? (
            <>
              {/* Add User Form */}
              <div className="space-y-4 p-4 border rounded-lg">
                <h4 className="font-medium">Add New User</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Name</Label>
                    <Input
                      value={newUserName}
                      onChange={(e) => setNewUserName(e.target.value)}
                      placeholder="Enter user name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Role</Label>
                    <Select
                      value={newUserRole}
                      onValueChange={(v) => setNewUserRole(v as DBUser['role'])}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="admin">Admin</SelectItem>
                        <SelectItem value="operator">Operator</SelectItem>
                        <SelectItem value="viewer">Viewer</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <Button
                  onClick={handleAddUser}
                  disabled={isAddingUser || !newUserName.trim()}
                  className="w-full"
                >
                  <UserPlus className="h-4 w-4 mr-2" />
                  Add User
                </Button>
              </div>

              {/* User List */}
              <div className="space-y-2">
                <h4 className="font-medium">Team Members</h4>
                {users.map(user => (
                  <div
                    key={user.id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className={getRoleColor(user.role)}>
                        {getRoleIcon(user.role)}
                      </div>
                      <div>
                        <div className="font-medium">{user.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {user.role} • Added {new Date(user.createdAt).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                    {user.id !== currentUser.id && (
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDeleteUser(user.id)}
                      >
                        Remove
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <Alert>
              <Users className="h-4 w-4" />
              <AlertDescription>
                Only administrators can manage users
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
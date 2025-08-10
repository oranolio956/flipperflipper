/**
 * Authorization Helper
 * Role-based access control
 */

export type Role = 'admin' | 'operator' | 'viewer';
export type Action = 
  | 'editSettings'
  | 'assignDeal'
  | 'viewAnalytics'
  | 'backup'
  | 'manageUsers'
  | 'editDeal'
  | 'createDeal'
  | 'deleteDeal'
  | 'exportData';

/**
 * Check if a role can perform an action
 */
export function can(userRole: Role, action: Action): boolean {
  const permissions: Record<Role, Set<Action>> = {
    admin: new Set([
      'editSettings',
      'assignDeal',
      'viewAnalytics',
      'backup',
      'manageUsers',
      'editDeal',
      'createDeal',
      'deleteDeal',
      'exportData',
    ]),
    operator: new Set([
      'assignDeal',
      'viewAnalytics',
      'editDeal',
      'createDeal',
      'exportData',
    ]),
    viewer: new Set([
      'viewAnalytics',
      'exportData',
    ]),
  };
  
  return permissions[userRole]?.has(action) || false;
}

/**
 * Get list of actions a role can perform
 */
export function getAllowedActions(userRole: Role): Action[] {
  const allActions: Action[] = [
    'editSettings',
    'assignDeal',
    'viewAnalytics',
    'backup',
    'manageUsers',
    'editDeal',
    'createDeal',
    'deleteDeal',
    'exportData',
  ];
  
  return allActions.filter(action => can(userRole, action));
}

/**
 * Check if user can modify a specific deal
 */
export function canModifyDeal(
  userRole: Role,
  dealAssigneeId?: string,
  currentUserId?: string
): boolean {
  // Admins can modify any deal
  if (userRole === 'admin') return true;
  
  // Operators can modify unassigned deals or their own
  if (userRole === 'operator') {
    return !dealAssigneeId || dealAssigneeId === currentUserId;
  }
  
  // Viewers cannot modify deals
  return false;
}

/**
 * Filter deals based on user permissions
 */
export function filterDealsForUser(
  deals: Array<{ assigneeId?: string }>,
  userRole: Role,
  currentUserId?: string
): Array<{ assigneeId?: string }> {
  // Admins and viewers see all deals
  if (userRole === 'admin' || userRole === 'viewer') {
    return deals;
  }
  
  // Operators see unassigned deals and their own
  if (userRole === 'operator') {
    return deals.filter(deal => 
      !deal.assigneeId || deal.assigneeId === currentUserId
    );
  }
  
  return [];
}
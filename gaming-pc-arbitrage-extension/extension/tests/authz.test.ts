/**
 * Authorization Tests
 */

import { describe, it, expect } from 'vitest';
import { can, getAllowedActions, canModifyDeal, filterDealsForUser } from '@/lib/authz';

describe('can', () => {
  it('should grant admin all permissions', () => {
    expect(can('admin', 'editSettings')).toBe(true);
    expect(can('admin', 'manageUsers')).toBe(true);
    expect(can('admin', 'assignDeal')).toBe(true);
    expect(can('admin', 'backup')).toBe(true);
  });

  it('should grant operator limited permissions', () => {
    expect(can('operator', 'editSettings')).toBe(false);
    expect(can('operator', 'manageUsers')).toBe(false);
    expect(can('operator', 'assignDeal')).toBe(true);
    expect(can('operator', 'editDeal')).toBe(true);
    expect(can('operator', 'viewAnalytics')).toBe(true);
  });

  it('should grant viewer minimal permissions', () => {
    expect(can('viewer', 'editSettings')).toBe(false);
    expect(can('viewer', 'manageUsers')).toBe(false);
    expect(can('viewer', 'assignDeal')).toBe(false);
    expect(can('viewer', 'editDeal')).toBe(false);
    expect(can('viewer', 'viewAnalytics')).toBe(true);
    expect(can('viewer', 'exportData')).toBe(true);
  });
});

describe('getAllowedActions', () => {
  it('should return all actions for admin', () => {
    const actions = getAllowedActions('admin');
    expect(actions).toContain('editSettings');
    expect(actions).toContain('manageUsers');
    expect(actions).toContain('backup');
    expect(actions.length).toBeGreaterThan(5);
  });

  it('should return limited actions for operator', () => {
    const actions = getAllowedActions('operator');
    expect(actions).toContain('assignDeal');
    expect(actions).toContain('editDeal');
    expect(actions).not.toContain('editSettings');
    expect(actions).not.toContain('manageUsers');
  });

  it('should return minimal actions for viewer', () => {
    const actions = getAllowedActions('viewer');
    expect(actions).toHaveLength(2);
    expect(actions).toContain('viewAnalytics');
    expect(actions).toContain('exportData');
  });
});

describe('canModifyDeal', () => {
  it('should allow admin to modify any deal', () => {
    expect(canModifyDeal('admin', 'user-123', 'user-456')).toBe(true);
    expect(canModifyDeal('admin', undefined, 'user-456')).toBe(true);
    expect(canModifyDeal('admin', 'user-456', 'user-456')).toBe(true);
  });

  it('should allow operator to modify unassigned deals', () => {
    expect(canModifyDeal('operator', undefined, 'user-123')).toBe(true);
  });

  it('should allow operator to modify their own deals', () => {
    expect(canModifyDeal('operator', 'user-123', 'user-123')).toBe(true);
  });

  it('should not allow operator to modify others deals', () => {
    expect(canModifyDeal('operator', 'user-456', 'user-123')).toBe(false);
  });

  it('should not allow viewer to modify any deal', () => {
    expect(canModifyDeal('viewer', undefined, 'user-123')).toBe(false);
    expect(canModifyDeal('viewer', 'user-123', 'user-123')).toBe(false);
  });
});

describe('filterDealsForUser', () => {
  const deals = [
    { id: '1', assigneeId: undefined },
    { id: '2', assigneeId: 'user-123' },
    { id: '3', assigneeId: 'user-456' },
    { id: '4', assigneeId: undefined },
  ];

  it('should show all deals to admin', () => {
    const filtered = filterDealsForUser(deals, 'admin', 'user-123');
    expect(filtered).toHaveLength(4);
  });

  it('should show all deals to viewer', () => {
    const filtered = filterDealsForUser(deals, 'viewer', 'user-123');
    expect(filtered).toHaveLength(4);
  });

  it('should show unassigned and own deals to operator', () => {
    const filtered = filterDealsForUser(deals, 'operator', 'user-123');
    expect(filtered).toHaveLength(3);
    expect(filtered).toContainEqual({ id: '1', assigneeId: undefined });
    expect(filtered).toContainEqual({ id: '2', assigneeId: 'user-123' });
    expect(filtered).toContainEqual({ id: '4', assigneeId: undefined });
    expect(filtered).not.toContainEqual({ id: '3', assigneeId: 'user-456' });
  });
});
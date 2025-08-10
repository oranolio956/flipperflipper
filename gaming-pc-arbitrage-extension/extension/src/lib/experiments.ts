/**
 * Experiments Library
 * Manage A/B test persistence and variant selection
 */

import { db } from './db';
import { 
  pickVariant, 
  recordImpression, 
  recordOutcome,
  maybePromoteWinner,
  type Experiment 
} from '@/core/abtest';
import type { DBExperiment } from './db';

/**
 * Get experiment by ID
 */
export async function getExperiment(experimentId: string): Promise<Experiment | null> {
  const dbExp = await db.experiments.where('id').equals(experimentId).first();
  if (!dbExp) return null;
  
  return {
    id: dbExp.id,
    name: dbExp.name,
    description: dbExp.description,
    variants: dbExp.variants,
    promotedId: dbExp.promotedId,
    createdAt: dbExp.createdAt,
    updatedAt: dbExp.updatedAt,
  };
}

/**
 * Update experiment in database
 */
export async function updateExperiment(exp: Experiment): Promise<void> {
  const dbExp = await db.experiments.where('id').equals(exp.id).first();
  if (!dbExp?._id) return;
  
  await db.experiments.update(dbExp._id, {
    variants: exp.variants,
    promotedId: exp.promotedId,
    updatedAt: exp.updatedAt,
  });
}

/**
 * Select variant and record impression
 */
export async function selectVariant(
  experimentId: string,
  strategy: 'epsilonGreedy' | 'ucb1' = 'epsilonGreedy'
): Promise<{ variantId: string; templateId: string } | null> {
  const exp = await getExperiment(experimentId);
  if (!exp) return null;
  
  // Pick variant
  const variantId = pickVariant(exp, strategy);
  
  // Record impression
  const updated = recordImpression(exp, variantId);
  await updateExperiment(updated);
  
  // Map variant to template ID
  const templateMap: Record<string, string> = {
    'opener_friendly': 'opener_friendly',
    'opener_direct': 'opener_direct', 
    'opener_curious': 'opener_curious',
  };
  
  return {
    variantId,
    templateId: templateMap[variantId] || variantId,
  };
}

/**
 * Record template outcome
 */
export async function recordTemplateOutcome(
  experimentId: string,
  variantId: string,
  success: boolean
): Promise<void> {
  const exp = await getExperiment(experimentId);
  if (!exp) return;
  
  // Record outcome
  let updated = recordOutcome(exp, variantId, success);
  
  // Check if we can promote a winner
  updated = maybePromoteWinner(updated);
  
  await updateExperiment(updated);
  
  // Log event
  await db.events.add({
    timestamp: Date.now(),
    category: 'experiment',
    name: 'outcome_recorded',
    data: {
      experimentId,
      variantId,
      success,
      promoted: updated.promotedId,
    },
  });
}

/**
 * Get all experiments
 */
export async function getAllExperiments(): Promise<Experiment[]> {
  const dbExps = await db.experiments.toArray();
  return dbExps.map(exp => ({
    id: exp.id,
    name: exp.name,
    description: exp.description,
    variants: exp.variants,
    promotedId: exp.promotedId,
    createdAt: exp.createdAt,
    updatedAt: exp.updatedAt,
  }));
}

/**
 * Promote variant manually
 */
export async function promoteVariant(
  experimentId: string,
  variantId: string
): Promise<void> {
  const dbExp = await db.experiments.where('id').equals(experimentId).first();
  if (!dbExp?._id) return;
  
  // Verify variant exists
  const variant = dbExp.variants.find(v => v.id === variantId);
  if (!variant) {
    throw new Error(`Variant ${variantId} not found`);
  }
  
  await db.experiments.update(dbExp._id, {
    promotedId: variantId,
    updatedAt: new Date(),
  });
  
  // Log event
  await db.events.add({
    timestamp: Date.now(),
    category: 'experiment',
    name: 'variant_promoted',
    data: {
      experimentId,
      variantId,
      manual: true,
    },
  });
}

/**
 * Reset experiment (clear promotion)
 */
export async function resetExperiment(experimentId: string): Promise<void> {
  const dbExp = await db.experiments.where('id').equals(experimentId).first();
  if (!dbExp?._id) return;
  
  await db.experiments.update(dbExp._id, {
    promotedId: undefined,
    updatedAt: new Date(),
  });
}
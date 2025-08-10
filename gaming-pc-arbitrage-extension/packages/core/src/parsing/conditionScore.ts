/**
 * Condition Score
 * Analyze listing text to determine item condition
 */

export interface ConditionAnalysis {
  score: number; // 0-100
  grade: 'new' | 'like-new' | 'excellent' | 'good' | 'fair' | 'poor';
  factors: {
    positive: string[];
    negative: string[];
  };
  confidence: number; // 0-1
}

// Keyword mappings
const CONDITION_KEYWORDS = {
  new: {
    keywords: ['new', 'unopened', 'sealed', 'nib', 'bnib', 'factory sealed', 'brand new'],
    score: 100,
  },
  likeNew: {
    keywords: ['like new', 'mint', 'pristine', 'barely used', 'open box', 'hardly used'],
    score: 90,
  },
  excellent: {
    keywords: ['excellent', 'great condition', 'very good', 'well maintained', 'adult owned'],
    score: 80,
  },
  good: {
    keywords: ['good condition', 'works great', 'fully functional', 'clean', 'tested'],
    score: 70,
  },
  fair: {
    keywords: ['fair', 'some wear', 'minor issues', 'cosmetic damage', 'scratches'],
    score: 50,
  },
  poor: {
    keywords: ['needs work', 'for parts', 'not working', 'damaged', 'broken', 'repair'],
    score: 20,
  },
};

const NEGATIVE_INDICATORS = [
  'smoker', 'pet', 'dusty', 'dirty', 'stained',
  'mining', 'mined', 'crypto', '24/7',
  'overclocked', 'oc\'d', 'modded',
  'no returns', 'as is', 'final sale',
];

const POSITIVE_INDICATORS = [
  'original box', 'receipts', 'warranty',
  'smoke-free', 'pet-free', 'clean environment',
  'barely used', 'light use', 'weekend gaming',
  'upgraded', 'maintained', 'cleaned regularly',
];

/**
 * Calculate condition score from text
 */
export function calculateConditionScore(text: string): ConditionAnalysis {
  const lowerText = text.toLowerCase();
  const factors = {
    positive: [] as string[],
    negative: [] as string[],
  };
  
  let baseScore = 60; // Start with neutral
  let matchedGrade: keyof typeof CONDITION_KEYWORDS | null = null;
  
  // Check for condition keywords
  for (const [grade, config] of Object.entries(CONDITION_KEYWORDS)) {
    for (const keyword of config.keywords) {
      if (lowerText.includes(keyword)) {
        baseScore = Math.max(baseScore, config.score);
        matchedGrade = grade as keyof typeof CONDITION_KEYWORDS;
        factors.positive.push(`States "${keyword}"`);
        break;
      }
    }
  }
  
  // Check negative indicators
  for (const indicator of NEGATIVE_INDICATORS) {
    if (lowerText.includes(indicator)) {
      baseScore -= 10;
      factors.negative.push(indicator);
    }
  }
  
  // Check positive indicators
  for (const indicator of POSITIVE_INDICATORS) {
    if (lowerText.includes(indicator)) {
      baseScore += 5;
      factors.positive.push(indicator);
    }
  }
  
  // Age-related adjustments
  const ageMatch = lowerText.match(/(\d+)\s*(year|month|week|day)s?\s*(old|ago)/);
  if (ageMatch) {
    const amount = parseInt(ageMatch[1]);
    const unit = ageMatch[2];
    
    if (unit === 'year' && amount > 2) {
      baseScore -= amount * 5;
      factors.negative.push(`${amount} years old`);
    } else if (unit === 'month' && amount < 6) {
      baseScore += 5;
      factors.positive.push(`Only ${amount} months old`);
    }
  }
  
  // Usage patterns
  if (lowerText.includes('daily driver') || lowerText.includes('main pc')) {
    baseScore -= 5;
    factors.negative.push('Daily use');
  }
  
  if (lowerText.includes('spare') || lowerText.includes('backup') || lowerText.includes('second pc')) {
    baseScore += 5;
    factors.positive.push('Light use (spare/backup)');
  }
  
  // Clamp score
  const finalScore = Math.max(0, Math.min(100, baseScore));
  
  // Determine grade
  let grade: ConditionAnalysis['grade'];
  if (finalScore >= 95) grade = 'new';
  else if (finalScore >= 85) grade = 'like-new';
  else if (finalScore >= 75) grade = 'excellent';
  else if (finalScore >= 65) grade = 'good';
  else if (finalScore >= 45) grade = 'fair';
  else grade = 'poor';
  
  // Calculate confidence based on number of indicators found
  const totalIndicators = factors.positive.length + factors.negative.length;
  const confidence = Math.min(1, 0.3 + (totalIndicators * 0.1));
  
  return {
    score: finalScore,
    grade,
    factors,
    confidence,
  };
}

/**
 * Get condition color for UI
 */
export function getConditionColor(grade: ConditionAnalysis['grade']): string {
  const colors = {
    'new': '#10b981',
    'like-new': '#34d399',
    'excellent': '#60a5fa',
    'good': '#3b82f6',
    'fair': '#f59e0b',
    'poor': '#ef4444',
  };
  
  return colors[grade] || '#6b7280';
}

/**
 * Get condition description
 */
export function getConditionDescription(grade: ConditionAnalysis['grade']): string {
  const descriptions = {
    'new': 'Brand new, unopened, or in original packaging',
    'like-new': 'Barely used, no visible wear',
    'excellent': 'Light use, very well maintained',
    'good': 'Normal use, fully functional',
    'fair': 'Shows wear, may have minor issues',
    'poor': 'Significant wear or needs repair',
  };
  
  return descriptions[grade] || 'Unknown condition';
}
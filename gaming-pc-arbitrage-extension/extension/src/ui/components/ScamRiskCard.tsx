/**
 * Scam Risk Card Component
 * Display scam risk assessment with reasons
 */

import React from 'react';
import { AlertTriangle, Shield, ShieldAlert, ShieldOff } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import type { ScamRiskResult } from '@/core/risk/scamRules';

interface ScamRiskCardProps {
  scamRisk: ScamRiskResult;
  className?: string;
}

export function ScamRiskCard({ scamRisk, className }: ScamRiskCardProps) {
  const getIcon = () => {
    if (scamRisk.recommendation === 'avoid') {
      return <ShieldOff className="h-5 w-5 text-red-500" />;
    } else if (scamRisk.recommendation === 'caution') {
      return <ShieldAlert className="h-5 w-5 text-yellow-500" />;
    } else {
      return <Shield className="h-5 w-5 text-green-500" />;
    }
  };

  const getScoreColor = () => {
    if (scamRisk.score >= 60) return 'text-red-500';
    if (scamRisk.score >= 30) return 'text-yellow-500';
    return 'text-green-500';
  };

  const getProgressColor = () => {
    if (scamRisk.score >= 60) return 'bg-red-500';
    if (scamRisk.score >= 30) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getLevelBadgeVariant = (level: string) => {
    switch (level) {
      case 'high':
        return 'destructive';
      case 'medium':
        return 'warning';
      default:
        return 'secondary';
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            {getIcon()}
            Scam Risk Assessment
          </span>
          <span className={`text-2xl font-bold ${getScoreColor()}`}>
            {scamRisk.score}
          </span>
        </CardTitle>
        <CardDescription>
          Recommendation: <strong className="uppercase">{scamRisk.recommendation}</strong>
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span>Risk Score</span>
            <span>{scamRisk.score}/100</span>
          </div>
          <Progress 
            value={scamRisk.score} 
            className="h-2"
            indicatorClassName={getProgressColor()}
          />
        </div>

        {scamRisk.reasons.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium text-sm">Risk Factors:</h4>
            {scamRisk.reasons.map((reason, idx) => (
              <Alert key={idx} className="py-2">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{reason.reason}</span>
                    <Badge variant={getLevelBadgeVariant(reason.level)}>
                      {reason.level}
                    </Badge>
                  </div>
                  {reason.mitigation && (
                    <div className="text-sm text-muted-foreground">
                      <strong>Mitigation:</strong> {reason.mitigation}
                    </div>
                  )}
                </AlertDescription>
              </Alert>
            ))}
          </div>
        )}

        {scamRisk.recommendation === 'avoid' && (
          <Alert variant="destructive">
            <ShieldOff className="h-4 w-4" />
            <AlertDescription>
              <strong>High Risk:</strong> We strongly recommend avoiding this listing.
              Multiple red flags indicate potential fraud.
            </AlertDescription>
          </Alert>
        )}

        {scamRisk.recommendation === 'caution' && (
          <Alert>
            <ShieldAlert className="h-4 w-4" />
            <AlertDescription>
              <strong>Proceed with Caution:</strong> Several risk factors detected.
              Follow the mitigation steps and trust your instincts.
            </AlertDescription>
          </Alert>
        )}

        {scamRisk.recommendation === 'safe' && scamRisk.score === 0 && (
          <Alert className="border-green-200 bg-green-50">
            <Shield className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              <strong>Low Risk:</strong> No significant scam indicators detected.
              Standard precautions still apply.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
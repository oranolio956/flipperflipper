using System;
using System.Runtime.CompilerServices;
using ProxyAssessmentTool.Core.Models;
using System.Collections.Generic; // Added missing import for List

namespace ProxyAssessmentTool.Core.Eligibility
{
    /// <summary>
    /// Thread-safe, immutable snapshot of data needed for eligibility evaluation
    /// </summary>
    public readonly record struct EligibilitySnapshot(
        int FraudScoreInt,
        bool IsSocks5,
        bool NoAuth,
        string CountryIso,
        bool IsMobile,
        UsageClass Usage,
        DateTime CapturedAt = default)
    {
        public EligibilitySnapshot() : this(0, false, false, "", false, UsageClass.Unknown, DateTime.UtcNow) { }
    }

    /// <summary>
    /// Pure, stateless, thread-safe eligibility evaluator
    /// </summary>
    public static class EligibilityEvaluator
    {
        // Constants for comparison
        private const int AcceptableFraudScore = 0;
        private const string RequiredCountryCode = "US";
        
        /// <summary>
        /// Evaluates eligibility based on strict criteria. Thread-safe and deterministic.
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        public static bool IsEligible(in EligibilitySnapshot snapshot)
        {
            return snapshot.FraudScoreInt == AcceptableFraudScore
                && snapshot.IsSocks5
                && snapshot.NoAuth
                && string.Equals(snapshot.CountryIso, RequiredCountryCode, StringComparison.OrdinalIgnoreCase)
                && snapshot.IsMobile
                && IsUsageAcceptable(snapshot.Usage);
        }

        /// <summary>
        /// Evaluates eligibility and provides detailed reasons for ineligibility
        /// </summary>
        public static EligibilityResult EvaluateWithReasons(in EligibilitySnapshot snapshot)
        {
            var reasons = new List<string>();

            if (snapshot.FraudScoreInt != AcceptableFraudScore)
                reasons.Add($"Fraud score is {snapshot.FraudScoreInt}, not {AcceptableFraudScore}");

            if (!snapshot.IsSocks5)
                reasons.Add("Protocol is not SOCKS5");

            if (!snapshot.NoAuth)
                reasons.Add("Authentication is required (not no-auth)");

            if (!string.Equals(snapshot.CountryIso, RequiredCountryCode, StringComparison.OrdinalIgnoreCase))
                reasons.Add($"Country is {snapshot.CountryIso ?? "unknown"}, not {RequiredCountryCode}");

            if (!snapshot.IsMobile)
                reasons.Add("Network is not mobile");

            if (!IsUsageAcceptable(snapshot.Usage))
                reasons.Add($"Usage class {snapshot.Usage} is not acceptable");

            return new EligibilityResult(
                IsEligible: reasons.Count == 0,
                Reasons: reasons.ToArray(),
                EvaluatedAt: DateTime.UtcNow,
                Snapshot: snapshot
            );
        }

        /// <summary>
        /// Determines if usage class is acceptable for eligibility
        /// </summary>
        [MethodImpl(MethodImplOptions.AggressiveInlining)]
        private static bool IsUsageAcceptable(UsageClass usage)
        {
            return usage == UsageClass.Unused || usage == UsageClass.LowUsage;
        }

        /// <summary>
        /// Creates a snapshot from a Finding object
        /// </summary>
        public static EligibilitySnapshot CreateSnapshot(Finding finding, FraudScore fraudScore)
        {
            return new EligibilitySnapshot(
                FraudScoreInt: fraudScore.Value,
                IsSocks5: finding.Protocol == ProxyProtocol.Socks5,
                NoAuth: finding.SelectedAuthMethod == AuthMethod.NoAuth,
                CountryIso: finding.CountryCode ?? string.Empty,
                IsMobile: finding.IsMobile,
                Usage: finding.UsageClass,
                CapturedAt: DateTime.UtcNow
            );
        }
    }

    /// <summary>
    /// Result of eligibility evaluation with detailed information
    /// </summary>
    public sealed record EligibilityResult(
        bool IsEligible,
        string[] Reasons,
        DateTime EvaluatedAt,
        EligibilitySnapshot Snapshot)
    {
        /// <summary>
        /// Gets a formatted string of all ineligibility reasons
        /// </summary>
        public string GetReasonsText() => string.Join("; ", Reasons);
    }

    /// <summary>
    /// Strongly typed fraud score with normalization
    /// </summary>
    public readonly record struct FraudScore : IComparable<FraudScore>, IEquatable<FraudScore>
    {
        private const decimal MinScore = 0m;
        private const decimal MaxScore = 10m;
        
        public int Value { get; }
        public decimal RawValue { get; }

        public FraudScore(decimal raw)
        {
            RawValue = Math.Clamp(raw, MinScore, MaxScore);
            Value = (int)Math.Round(RawValue, MidpointRounding.ToZero);
        }

        public static implicit operator int(FraudScore score) => score.Value;
        
        public static explicit operator FraudScore(decimal value) => new(value);
        
        public static explicit operator FraudScore(double value) => new((decimal)value);
        
        public static explicit operator FraudScore(int value) => new(value);

        public int CompareTo(FraudScore other) => Value.CompareTo(other.Value);

        public override string ToString() => $"{Value}/10 (raw: {RawValue:F2})";

        // Custom equality to use normalized integer value
        public bool Equals(FraudScore other) => Value == other.Value;
        
        public override int GetHashCode() => Value.GetHashCode();
        
        public static bool operator ==(FraudScore left, FraudScore right) => left.Equals(right);
        
        public static bool operator !=(FraudScore left, FraudScore right) => !left.Equals(right);
        
        public static bool operator <(FraudScore left, FraudScore right) => left.CompareTo(right) < 0;
        
        public static bool operator >(FraudScore left, FraudScore right) => left.CompareTo(right) > 0;
        
        public static bool operator <=(FraudScore left, FraudScore right) => left.CompareTo(right) <= 0;
        
        public static bool operator >=(FraudScore left, FraudScore right) => left.CompareTo(right) >= 0;

        /// <summary>
        /// Parses a fraud score from various string formats
        /// </summary>
        public static bool TryParse(string? input, out FraudScore score)
        {
            score = default;
            
            if (string.IsNullOrWhiteSpace(input))
                return false;

            // Handle "X/10" format
            if (input.Contains('/'))
            {
                var parts = input.Split('/');
                if (parts.Length == 2 && decimal.TryParse(parts[0], out var numerator))
                {
                    score = new FraudScore(numerator);
                    return true;
                }
            }

            // Handle plain decimal
            if (decimal.TryParse(input, out var value))
            {
                score = new FraudScore(value);
                return true;
            }

            return false;
        }
    }
}
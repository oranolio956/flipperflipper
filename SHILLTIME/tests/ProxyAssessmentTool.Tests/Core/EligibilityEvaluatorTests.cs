using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using ProxyAssessmentTool.Core.Eligibility;
using ProxyAssessmentTool.Core.Models;
using Xunit;

namespace ProxyAssessmentTool.Tests.Core
{
    public class EligibilityEvaluatorTests
    {
        [Fact]
        public void IsEligible_WithAllCriteriaMet_ReturnsTrue()
        {
            // Arrange
            var snapshot = new EligibilitySnapshot(
                FraudScoreInt: 0,
                IsSocks5: true,
                NoAuth: true,
                CountryIso: "US",
                IsMobile: true,
                Usage: UsageClass.Unused
            );

            // Act
            var result = EligibilityEvaluator.IsEligible(snapshot);

            // Assert
            Assert.True(result);
        }

        [Theory]
        [InlineData(1, false)] // Non-zero fraud score
        [InlineData(5, false)] // Higher fraud score
        [InlineData(10, false)] // Max fraud score
        public void IsEligible_WithNonZeroFraudScore_ReturnsFalse(int fraudScore, bool expected)
        {
            // Arrange
            var snapshot = new EligibilitySnapshot(
                FraudScoreInt: fraudScore,
                IsSocks5: true,
                NoAuth: true,
                CountryIso: "US",
                IsMobile: true,
                Usage: UsageClass.Unused
            );

            // Act
            var result = EligibilityEvaluator.IsEligible(snapshot);

            // Assert
            Assert.Equal(expected, result);
        }

        [Fact]
        public void IsEligible_WithNonSocks5Protocol_ReturnsFalse()
        {
            // Arrange
            var snapshot = new EligibilitySnapshot(
                FraudScoreInt: 0,
                IsSocks5: false,
                NoAuth: true,
                CountryIso: "US",
                IsMobile: true,
                Usage: UsageClass.Unused
            );

            // Act
            var result = EligibilityEvaluator.IsEligible(snapshot);

            // Assert
            Assert.False(result);
        }

        [Fact]
        public void IsEligible_WithAuthentication_ReturnsFalse()
        {
            // Arrange
            var snapshot = new EligibilitySnapshot(
                FraudScoreInt: 0,
                IsSocks5: true,
                NoAuth: false,
                CountryIso: "US",
                IsMobile: true,
                Usage: UsageClass.Unused
            );

            // Act
            var result = EligibilityEvaluator.IsEligible(snapshot);

            // Assert
            Assert.False(result);
        }

        [Theory]
        [InlineData("CA", false)] // Canada
        [InlineData("UK", false)] // United Kingdom
        [InlineData("US", true)]  // United States (valid)
        [InlineData("us", true)]  // Case insensitive
        [InlineData("", false)]   // Empty
        [InlineData(null, false)] // Null
        public void IsEligible_WithVariousCountryCodes_ReturnsExpected(string? countryCode, bool expected)
        {
            // Arrange
            var snapshot = new EligibilitySnapshot(
                FraudScoreInt: 0,
                IsSocks5: true,
                NoAuth: true,
                CountryIso: countryCode ?? "",
                IsMobile: true,
                Usage: UsageClass.Unused
            );

            // Act
            var result = EligibilityEvaluator.IsEligible(snapshot);

            // Assert
            Assert.Equal(expected, result);
        }

        [Fact]
        public void IsEligible_WithNonMobileNetwork_ReturnsFalse()
        {
            // Arrange
            var snapshot = new EligibilitySnapshot(
                FraudScoreInt: 0,
                IsSocks5: true,
                NoAuth: true,
                CountryIso: "US",
                IsMobile: false,
                Usage: UsageClass.Unused
            );

            // Act
            var result = EligibilityEvaluator.IsEligible(snapshot);

            // Assert
            Assert.False(result);
        }

        [Theory]
        [InlineData(UsageClass.Unused, true)]
        [InlineData(UsageClass.LowUsage, true)]
        [InlineData(UsageClass.ModerateUsage, false)]
        [InlineData(UsageClass.HighUsage, false)]
        [InlineData(UsageClass.Active, false)]
        [InlineData(UsageClass.Unknown, false)]
        public void IsEligible_WithVariousUsageClasses_ReturnsExpected(UsageClass usage, bool expected)
        {
            // Arrange
            var snapshot = new EligibilitySnapshot(
                FraudScoreInt: 0,
                IsSocks5: true,
                NoAuth: true,
                CountryIso: "US",
                IsMobile: true,
                Usage: usage
            );

            // Act
            var result = EligibilityEvaluator.IsEligible(snapshot);

            // Assert
            Assert.Equal(expected, result);
        }

        [Fact]
        public void EvaluateWithReasons_WithAllCriteriaMet_ReturnsEligibleWithNoReasons()
        {
            // Arrange
            var snapshot = new EligibilitySnapshot(
                FraudScoreInt: 0,
                IsSocks5: true,
                NoAuth: true,
                CountryIso: "US",
                IsMobile: true,
                Usage: UsageClass.Unused
            );

            // Act
            var result = EligibilityEvaluator.EvaluateWithReasons(snapshot);

            // Assert
            Assert.True(result.IsEligible);
            Assert.Empty(result.Reasons);
        }

        [Fact]
        public void EvaluateWithReasons_WithMultipleFailures_ReturnsAllReasons()
        {
            // Arrange
            var snapshot = new EligibilitySnapshot(
                FraudScoreInt: 5,
                IsSocks5: false,
                NoAuth: false,
                CountryIso: "CA",
                IsMobile: false,
                Usage: UsageClass.HighUsage
            );

            // Act
            var result = EligibilityEvaluator.EvaluateWithReasons(snapshot);

            // Assert
            Assert.False(result.IsEligible);
            Assert.Equal(6, result.Reasons.Length);
            Assert.Contains("Fraud score is 5, not 0", result.Reasons);
            Assert.Contains("Protocol is not SOCKS5", result.Reasons);
            Assert.Contains("Authentication is required (not no-auth)", result.Reasons);
            Assert.Contains("Country is CA, not US", result.Reasons);
            Assert.Contains("Network is not mobile", result.Reasons);
            Assert.Contains("Usage class HighUsage is not acceptable", result.Reasons);
        }

        [Fact]
        public async Task IsEligible_ConcurrentEvaluation_ReturnsDeterministicResults()
        {
            // Arrange
            var snapshot = new EligibilitySnapshot(
                FraudScoreInt: 0,
                IsSocks5: true,
                NoAuth: true,
                CountryIso: "US",
                IsMobile: true,
                Usage: UsageClass.LowUsage
            );

            const int iterations = 1_000_000;
            const int parallelism = 100;
            var results = new bool[iterations];

            // Act
            await Parallel.ForAsync(0, iterations, new ParallelOptions { MaxDegreeOfParallelism = parallelism }, 
                async (i, ct) =>
                {
                    results[i] = EligibilityEvaluator.IsEligible(snapshot);
                    await Task.Yield();
                });

            // Assert
            Assert.All(results, r => Assert.True(r));
        }

        [Fact]
        public void IsEligible_PerformanceTest_MeetsLatencyRequirements()
        {
            // Arrange
            var snapshot = new EligibilitySnapshot(
                FraudScoreInt: 0,
                IsSocks5: true,
                NoAuth: true,
                CountryIso: "US",
                IsMobile: true,
                Usage: UsageClass.Unused
            );

            const int warmupIterations = 1000;
            const int testIterations = 100_000;

            // Warmup
            for (int i = 0; i < warmupIterations; i++)
            {
                _ = EligibilityEvaluator.IsEligible(snapshot);
            }

            // Act
            var sw = Stopwatch.StartNew();
            for (int i = 0; i < testIterations; i++)
            {
                _ = EligibilityEvaluator.IsEligible(snapshot);
            }
            sw.Stop();

            // Assert
            var avgLatencyMicroseconds = sw.Elapsed.TotalMicroseconds / testIterations;
            Assert.True(avgLatencyMicroseconds < 1, $"Average latency {avgLatencyMicroseconds:F2}μs exceeds 1μs target");
        }

        [Fact]
        public void CreateSnapshot_FromFindingAndFraudScore_CreatesCorrectSnapshot()
        {
            // Arrange
            var finding = new Finding
            {
                Protocol = ProxyProtocol.Socks5,
                SelectedAuthMethod = AuthMethod.NoAuth,
                CountryCode = "US",
                IsMobile = true,
                UsageClass = UsageClass.LowUsage
            };
            var fraudScore = new FraudScore(0.4m); // Should normalize to 0

            // Act
            var snapshot = EligibilityEvaluator.CreateSnapshot(finding, fraudScore);

            // Assert
            Assert.Equal(0, snapshot.FraudScoreInt);
            Assert.True(snapshot.IsSocks5);
            Assert.True(snapshot.NoAuth);
            Assert.Equal("US", snapshot.CountryIso);
            Assert.True(snapshot.IsMobile);
            Assert.Equal(UsageClass.LowUsage, snapshot.Usage);
        }
    }

    public class FraudScoreTests
    {
        [Theory]
        [InlineData(0.0, 0)]
        [InlineData(0.4, 0)]
        [InlineData(0.5, 1)]
        [InlineData(0.9, 1)]
        [InlineData(1.0, 1)]
        [InlineData(5.4, 5)]
        [InlineData(5.5, 6)]
        [InlineData(9.9, 10)]
        [InlineData(10.0, 10)]
        [InlineData(15.0, 10)] // Clamped to max
        [InlineData(-5.0, 0)]  // Clamped to min
        public void FraudScore_Normalization_WorksCorrectly(double raw, int expected)
        {
            // Act
            var score = new FraudScore((decimal)raw);

            // Assert
            Assert.Equal(expected, score.Value);
        }

        [Fact]
        public void FraudScore_Equality_UsesNormalizedValue()
        {
            // Arrange
            var score1 = new FraudScore(0.4m); // Normalizes to 0
            var score2 = new FraudScore(0.0m); // Already 0
            var score3 = new FraudScore(0.5m); // Normalizes to 1

            // Act & Assert
            Assert.Equal(score1, score2);
            Assert.NotEqual(score1, score3);
            Assert.True(score1 == score2);
            Assert.False(score1 == score3);
        }

        [Theory]
        [InlineData("0", 0, true)]
        [InlineData("5", 5, true)]
        [InlineData("10", 10, true)]
        [InlineData("0/10", 0, true)]
        [InlineData("5/10", 5, true)]
        [InlineData("7.5/10", 8, true)]
        [InlineData("invalid", 0, false)]
        [InlineData("", 0, false)]
        [InlineData(null, 0, false)]
        public void TryParse_VariousFormats_ParsesCorrectly(string? input, int expectedValue, bool expectedSuccess)
        {
            // Act
            var success = FraudScore.TryParse(input, out var score);

            // Assert
            Assert.Equal(expectedSuccess, success);
            if (success)
            {
                Assert.Equal(expectedValue, score.Value);
            }
        }

        [Fact]
        public void FraudScore_Comparisons_WorkCorrectly()
        {
            // Arrange
            var score0 = new FraudScore(0);
            var score5 = new FraudScore(5);
            var score10 = new FraudScore(10);

            // Act & Assert
            Assert.True(score0 < score5);
            Assert.True(score5 < score10);
            Assert.True(score10 > score5);
            Assert.True(score5 > score0);
            Assert.True(score0 <= score5);
            Assert.True(score5 <= score5);
            Assert.True(score10 >= score5);
            Assert.True(score5 >= score5);
        }

        [Fact]
        public void FraudScore_ImplicitConversion_ToInt()
        {
            // Arrange
            var score = new FraudScore(7.8m);

            // Act
            int value = score;

            // Assert
            Assert.Equal(8, value);
        }
    }
}
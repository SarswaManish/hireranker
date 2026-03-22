from django.test import TestCase

from .scoring import calculate_overall_score, get_recommendation_bucket, normalize_score_dict, SCORE_WEIGHTS


class ScoringTests(TestCase):
    def test_score_weights_sum_to_one(self):
        total = sum(SCORE_WEIGHTS.values())
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_calculate_overall_score_perfect(self):
        breakdown = {
            'skills_match_score': 100,
            'experience_depth_score': 100,
            'impact_score': 100,
            'project_relevance_score': 100,
            'communication_resume_quality_score': 100,
            'domain_fit_score': 100,
            'risk_penalty_score': 0,
        }
        score = calculate_overall_score(breakdown)
        self.assertAlmostEqual(score, 100.0, places=1)

    def test_calculate_overall_score_zero(self):
        breakdown = {
            'skills_match_score': 0,
            'experience_depth_score': 0,
            'impact_score': 0,
            'project_relevance_score': 0,
            'communication_resume_quality_score': 0,
            'domain_fit_score': 0,
            'risk_penalty_score': 0,
        }
        score = calculate_overall_score(breakdown)
        self.assertEqual(score, 0.0)

    def test_calculate_with_risk_penalty(self):
        breakdown = {
            'skills_match_score': 100,
            'experience_depth_score': 100,
            'impact_score': 100,
            'project_relevance_score': 100,
            'communication_resume_quality_score': 100,
            'domain_fit_score': 100,
            'risk_penalty_score': 10,
        }
        score = calculate_overall_score(breakdown)
        self.assertAlmostEqual(score, 90.0, places=1)

    def test_get_recommendation_strong_yes(self):
        self.assertEqual(get_recommendation_bucket(85.0), 'strong_yes')

    def test_get_recommendation_yes(self):
        self.assertEqual(get_recommendation_bucket(70.0), 'yes')

    def test_get_recommendation_maybe(self):
        self.assertEqual(get_recommendation_bucket(50.0), 'maybe')

    def test_get_recommendation_no(self):
        self.assertEqual(get_recommendation_bucket(30.0), 'no')

    def test_normalize_score_dict_0_10_scale(self):
        raw = {
            'skills_match_score': 8.5,
            'experience_depth_score': 7.0,
            'impact_score': 6.0,
            'project_relevance_score': 9.0,
            'communication_resume_quality_score': 7.5,
            'domain_fit_score': 8.0,
            'risk_penalty_score': 2.0,
        }
        normalized = normalize_score_dict(raw)
        self.assertAlmostEqual(normalized['skills_match_score'], 85.0, places=1)
        self.assertAlmostEqual(normalized['risk_penalty_score'], 2.0, places=1)

    def test_normalize_score_dict_0_100_scale(self):
        raw = {
            'skills_match_score': 85,
            'experience_depth_score': 70,
            'impact_score': 60,
            'project_relevance_score': 90,
            'communication_resume_quality_score': 75,
            'domain_fit_score': 80,
            'risk_penalty_score': 5,
        }
        normalized = normalize_score_dict(raw)
        self.assertAlmostEqual(normalized['skills_match_score'], 85.0, places=1)

    def test_score_clamped_at_100(self):
        breakdown = {
            'skills_match_score': 150,  # Over 100
            'experience_depth_score': 100,
            'impact_score': 100,
            'project_relevance_score': 100,
            'communication_resume_quality_score': 100,
            'domain_fit_score': 100,
            'risk_penalty_score': 0,
        }
        score = calculate_overall_score(breakdown)
        self.assertLessEqual(score, 100.0)

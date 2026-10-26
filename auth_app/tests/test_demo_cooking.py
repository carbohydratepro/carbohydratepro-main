from django.test import SimpleTestCase
from django.urls import reverse


class DemoCookingTest(SimpleTestCase):
    def test_demo_is_public_and_uses_no_database(self) -> None:
        response = self.client.get(reverse('demo_cooking'))
        self.assertContains(response, 'チキンカレー')
        self.assertContains(response, 'demoSignupModal')
        self.assertEqual(response.context['page_obj'].paginator.count, 3)

    def test_search_sort_and_empty_results(self) -> None:
        response = self.client.get(reverse('demo_cooking'), {'search': '鶏肉'})
        self.assertEqual(response.context['page_obj'].paginator.count, 1)
        response = self.client.get(reverse('demo_cooking'), {'sort': 'count'})
        self.assertEqual(response.context['page_obj'][0].title, 'トマトパスタ')
        response = self.client.get(reverse('demo_cooking'), {'search': '存在しない料理'})
        self.assertContains(response, '条件に一致する料理がありません。')

    def test_invalid_parameters_are_safe(self) -> None:
        response = self.client.get(reverse('demo_cooking'), {'sort': 'invalid', 'page': 'invalid'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sort'], 'recent')

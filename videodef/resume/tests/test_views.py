from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.http import JsonResponse
import json
import io

from resume.models import Resume, TeacherReview, FuzzyComparisonSettings, UserCriteriaWeights
from resume.tests.utils import ResumeTestBase
from resume.views import (
    PublicResumeListView, 
    api_calculate_criteria_weights,
    api_calculate_alternatives_weights,
    api_check_consistency,
    export_search_results_excel,
    what_if_analysis,
    admin_fuzzy_settings,
    create_review,
    user_weights_settings
)

User = get_user_model()


class ResumeViewsTest(ResumeTestBase):
    def setUp(self):
        super().setUp()
        self.resume = Resume.objects.create(
            user=self.user,
            short_info="Резюме",
            detailed_info="Описание",
            status=Resume.DRAFT,
            education_level=5,
            experience_years=3,
            price_min=500,
            price_max=1000,
        )
        # Создаем активное резюме для публичных тестов
        self.active_resume = Resume.objects.create(
            user=self.user,
            short_info="Активное резюме",
            detailed_info="Активное описание",
            status=Resume.ACTIVE,
            education_level=7,
            experience_years=5,
            price_min=600,
            price_max=1200,
        )

    # ... существующие тесты ...

    def test_public_list_view_with_filters(self):
        """Тест публичного списка с фильтрами"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse("resume:public_resume_list")
        response = self.client.get(url, {
            'price_min': 500,
            'price_max': 1000,
            'min_experience': 3,
            'min_rating': 0,
            'max_distance': 20,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "resume/public_resume_list.html")
        self.assertIn('results', response.context)

    def test_public_list_view_with_weight_mode_custom(self):
        """Тест публичного списка с пользовательскими весами"""
        self.client.login(username='testuser', password='testpass123')
        
        # Создаем пользовательские веса
        UserCriteriaWeights.objects.create(
            user=self.user,
            weights={'price': 0.3, 'distance': 0.3, 'experience': 0.2, 'rating': 0.2, 'education': 0.0}
        )
        
        url = reverse("resume:public_resume_list")
        response = self.client.get(url, {
            'weight_mode': 'custom',
            'price_min': 0,
            'price_max': 10000,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)

    def test_public_list_view_with_violation_filter(self):
        """Тест публичного списка с фильтром по нарушениям"""
        self.client.login(username='testuser', password='testpass123')
        
        # Добавляем нарушение к резюме
        self.active_resume.violation_types.add(self.violation)
        
        url = reverse("resume:public_resume_list")
        response = self.client.get(url, {
            'violation_types': [str(self.violation.id)],
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.context)

    def test_public_detail_view_authenticated(self):
        """Тест публичного просмотра резюме авторизованным пользователем"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse("resume:public_resume_detail", kwargs={"pk": self.active_resume.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Активное описание")
        # Проверяем, что ссылка на чат показывается
        self.assertContains(response, "Написать в чат")

    def test_create_review_view(self):
        """Тест создания отзыва"""
        # Создаем второго пользователя - преподавателя
        teacher_user = User.objects.create_user(
            username='teacher',
            email='teacher@example.com',
            password='pass123',
            phone_number='+71234567891'
        )
        # Создаем профиль преподавателя
        from account.models import Profile, Role
        role = Role.objects.create(name="Преподаватель")
        Profile.objects.create(
            user=teacher_user,
            role=role,
            first_name="Преподаватель",
            last_name="Тестов",
        )
        
        # Создаем резюме для преподавателя
        teacher_resume = Resume.objects.create(
            user=teacher_user,
            short_info="Резюме преподавателя",
            detailed_info="Описание",
            status=Resume.ACTIVE,
            education_level=5,
            experience_years=3,
            price_min=500,
            price_max=1000,
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse("resume:create_review", kwargs={"teacher_id": teacher_user.unique_id})
        
        # GET запрос
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertTemplateUsed(response_get, "resume/create_review.html")
        
        # POST запрос
        response_post = self.client.post(url, {
            'rating': 5,
            'comment': 'Отличный преподаватель!'
        })
        self.assertEqual(response_post.status_code, 302)  # Редирект после создания
        
        # Проверяем, что отзыв создан
        self.assertTrue(
            TeacherReview.objects.filter(
                teacher=teacher_user,
                parent=self.user,
                rating=5,
                comment='Отличный преподаватель!'
            ).exists()
        )

    def test_ajax_create_document(self):
        """Тест AJAX создания документа"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse("resume:ajax_create_document")
        response = self.client.post(url, {
            'name': 'Тестовый документ',
            'info': 'Информация о документе',
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('document', data)

    def test_get_child_violations(self):
        """Тест получения нарушений ребенка"""
        self.client.login(username='testuser', password='testpass123')
        
        # Создаем ребенка
        from child.models import Child
        child = Child.objects.create(
            user=self.user,
            name="Тестовый ребенок",
            info="Информация",
            gender="Мужской",
            date_birth="2010-01-01",
        )
        child.violation_types.add(self.violation)
        
        url = reverse("resume:get_child_violations")
        response = self.client.get(url, {'child_id': child.id})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['violations'][0]['id'], self.violation.id)

    def test_user_weights_settings(self):
        """Тест настройки пользовательских весов"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse("resume:user_weights_settings")
        
        # GET запрос
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertTemplateUsed(response_get, "resume/user_weights_settings.html")
        
        # POST запрос
        response_post = self.client.post(url, {
            'use_custom': 'on',
            'calculated_weights': json.dumps({'price': 0.3, 'distance': 0.3}),
        })
        self.assertEqual(response_post.status_code, 302)  # Редирект


class ResumeAPITests(ResumeTestBase):
    """Тесты API эндпоинтов"""
    
    def setUp(self):
        super().setUp()
        # Делаем пользователя staff
        self.user.is_staff = True
        self.user.save()
        self.client.login(username='testuser', password='testpass123')

    def test_api_calculate_criteria_weights(self):
        """Тест API расчета весов критериев"""
        url = reverse("resume:api_calculate_criteria_weights")
        data = {
            'comparisons': {
                'criteria_comp_price_distance': '3',
                'criteria_comp_price_experience': '2',
                'criteria_comp_price_rating': '4',
                'criteria_comp_price_education': '5',
                'criteria_comp_distance_experience': '2',
                'criteria_comp_distance_rating': '3',
                'criteria_comp_distance_education': '4',
                'criteria_comp_experience_rating': '2',
                'criteria_comp_experience_education': '3',
                'criteria_comp_rating_education': '2',
            }
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn('weights', result)
        self.assertIn('cr', result)
        self.assertIn('is_consistent', result)

    def test_api_calculate_alternatives_weights(self):
        """Тест API расчета весов альтернатив"""
        # Создаем активное резюме
        Resume.objects.create(
            user=self.user,
            short_info="Активное резюме",
            detailed_info="Описание",
            status=Resume.ACTIVE,
            education_level=5,
            experience_years=3,
            price_min=500,
            price_max=1000,
        )
        
        url = reverse("resume:api_calculate_alternatives_weights")
        data = {
            'criterion': 'price',
            'comparisons': {}
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn('weights', result)
        self.assertIn('consistency', result)

    def test_api_check_consistency(self):
        """Тест API проверки согласованности"""
        url = reverse("resume:api_check_consistency")
        data = {
            'comparisons': {
                'criteria_comp_price_distance': '3',
                'criteria_comp_price_experience': '2',
                'criteria_comp_price_rating': '4',
                'criteria_comp_price_education': '5',
                'criteria_comp_distance_experience': '2',
                'criteria_comp_distance_rating': '3',
                'criteria_comp_distance_education': '4',
                'criteria_comp_experience_rating': '2',
                'criteria_comp_experience_education': '3',
                'criteria_comp_rating_education': '2',
            }
        }
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn('lambda_max', result)
        self.assertIn('cr', result)
        self.assertIn('is_consistent', result)


class ResumeFuzzyTests(ResumeTestBase):
    """Тесты fuzzy функциональности"""
    
    def setUp(self):
        super().setUp()
        # Создаем несколько активных резюме для fuzzy анализа
        for i in range(3):
            Resume.objects.create(
                user=self.user,
                short_info=f"Резюме {i}",
                detailed_info=f"Описание {i}",
                status=Resume.ACTIVE,
                education_level=5 + i,
                experience_years=3 + i,
                price_min=500 + i * 100,
                price_max=1000 + i * 100,
            )
        
        # Создаем настройки fuzzy
        FuzzyComparisonSettings.objects.create(
            use_expert_comparisons=True,
            criteria_comparisons=json.dumps([
                {'criterion1': 'price', 'criterion2': 'distance', 'value': 3},
                {'criterion1': 'price', 'criterion2': 'experience', 'value': 2},
            ])
        )

    def test_what_if_analysis(self):
        """Тест анализа "Что-Если" """
        self.client.login(username='testuser', password='testpass123')
        
        # Сначала нужно выполнить поиск
        search_url = reverse("resume:public_resume_list")
        self.client.get(search_url)
        
        url = reverse("resume:what_if_analysis")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "resume/what_if_analysis.html")
        
        # Тест AJAX запроса
        response_ajax = self.client.post(
            url,
            {
                'analysis_type': 'criterion',
                'criterion1': 'price',
                'criterion2': 'distance',
                'new_value': '5'
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response_ajax.status_code, 200)
        result = response_ajax.json()
        self.assertIn('solution', result)

    def test_fuzzy_demo(self):
        """Тест демонстрации fuzzy"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse("resume:fuzzy_demo")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "resume/fuzzy_demo.html")
        self.assertIn('model', response.context)
        self.assertIn('solution', response.context)
        self.assertIn('ranking', response.context)

    def test_export_search_results_excel(self):
        """Тест экспорта результатов в Excel"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse("resume:export_search_results_excel")
        response = self.client.get(url, {
            'price_min': 0,
            'price_max': 10000,
            'max_distance': 20,
            'weight_mode': 'expert',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('Content-Disposition', response)
        self.assertIn('teacher_search_', response['Content-Disposition'])


class ResumeAdminTests(ResumeTestBase):
    """Тесты админских функций"""
    
    def setUp(self):
        super().setUp()
        # Делаем пользователя staff
        self.user.is_staff = True
        self.user.save()
        self.client.login(username='testuser', password='testpass123')

    def test_admin_fuzzy_settings_get(self):
        """Тест GET запроса админских настроек fuzzy"""
        url = reverse("resume:admin_fuzzy_settings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "resume/admin_fuzzy_settings.html")
        self.assertIn('criteria', response.context)
        self.assertIn('teacher_choices', response.context)

    def test_admin_fuzzy_settings_post(self):
        """Тест POST запроса админских настроек fuzzy"""
        url = reverse("resume:admin_fuzzy_settings")
        data = {
            'criteria_comp_price_distance': '3',
            'criteria_comp_price_experience': '2',
            'use_expert_comparisons': 'on',
            'criteria_weights': json.dumps({'price': 0.3, 'distance': 0.3}),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Редирект после сохранения
        
        # Проверяем, что настройки сохранены
        settings = FuzzyComparisonSettings.objects.first()
        self.assertIsNotNone(settings)
        self.assertTrue(settings.use_expert_comparisons)

    def test_verification_report(self):
        """Тест отчета верификации"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse("resume:verification_report")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "resume/verification_report.html")
        self.assertIn('plots', response.context)
        self.assertIn('weights', response.context)
        self.assertIn('solution', response.context)
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from .models import SupportOrganization, ChatBotResponse, AnonymousStats
from .nlp_engine import clean_and_tokenize, calculate_match_score, match_intent, initialize_default_responses

class NLPEngineTests(TestCase):
    
    def setUp(self):
        # Populate responses before each test
        initialize_default_responses()
        
    def test_clean_and_tokenize(self):
        """Verifies punctuation removal, lowercasing, and stopword removal."""
        text = "Hello! My partner hit me and I need a safety plan."
        tokens = clean_and_tokenize(text)
        
        # Stopwords like 'my', 'and', 'i', 'need', 'a' should be removed
        # Punctuation like '!' should be removed
        self.assertIn("hello", tokens)
        self.assertIn("partner", tokens)
        self.assertIn("hit", tokens)
        self.assertIn("safety", tokens)
        self.assertIn("plan", tokens)
        self.assertNotIn("my", tokens)
        self.assertNotIn("and", tokens)
        self.assertNotIn("i", tokens)

    def test_calculate_match_score(self):
        """Checks match score metrics logic."""
        user_tokens = ["hit", "partner"]
        user_raw = "hit partner"
        db_keywords = "hit, punch, beat, slap"
        
        score = calculate_match_score(user_tokens, user_raw, db_keywords)
        self.assertGreater(score, 0)
        
        # Unrelated keywords should score 0
        unrelated_score = calculate_match_score(user_tokens, user_raw, "money, finance, job")
        self.assertEqual(unrelated_score, 0.0)

    def test_match_intent_greeting(self):
        """Verifies that greetings are classified correctly."""
        response, score = match_intent("hello there")
        self.assertEqual(response.intent, "greeting")
        
    def test_match_intent_emergency(self):
        """Verifies high-priority emergency word override overrides all other matches."""
        response, score = match_intent("he has a knife and threatens to kill me")
        self.assertEqual(response.intent, "emergency")
        
    def test_match_intent_fallback(self):
        """Verifies fallback classification on gibberish or obscure queries."""
        response, score = match_intent("xyzabcqwerty")
        self.assertEqual(response.intent, "fallback")


class ViewsAndAPITests(TestCase):
    
    def setUp(self):
        # Create test organizations
        SupportOrganization.objects.create(
            name="Test Shelter Lagos",
            category="shelter",
            state="Lagos",
            phone_number="08011112222",
            address="Lagos address",
            is_verified=True
        )
        SupportOrganization.objects.create(
            name="Test Clinic Abuja",
            category="medical",
            state="FCT",
            phone_number="08033334444",
            address="Abuja address",
            is_verified=True
        )
        # Create unverified org
        SupportOrganization.objects.create(
            name="Unverified Shelter",
            category="shelter",
            state="Lagos",
            phone_number="08055556666",
            address="Lagos address",
            is_verified=False
        )
        
        self.client = Client()

    def test_chat_home_renders(self):
        """Checks that the main index view loads successfully."""
        url = reverse('advisor:chat_home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GBV Advisory Portal")

    def test_chat_api_response(self):
        """Verifies POST communication to AJAX chat endpoint returns classified response."""
        url = reverse('advisor:chat_api')
        payload = {'message': 'My husband hit me yesterday.'}
        
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('response', data)
        self.assertEqual(data['intent'], 'physical_abuse')
        self.assertEqual(data['suggested_action'], 'safety_plan')
        
        # Verify anonymous statistics were logged
        self.assertEqual(AnonymousStats.objects.count(), 1)
        self.assertEqual(AnonymousStats.objects.first().detected_intent, 'physical_abuse')

    def test_directory_api_filtering(self):
        """Verifies state/category filters in NGO search directory."""
        url = reverse('advisor:directory_api')
        
        # Search Lagos shelter
        response = self.client.get(url, {'state': 'Lagos', 'category': 'shelter'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Ensure we have at least 1 Lagos shelter and our test shelter is in the list
        self.assertGreaterEqual(len(data['results']), 1)
        names = [org['name'] for org in data['results']]
        self.assertIn("Test Shelter Lagos", names)
        
        # Search unverified or non-existent
        response_fct = self.client.get(url, {'state': 'FCT', 'category': 'shelter'})
        self.assertEqual(response_fct.status_code, 200)
        self.assertEqual(len(response_fct.json()['results']), 0)

    def test_log_stat_api(self):
        """Verifies client-side click interactions can be logged anonymously."""
        url = reverse('advisor:log_stat_api')
        payload = {'action': 'downloaded_safety_plan'}
        
        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'logged')
        
        # Assert database log exists
        self.assertEqual(AnonymousStats.objects.filter(action_taken='downloaded_safety_plan').count(), 1)


class ModuleVerificationTests(TestCase):
    """
    Dedicated verification tests covering the 9 required modules:
    1. Homepage: Access application homepage -> Homepage displays correctly
    2. Chatbot Interface: Enter and submit a message -> Message is received by the system
    3. NLP Processing: Submit a question about GBV -> System identifies the relevant intent
    4. Knowledge Base: Request information about types of GBV -> Relevant information is retrieved
    5. Emotional Support: Submit a message expressing distress -> Appropriate supportive response is provided
    6. Safety Advisory: Request safety guidance -> Relevant safety information is provided
    7. Referral Module: Request contact information for support services -> Relevant referral information is displayed
    8. Administrative Module: Attempt to update knowledge-base information -> Authorized administrator can update records
    9. Database: Retrieve stored information -> Relevant records are retrieved successfully
    """
    def setUp(self):
        initialize_default_responses()
        self.client = Client()
        
        # Create test admin user
        self.admin_user = User.objects.create_superuser(
            username='test_admin',
            password='AdminPassword123!',
            email='admin@example.com'
        )
        # Create test regular user
        self.regular_user = User.objects.create_user(
            username='test_user',
            password='UserPassword123!',
            email='user@example.com'
        )
        # Create test support organizations
        SupportOrganization.objects.create(
            name="Lagos Emergency Shelter",
            category="shelter",
            state="Lagos",
            phone_number="08012345678",
            address="Ikeja, Lagos",
            description="Emergency shelter for women",
            is_verified=True
        )
        SupportOrganization.objects.create(
            name="Abuja Legal Aid Clinic",
            category="legal",
            state="FCT",
            phone_number="08098765432",
            address="Maitama, Abuja",
            description="Legal representation and advice",
            is_verified=True
        )

    # 1. Homepage: Access the application homepage -> Homepage displays correctly
    def test_01_homepage_displays_correctly(self):
        response = self.client.get(reverse('advisor:chat_home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GBV Advisory Portal")
        self.assertContains(response, "Quick Exit")
        self.assertContains(response, "Resource Hub")
        self.assertContains(response, "Find Support")
        self.assertContains(response, "Safety Planner")

    def test_separate_landing_and_chat_interface(self):
        """Verifies that the institutional landing page and chat workspace are distinct pages."""
        # 1. Landing Page
        home_res = self.client.get(reverse('advisor:chat_home'))
        self.assertEqual(home_res.status_code, 200)
        self.assertContains(home_res, "NASARAWA STATE UNIVERSITY, KEFFI")
        self.assertContains(home_res, "Knowledge for Development")
        self.assertContains(home_res, "Start Confidential Chat")
        self.assertContains(home_res, reverse('advisor:chat_page'))
        
        # 2. Dedicated Chat Interface
        chat_res = self.client.get(reverse('advisor:chat_page'))
        self.assertEqual(chat_res.status_code, 200)
        self.assertContains(chat_res, "NSUK GBV Advisory Assistant")
        self.assertContains(chat_res, "Back to NSUK Portal")
        self.assertContains(chat_res, "chat-history")
        self.assertContains(chat_res, "chat-input")

    # 2. Chatbot Interface: Enter and submit a message -> Message is received by the system
    def test_02_chatbot_interface_message_received(self):
        response = self.client.post(
            reverse('advisor:chat_api'),
            data=json.dumps({'message': 'Hello, I need help'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('response', data)
        self.assertIn('intent', data)
        # Verify message was logged in system stats
        self.assertTrue(AnonymousStats.objects.exists())

    # 3. NLP Processing: Submit a question about GBV -> System identifies the relevant intent
    def test_03_nlp_processing_identifies_gbv_intent(self):
        # Test submission via chat API
        response = self.client.post(
            reverse('advisor:chat_api'),
            data=json.dumps({'message': 'Submit a question about GBV: What is gender-based violence?'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['intent'], 'gbv_info')
        self.assertIn("Gender-Based Violence", data['response'])
        
        # Direct NLP engine test
        matched, score = match_intent("What is GBV?")
        self.assertEqual(matched.intent, 'gbv_info')
        self.assertGreater(score, 0)

    # 4. Knowledge Base: Request information about types of GBV -> Relevant information is retrieved
    def test_04_knowledge_base_retrieves_types_of_gbv(self):
        # Via Chatbot Interface
        response = self.client.post(
            reverse('advisor:chat_api'),
            data=json.dumps({'message': 'Request information about types of GBV'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['intent'], 'types_of_gbv')
        self.assertIn("Physical Abuse", data['response'])
        self.assertIn("Sexual Violence", data['response'])
        self.assertIn("Emotional & Psychological Abuse", data['response'])
        self.assertIn("Socio-Economic", data['response'])
        
        # Via Knowledge Base API
        kb_response = self.client.get(reverse('advisor:knowledge_base_api') + '?intent=types_of_gbv')
        self.assertEqual(kb_response.status_code, 200)
        kb_data = kb_response.json()
        self.assertEqual(kb_data['count'], 1)
        self.assertEqual(kb_data['knowledge_base'][0]['intent'], 'types_of_gbv')

    # 5. Emotional Support: Submit a message expressing distress -> Appropriate supportive response is provided
    def test_05_emotional_support_for_distress(self):
        response = self.client.post(
            reverse('advisor:chat_api'),
            data=json.dumps({'message': 'Submit a message expressing distress: I feel so overwhelmed, scared, and in deep distress'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['intent'], 'emotional_support')
        self.assertIn("distress", data['response'].lower())
        self.assertIn("valid", data['response'].lower())
        self.assertIn("breath", data['response'].lower())

    # 6. Safety Advisory: Request safety guidance -> Relevant safety information is provided
    def test_06_safety_advisory_guidance(self):
        response = self.client.post(
            reverse('advisor:chat_api'),
            data=json.dumps({'message': 'Request safety guidance: How can I stay safe?'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['intent'], 'safety_advisory')
        self.assertIn("Safety", data['title'])
        self.assertIn("exit", data['response'].lower())
        self.assertIn("code word", data['response'].lower())
        self.assertIn("digital safety", data['response'].lower())
        self.assertEqual(data['suggested_action'], 'safety_plan')

    # 7. Referral Module: Request contact information for support services -> Relevant referral information is displayed
    def test_07_referral_module_contact_information(self):
        # Via Chat API
        response = self.client.post(
            reverse('advisor:chat_api'),
            data=json.dumps({'message': 'Request contact information for support services'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['intent'], 'referral_module')
        self.assertIn("0800", data['response'])
        self.assertIn("Helpline", data['response'])
        
        # Via Directory / Referral API
        dir_response = self.client.get(reverse('advisor:directory_api'), {'state': 'Lagos'})
        self.assertEqual(dir_response.status_code, 200)
        results = dir_response.json()['results']
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]['phone_number'], "08012345678")
        
        # Via Referrals alias API
        ref_response = self.client.get(reverse('advisor:referrals_api'), {'category': 'legal'})
        self.assertEqual(ref_response.status_code, 200)
        self.assertGreaterEqual(len(ref_response.json()['results']), 1)

    # 8. Administrative Module: Attempt to update knowledge-base information -> Authorized administrator can update records
    def test_08_administrative_module_update_knowledge_base(self):
        # 1. Unauthorized attempt (anonymous or non-staff user) must be rejected
        unauth_response = self.client.post(
            reverse('advisor:admin_update_knowledge_api'),
            data=json.dumps({
                'intent': 'types_of_gbv',
                'response_text': 'Unauthorized update attempt'
            }),
            content_type='application/json'
        )
        self.assertEqual(unauth_response.status_code, 403)
        
        # Non-staff logged in user must also be rejected
        self.client.force_login(self.regular_user)
        user_response = self.client.post(
            reverse('advisor:admin_update_knowledge_api'),
            data=json.dumps({
                'intent': 'types_of_gbv',
                'response_text': 'Regular user update attempt'
            }),
            content_type='application/json'
        )
        self.assertEqual(user_response.status_code, 403)
        
        # 2. Authorized administrator can update records successfully
        self.client.force_login(self.admin_user)
        updated_text = "Updated GBV knowledge information by authorized administrator."
        admin_response = self.client.post(
            reverse('advisor:admin_update_knowledge_api'),
            data=json.dumps({
                'intent': 'types_of_gbv',
                'response_text': updated_text,
                'title': 'Updated Types of GBV'
            }),
            content_type='application/json'
        )
        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(admin_response.json()['status'], 'success')
        
        # Verify the database record was actually updated
        updated_record = ChatBotResponse.objects.get(intent='types_of_gbv')
        self.assertEqual(updated_record.response_text, updated_text)
        self.assertEqual(updated_record.title, 'Updated Types of GBV')
        
        # Verify the chatbot now serves the updated knowledge information
        chat_response = self.client.post(
            reverse('advisor:chat_api'),
            data=json.dumps({'message': 'Request information about types of GBV'}),
            content_type='application/json'
        )
        self.assertEqual(chat_response.status_code, 200)
        self.assertEqual(chat_response.json()['response'], updated_text)

    # 9. Database: Retrieve stored information -> Relevant records are retrieved successfully
    def test_09_database_retrieve_stored_information(self):
        # Retrieve SupportOrganization records
        orgs = SupportOrganization.objects.filter(is_verified=True, state="Lagos")
        self.assertTrue(orgs.exists())
        self.assertEqual(orgs.first().name, "Lagos Emergency Shelter")
        
        # Retrieve ChatBotResponse records
        responses = ChatBotResponse.objects.filter(intent__in=['gbv_info', 'types_of_gbv', 'safety_advisory'])
        self.assertEqual(responses.count(), 3)
        
        # Retrieve AnonymousStats records
        AnonymousStats.objects.create(detected_intent='gbv_info', action_taken='test_action')
        stat = AnonymousStats.objects.filter(detected_intent='gbv_info').first()
        self.assertIsNotNone(stat)
        self.assertEqual(stat.action_taken, 'test_action')

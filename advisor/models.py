from django.db import models

class SupportOrganization(models.Model):
    """
    Database of verified NGOs, medical clinics, legal aid groups, shelters, and emergency hotlines.
    """
    CATEGORY_CHOICES = [
        ('helpline', 'Emergency Helpline'),
        ('counseling', 'Counseling & Mental Health'),
        ('medical', 'Medical Support'),
        ('shelter', 'Safe House & Shelter'),
        ('legal', 'Legal Aid & Advocacy'),
    ]

    NIGERIAN_STATES = [
        ('Abia', 'Abia'), ('Adamawa', 'Adamawa'), ('Akwa Ibom', 'Akwa Ibom'), ('Anambra', 'Anambra'),
        ('Bauchi', 'Bauchi'), ('Bayelsa', 'Bayelsa'), ('Benue', 'Benue'), ('Borno', 'Borno'),
        ('Cross River', 'Cross River'), ('Delta', 'Delta'), ('Ebonyi', 'Ebonyi'), ('Edo', 'Edo'),
        ('Ekiti', 'Ekiti'), ('Enugu', 'Enugu'), ('Gombe', 'Gombe'), ('Imo', 'Imo'),
        ('Jigawa', 'Jigawa'), ('Kaduna', 'Kaduna'), ('Kano', 'Kano'), ('Katsina', 'Katsina'),
        ('Kebbi', 'Kebbi'), ('Kogi', 'Kogi'), ('Kwara', 'Kwara'), ('Lagos', 'Lagos'),
        ('Nasarawa', 'Nasarawa'), ('Niger', 'Niger'), ('Ogun', 'Ogun'), ('Ondo', 'Ondo'),
        ('Osun', 'Osun'), ('Oyo', 'Oyo'), ('Plateau', 'Plateau'), ('Rivers', 'Rivers'),
        ('Sokoto', 'Sokoto'), ('Taraba', 'Taraba'), ('Yobe', 'Yobe'), ('Zamfara', 'Zamfara'),
        ('FCT', 'Federal Capital Territory (Abuja)'),
    ]

    name = models.CharField(max_length=200, help_text="Name of the supporting organization")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, help_text="Primary support category")
    state = models.CharField(max_length=50, choices=NIGERIAN_STATES, help_text="State in Nigeria where they operate")
    phone_number = models.CharField(max_length=100, help_text="Primary helpline phone number")
    alt_phone_number = models.CharField(max_length=100, blank=True, null=True, help_text="Alternative phone number")
    email = models.EmailField(blank=True, null=True, help_text="Contact email address")
    address = models.TextField(help_text="Physical location details")
    website = models.URLField(blank=True, null=True, help_text="Official website URL")
    description = models.TextField(help_text="Services offered and other relevant details")
    is_verified = models.BooleanField(default=True, help_text="Verified status of the organization")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Support Organization"
        verbose_name_plural = "Support Organizations"

    def __str__(self):
        return f"{self.name} ({self.get_state_display()}) - {self.get_category_display()}"


class ChatBotResponse(models.Model):
    """
    Dynamically managed intents and replies for the custom NLP engine.
    Allows administrators to modify chatbot text and triggers in real-time.
    """
    ACTION_CHOICES = [
        ('none', 'No specific action'),
        ('safety_plan', 'Prompt Safety Planner creation'),
        ('directory_search', 'Prompt support directory search'),
    ]

    intent = models.CharField(max_length=50, unique=True, help_text="Intent slug (e.g. 'greeting', 'physical_abuse')")
    title = models.CharField(max_length=150, help_text="Descriptive title of the advice category")
    keywords = models.TextField(help_text="Comma-separated trigger keywords and phrases")
    response_text = models.TextField(help_text="The empathetic advisory message returned to the user")
    suggested_action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='none', help_text="Suggested next action step for the user")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['intent']
        verbose_name = "Chatbot Advisory Response"
        verbose_name_plural = "Chatbot Advisory Responses"

    def __str__(self):
        return f"{self.intent.upper()}: {self.title}"


class AnonymousStats(models.Model):
    """
    Aggregated usage metadata for administrators to track trends, query volume, 
    and resource demand. Note: No user IDs, IP addresses, or chat contents are logged here.
    """
    timestamp = models.DateTimeField(auto_now_add=True)
    state_filter_used = models.CharField(max_length=50, blank=True, null=True, help_text="State selected during directory search")
    category_filter_used = models.CharField(max_length=50, blank=True, null=True, help_text="Organization category selected")
    detected_intent = models.CharField(max_length=50, blank=True, null=True, help_text="The intent slug classified by NLP engine")
    action_taken = models.CharField(max_length=50, blank=True, null=True, help_text="Specific action clicked (e.g., 'downloaded_safety_plan')")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Anonymous Stat"
        verbose_name_plural = "Anonymous Stats"

    def __str__(self):
        return f"Stat on {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

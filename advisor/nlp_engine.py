import re
from .models import ChatBotResponse

# Simple English stop words to filter out noise from the queries
STOP_WORDS = {
    'the', 'is', 'are', 'was', 'were', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 
    'to', 'in', 'on', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from',
    'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further',
    'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any',
    'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
    'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can',
    'will', 'just', 'don', 'should', 'now', 'i', 'me', 'my', 'myself', 'we', 'our',
    'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 'he',
    'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself',
    'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom',
    'this', 'that', 'these', 'those', 'am', 'been', 'being', 'have', 'has', 'had',
    'having', 'do', 'does', 'did', 'doing', 'would', 'should', 'could', 'ought'
}

# High-priority emergency trigger words
EMERGENCY_WORDS = {
    'kill', 'die', 'suicide', 'stab', 'knife', 'gun', 'weapon', 'police', 'run away',
    'danger', 'unsafe', 'immediate', 'threaten to kill', 'abusing now', 'hurt me'
}

def clean_and_tokenize(text):
    """
    Cleans text by removing punctuation, lowercasing, and splitting into tokens.
    """
    if not text:
        return []
    # Remove punctuation and force lowercase
    cleaned = re.sub(r'[^\w\s]', '', text.lower())
    # Tokenize by whitespace
    tokens = cleaned.split()
    # Filter stopwords
    return [t for t in tokens if t not in STOP_WORDS]

def calculate_match_score(user_tokens, user_raw, db_keywords):
    """
    Calculates a match score between the user input and an intent's keywords.
    Handles both token similarity and multi-word phrase matching.
    """
    if not db_keywords:
        return 0.0
    
    # Split keywords from DB
    keyword_phrases = [kw.strip().lower() for kw in db_keywords.split(',') if kw.strip()]
    if not keyword_phrases:
        return 0.0

    direct_matches = 0
    keyword_tokens = set()
    user_lower = user_raw.lower()

    for phrase in keyword_phrases:
        # 1. Check for exact phrase matches in raw user input (e.g. "safety plan")
        if len(phrase.split()) > 1:
            if phrase in user_lower:
                direct_matches += 2.0  # Give higher weight to multi-word phrase matches
        else:
            # 2. Check for exact single word matches in user raw
            if phrase in user_tokens or phrase in user_lower.split():
                direct_matches += 1.0
        
        # Accumulate tokens for Jaccard similarity
        for word in clean_and_tokenize(phrase):
            keyword_tokens.add(word)

    # 3. Compute Jaccard Similarity (intersection over union)
    user_token_set = set(user_tokens)
    intersection = user_token_set.intersection(keyword_tokens)
    union = user_token_set.union(keyword_tokens)
    
    jaccard_score = len(intersection) / len(union) if union else 0.0

    # Combine metrics: direct phrase/word hits plus background overlap
    total_score = (direct_matches * 1.5) + jaccard_score
    return total_score

def match_intent(user_message):
    """
    Matches the user's message against the database intents.
    Returns the ChatBotResponse object and a confidence score.
    """
    # 1. Auto-initialize database responses if empty
    initialize_default_responses()

    user_raw = user_message.strip()
    user_tokens = clean_and_tokenize(user_raw)

    # 2. Check for emergency override words
    for word in user_tokens:
        if word in EMERGENCY_WORDS:
            emergency_response = ChatBotResponse.objects.filter(intent='emergency').first()
            if emergency_response:
                return emergency_response, 10.0

    # Also check multi-word emergencies in raw text
    for word in EMERGENCY_WORDS:
        if word in user_raw.lower():
            emergency_response = ChatBotResponse.objects.filter(intent='emergency').first()
            if emergency_response:
                return emergency_response, 10.0

    # 3. Fetch all database responses
    responses = ChatBotResponse.objects.all()
    best_response = None
    max_score = 0.0

    for resp in responses:
        # Don't check default fallbacks or exit codes here
        if resp.intent in ['fallback', 'greeting', 'goodbye']:
            continue
            
        score = calculate_match_score(user_tokens, user_raw, resp.keywords)
        if score > max_score:
            max_score = score
            best_response = resp

    # Check greetings and goodbyes specifically if general score is low
    greeting_resp = ChatBotResponse.objects.filter(intent='greeting').first()
    goodbye_resp = ChatBotResponse.objects.filter(intent='goodbye').first()

    if greeting_resp:
        greeting_score = calculate_match_score(user_tokens, user_raw, greeting_resp.keywords)
        if greeting_score > max_score and greeting_score > 0.8:
            return greeting_resp, greeting_score

    if goodbye_resp:
        goodbye_score = calculate_match_score(user_tokens, user_raw, goodbye_resp.keywords)
        if goodbye_score > max_score and goodbye_score > 0.8:
            return goodbye_resp, goodbye_score

    # 4. Fallback threshold
    threshold = 0.15
    if best_response and max_score >= threshold:
        return best_response, max_score
    elif greeting_resp and any(x in user_tokens for x in ['hi', 'hello', 'hey']):
        return greeting_resp, 1.0
    else:
        fallback_resp = ChatBotResponse.objects.filter(intent='fallback').first()
        return fallback_resp, 0.0

def initialize_default_responses():
    """
    Checks if default intents exist in the database, and ensures all essential intents are populated.
    This guarantees the system works out-of-the-box with professional advice.
    """
    defaults = [
        {
            'intent': 'greeting',
            'title': 'Welcome and Greeting',
            'keywords': 'hello, hi, hey, greetings, good morning, good afternoon, good evening, anyone there, startup',
            'response_text': 'Hello. I am Endy, your confidential advisory assistant. I am here to support you. You can talk to me about anything, or browse our directory of support services. How can I assist you today? (Please remember, you can click the Quick Exit button at any time if you feel unsafe.)',
            'suggested_action': 'none'
        },
        {
            'intent': 'goodbye',
            'title': 'Goodbye and Take Care',
            'keywords': 'bye, goodbye, exit, leave, thank you, thanks, talk later, logoff',
            'response_text': 'Thank you for reaching out. Please take care of yourself. I am always here if you need to talk again. Remember that your safety and well-being are paramount.',
            'suggested_action': 'none'
        },
        {
            'intent': 'fallback',
            'title': 'Clarification Needed',
            'keywords': '',
            'response_text': 'I want to make sure I understand you correctly. Could you please rephrase or tell me more about what you are experiencing? You can ask about different types of abuse (physical, sexual, emotional, financial), how to make a safety plan, or where to find help.',
            'suggested_action': 'none'
        },
        {
            'intent': 'emergency',
            'title': 'Urgent Safety Advice',
            'keywords': 'emergency, kill, die, suicide, danger, weapon, police, help me, immediate, run away, hurt, unsafe, rescue, fire',
            'response_text': 'If you are in immediate physical danger, please contact local emergency services or a trusted neighbor immediately. Here are critical safety steps:\n1. Move to a space with a lockable door or an exit path.\n2. Keep your mobile phone fully charged and close to you.\n3. Identify a trusted friend or family member who you can alert with a pre-arranged distress signal.\n4. You can find emergency helpline numbers for your state in our Support Directory on the right.',
            'suggested_action': 'directory_search'
        },
        {
            'intent': 'gbv_info',
            'title': 'Understanding Gender-Based Violence (GBV)',
            'keywords': 'gbv, what is gbv, gender based violence, gender-based violence, define gbv, about gbv, understand gbv, domestic violence, question about gbv, submit a question about gbv, tell me about gbv, explain gbv, violence against women, gender violence, what does gbv mean',
            'response_text': 'Gender-Based Violence (GBV) refers to harmful acts directed against an individual based on their gender. It is rooted in structural gender inequality, abuse of power, and harmful cultural norms.\n\nKey information about GBV:\n• Forms of GBV include physical assault, sexual violence, emotional/psychological manipulation, socio-economic abuse, and harmful traditional practices.\n• Anyone can be affected, but women, girls, and vulnerable groups face heightened risks.\n• Legal Protection: In Nigeria, the Violence Against Persons (Prohibition) Act (VAPP) and Child Rights Act legally criminalize all forms of violence and provide protective restraining orders.\n• You are never to blame for abuse. Help is available through verified shelters, medical centers, and legal aid.',
            'suggested_action': 'none'
        },
        {
            'intent': 'types_of_gbv',
            'title': 'Knowledge Base: Recognized Types of GBV',
            'keywords': 'types of gbv, request information about types of gbv, information about types of gbv, forms of gbv, kinds of gbv, types of abuse, forms of abuse, kinds of abuse, types of violence, forms of violence, what are the types of gbv, list the types of gbv, gbv types, gbv categories, kinds of violence',
            'response_text': 'Here is comprehensive knowledge-base information on the primary types of Gender-Based Violence (GBV):\n\n1. Physical Abuse: Inflicting bodily harm or trauma (hitting, slapping, kicking, choking, beating, burning, or weapon assault).\n2. Sexual Violence: Any non-consensual sexual act, sexual assault, rape, coerced intercourse, unwanted sexual touching, or sexual exploitation.\n3. Emotional & Psychological Abuse: Systematic non-physical torment (threats, verbal degradation, gaslighting, extreme jealousy, forced isolation, and constant humiliation).\n4. Socio-Economic / Financial Abuse: Depriving access to financial resources, forbidding employment or education, stealing earnings, and forcing total financial dependency.\n5. Harmful Traditional Practices: Culturally excused abuses, including Female Genital Mutilation (FGM), early/child marriage, and dehumanizing widowhood rites.\n6. Technology-Facilitated / Online GBV: Cyberstalking, non-consensual distribution of intimate images, digital harassment, and surveillance spyware.\n\nYou can view more in-depth guides in the Resource Hub tab in the right-hand panel.',
            'suggested_action': 'none'
        },
        {
            'intent': 'emotional_support',
            'title': 'Emotional Support & Distress Care',
            'keywords': 'distress, expressing distress, message expressing distress, submit a message expressing distress, emotional support, in distress, overwhelmed, crying, scared, terrified, broken, hopeless, panic, anxiety, sadness, hurting emotionally, despair, feeling down, grief, trauma, heartbroken, depressed, need emotional support, comfort, someone to talk to',
            'response_text': 'I hear how much distress and emotional pain you are experiencing right now, and I want to reassure you: your feelings are completely valid, and you do not have to walk through this alone.\n\n• Please take a slow, gentle breath with me: inhale slowly for 4 seconds, hold for 4 seconds, and exhale gently for 6 seconds.\n• Remind yourself: You are safe in this conversation, what happened is not your fault, and your worth and dignity remain intact.\n• Reaching out takes profound courage. You deserve compassion, care, and a safe harbor to process your feelings without judgment.\n\nIf you would like to speak with a trained, compassionate counselor, you can explore our verified counseling services in the Support Directory.',
            'suggested_action': 'directory_search'
        },
        {
            'intent': 'safety_advisory',
            'title': 'Safety Advisory & Protection Guidance',
            'keywords': 'safety guidance, request safety guidance, safety advisory, safety advice, safety tips, safety measures, stay safe, how to stay safe, safety protocol, danger precautions, protect myself, safety steps, guidance on safety, keeping safe, safety guidance request',
            'response_text': 'Here is vital safety guidance to help you protect yourself in dangerous or volatile situations:\n\n1. Physical Space Safety: Identify at least two clear exit routes from your residence. During heated moments, move away from confined spaces or rooms with sharp objects (such as kitchens and bathrooms).\n2. Emergency Distress Signal: Agree on a covert code word or text message with a trusted family member, neighbor, or friend who knows to contact emergency services immediately upon receiving it.\n3. Digital Safety: Use private/incognito browsing mode, clear browser history regularly, and remember that you can press ESC or click the Quick Exit button at any moment to instantly leave this portal.\n4. Critical Documents & Go-Bag: Keep a discreet emergency bag with copies of identification, birth certificates, deeds, daily medications, and spare emergency cash stored safely with a trusted friend or hidden securely.\n5. Personalized Safety Plan: Open the Safety Planner tab in the right panel to customize, track, and export your personal safety checklist.',
            'suggested_action': 'safety_plan'
        },
        {
            'intent': 'referral_module',
            'title': 'Support Services Directory & Referral Contacts',
            'keywords': 'request contact information for support services, contact information for support services, support services, referrals, referral, contacts, helpline numbers, emergency contacts, find help, ngos, directory contacts, organization phone number, where to get help, referral information, support service contacts',
            'response_text': 'Here is direct contact information for verified support service referrals:\n\n• National Human Rights Commission (NHRC) GBV Helpline: 08006472468 / 09033333222 (Toll-Free Nationwide)\n• Lagos State Domestic & Sexual Violence Agency (DSVA): 08003333333 / 08137960048 (24/7 Rapid Response)\n• Mirabel Centre (SARC - Free Medical Care & Forensics): 08172401444 / 08187870000\n• Cece Yara Foundation (Crisis Counseling & Child Advocacy): 08002223333\n• Project Alert Shelter (Emergency Housing & Legal Support): 08052004856 / 08180091072\n• FIDA Legal Advocacy (Federation of Women Lawyers): Toll-free desks across Nigeria\n\nYou can also click below to browse our Support Directory tab to find verified shelters, clinics, and legal aid across all Nigerian states.',
            'suggested_action': 'directory_search'
        },
        {
            'intent': 'physical_abuse',
            'title': 'Dealing with Physical Abuse',
            'keywords': 'hit, punch, beat, slap, kicked, physical, bruise, choke, push, violence, assault, battered',
            'response_text': 'Physical violence is never acceptable, and you do not deserve to be hurt. Your physical safety is the priority. We recommend creating an interactive Safety Plan (available in the side panel) to prepare for emergency situations. Additionally, please search our directory to connect with local shelters, counselors, and legal advocates who can help protect you.',
            'suggested_action': 'safety_plan'
        },
        {
            'intent': 'sexual_abuse',
            'title': 'Addressing Sexual Violence',
            'keywords': 'rape, assault, touch, forced, molest, sexual, consent, abuse, forced sex, harassed',
            'response_text': 'I am deeply sorry you had to go through this. Please know that it is not your fault. If this happened recently, we strongly advise seeking medical attention immediately at a hospital or specialized Sexual Assault Referral Centre (SARC) to ensure your health and preserve legal evidence. You can filter our Support Directory under "Medical Support" or "Counseling" to find local, non-judgmental assistance.',
            'suggested_action': 'directory_search'
        },
        {
            'intent': 'psychological_abuse',
            'title': 'Understanding Emotional & Psychological Abuse',
            'keywords': 'threat, yell, control, verbal, insult, name-calling, gaslight, scream, stalk, isolate, mental torture, manipulation',
            'response_text': 'Emotional and psychological abuse can be deeply damaging, even without physical contact. Actions like constant checking, isolation from friends/family, extreme jealousy, and threats are forms of coercive control. You deserve respect and autonomy. Speaking with a counselor can help you process this experience. Check our directory under "Counseling & Mental Health" for supportive services.',
            'suggested_action': 'directory_search'
        },
        {
            'intent': 'economic_abuse',
            'title': 'Identifying Economic & Financial Abuse',
            'keywords': 'money, finance, job, bank account, card, cash, work, allowance, steal, block access, financial control',
            'response_text': 'Economic abuse occurs when someone controls your ability to acquire, use, or maintain money, or limits your employment and education. This is done to make you financially dependent. We recommend secretly gathering financial documents if safe to do so, opening a separate bank account if possible, and seeking counseling or legal advice from specialized advocacy organizations listed in our directory.',
            'suggested_action': 'safety_plan'
        },
        {
            'intent': 'legal_aid',
            'title': 'Legal Protection and Rights',
            'keywords': 'lawyer, court, divorce, sue, police report, justice, rights, legal, law, magistrate, prosecution, vapp act',
            'response_text': 'You have legal rights, including the right to safety and protection. In Nigeria, the Violence Against Persons (Prohibition) Act (VAPP) provides legal protection against forms of violence. Legal aid groups and advocacy networks can help you file reports, obtain restraining orders, or seek justice. You can search our Support Directory under "Legal Aid & Advocacy" to contact organizations that offer free or low-cost legal advice.',
            'suggested_action': 'directory_search'
        },
        {
            'intent': 'counseling',
            'title': 'Mental Health & Counseling Support',
            'keywords': 'counselor, therapy, therapist, depressed, anxiety, crying, talk, mental health, advice, sad, lonely, support group',
            'response_text': 'Healing from abuse takes time, and you don\'t have to carry this burden alone. Professional counselors can provide confidential psychological support, therapy, and coping mechanisms. We encourage you to filter our Support Directory under "Counseling & Mental Health" to find organizations offering free or affordable counseling in your state.',
            'suggested_action': 'directory_search'
        },
        {
            'intent': 'safety_plan_info',
            'title': 'Creating a Safety Plan',
            'keywords': 'safety plan, escape, leaving, checklist, pack, document, pack bag, safe escape',
            'response_text': 'A safety plan is a personalized plan to help you stay safe while in an abusive relationship, or when planning to leave. It includes identifying safe spaces, packing essential documents (ID, birth certificates, deeds), saving money, and designating emergency contacts. Use the "Safety Planner" tab in the side panel to dynamically create and download your custom plan.',
            'suggested_action': 'safety_plan'
        }
    ]

    for item in defaults:
        ChatBotResponse.objects.get_or_create(
            intent=item['intent'],
            defaults={
                'title': item['title'],
                'keywords': item['keywords'],
                'response_text': item['response_text'],
                'suggested_action': item['suggested_action'],
            }
        )
